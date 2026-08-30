# 📘 Единая База Знаний и Технический Регламент Проекта: Sminex Mobile Autotest Framework

---

## 📌 1. Назначение и Архитектурный Обзор

Фреймворк **Sminex Mobile Autotest Framework** предназначен для автоматической трансформации требований из **Jira** в проверенные автотесты (Android UI на **Appium**, **API** и **E2E**) с двусторонней связью с **Qase TMS** и CI/CD в **GitHub Actions**.

### 🔄 Сквозная Схема Движения Данных (End-to-End Pipeline)

```mermaid
flowchart TD
    subgraph 1. Jira & n8n Orchestration
        A[Jira Issue: Status -> 'In Testing'] -->|POST Webhook| B[n8n: Jira Webhook]
        B --> C[n8n: LLM Normalize TS]
        C --> D[n8n: LLM Generate Checklist]
        D -->|Comment| E[Jira Issue Comment]
        C --> F[n8n: LLM Generate TCs JSON]
        F --> G[n8n: Fetch Qase Manual TCs]
        G --> H[n8n: LLM Deduplicate & Format]
    end

    subgraph 2. Local Code Generation & Appium
        H -->|POST /agent/trigger-codegen| I[PyCharm Agent: agent_codegen.py:5000]
        I -->|Auto-Start| J[Appium Server: 4723]
        I --> K[Генерация файлов: tests/review/JIRA-KEY/]
        K --> L[Запись в tests/review/manifest.json: pending_review]
    end

    subgraph 3. QA Review & Promotion
        K --> M[QA Review в PyCharm: pytest tests/review/ -v]
        M --> N[promote_review_tests.py --verify --apply]
        N --> O[Перенос в tests/ui, tests/api, tests/e2e]
        N -->|PATCH Custom Fields| P[Qase TMS API: Case stays Manual, fields updated]
    end

    subgraph 4. CI/CD & GitHub Actions
        O --> Q[Git Push: sminex-mobile/main]
        Q --> R[GitHub Actions: verify-review-tests.yml on PR]
        Q --> S[GitHub Actions: promote-approved-tests.yml via workflow_dispatch]
    end
```

---

## ⚡ 2. Детализация n8n Workflow и Все Промпты LLM

Сценарий в n8n состоит из 8 последовательных узлов (Nodes), работающих с моделью **`gpt-4o`**.

### 🔹 Узел 1: `Jira Webhook (In Testing)`
* **Тип**: `n8n-nodes-base.webhook` (v1)
* **Метод**: `POST`
* **Path**: `jira-testing-trigger`
* **Назначение**: Принимает событие из Jira при переходе задачи в статус *In Testing*.
* **Входные данные**: JSON из Jira с полем `body.issue.fields.description` и `body.issue.key`.

---

### 🔹 Узел 2: `LLM: Normalize TS`
* **Тип**: `n8n-nodes-base.openAi` (v1)
* **Модель**: `gpt-4o`
* **Промпт (Точный текст)**:
```text
/Normalize the following Technical Specification from Jira:
{{ $json["body"]["issue"]["fields"]["description"] }}
```
* **Назначение**: Очищает сырой текст задачи Jira от разметки, опечаток и приводит к четким техническим требованиям.

---

### 🔹 Узел 3: `LLM: Generate Checklist`
* **Тип**: `n8n-nodes-base.openAi` (v1)
* **Модель**: `gpt-4o`
* **Промпт (Точный текст)**:
```text
/Generate a QA checklist (positive, negative, integration, UI) for this normalized TS:
{{ $json["text"] }}
```
* **Назначение**: Формирует структурированный чеклист проверки (позитивные, негативные, UI и интеграционные сценарии).

---

### 🔹 Узел 4: `Add Checklist to Jira`
* **Тип**: `n8n-nodes-base.httpRequest` (v4)
* **Метод**: `POST`
* **URL**: `https://romeo-timony.atlassian.net/rest/api/2/issue/{{ $('Jira Webhook (In Testing)').item.json["body"]["issue"]["key"] }}/comment`
* **Заголовки**: `Content-Type: application/json`
* **Назначение**: Публикует сгенерированный чеклист в виде комментария прямо в задаче Jira.

---

### 🔹 Узел 5: `LLM: Generate TCs (JSON)`
* **Тип**: `n8n-nodes-base.openAi` (v1)
* **Модель**: `gpt-4o`
* **Промпт (Точный текст)**:
```text
/Generate structured manual test cases in JSON format (UI, API, E2E) with Title, Type, Preconditions, Steps, and Expected Results based on this normalized TS:
{{ $('LLM: Normalize TS').item.json["text"] }}
```
* **Назначение**: Генерирует ручные тест-кейсы в строго структурированном виде.

---

### 🔹 Узел 6: `Fetch Existing Qase Manual TCs`
* **Тип**: `n8n-nodes-base.httpRequest` (v4)
* **Метод**: `GET`
* **URL**: `https://api.qase.io/v1/case/ROMEO?limit=100`
* **Заголовки**:
  - `Token: 0a18fa9527fd31956a9353995bb62ccc94a23e547272b959484224cfda98bce6`
  - `Accept: application/json`
* **Назначение**: Получает список текущих мануальных кейсов из Qase TMS для исключения дублирования.

---

### 🔹 Узел 7: `LLM: Review & Deduplicate`
* **Тип**: `n8n-nodes-base.openAi` (v1)
* **Модель**: `gpt-4o`
* **Промпт (Точный текст)**:
```text
/Compare the new test cases:
{{ $('LLM: Generate TCs (JSON)').item.json["text"] }}

with existing Allure / Qase test cases:
{{ $json["result"]["entities"] }}

Identify and remove duplicates, validate relevance to TS. Return filtered JSON test cases.
```
* **Назначение**: Сравнивает новые кейсы с существующей базой Qase, убирает дубликаты и возвращает финальный JSON-массив.

---

### 🔹 Узел 8: `Trigger PyCharm Agent`
* **Тип**: `n8n-nodes-base.httpRequest` (v4)
* **Метод**: `POST`
* **URL**: `http://host.docker.internal:5000/agent/trigger-codegen`
* **Заголовки**:
  - `Authorization: Bearer n8n_agent_secret_token`
  - `Content-Type: application/json; charset=utf-8`
* **Тело запроса (JSON)**:
```json
{
  "task": "Сгенерируй Android-автотесты по ручным кейсам",
  "platform": "android",
  "jiraKey": "{{ $('Jira Webhook (In Testing)').item.json[\"body\"][\"issue\"][\"key\"] }}",
  "apply": true,
  "testCases": {{ $json["text"] }}
}
```

---

## 🤖 3. Работа PyCharm Агента (`agent_codegen.py`)

Сервер агента работает на порту `5000` и выполняет следующие задачи:

1. **Автозапуск Appium**:
   - При старте проверяет порт `4723`. Если порт закрыт, подготавливает и запускает `appium.cmd` (на Windows) или `appium` (на Unix) в фоновом режиме.
2. **Авторизация**:
   - Проверяет заголовок `Authorization: Bearer n8n_agent_secret_token`. При несовпадении возвращает `401 Unauthorized`.
3. **Кодогенерация**:
   - Создаёт структуру папок: `tests/review/<JIRA_KEY>/ui/`, `tests/review/<JIRA_KEY>/back/`, `tests/review/<JIRA_KEY>/e2e/`.
   - Генерирует файлы Python-тестов с декораторами:
     - `@pytest.mark.review`
     - `@pytest.mark.jira("<JIRA_KEY>")`
     - `@pytest.mark.qase_case("<qaseCaseId>")`
     - `@allure.epic("<Type> Автотесты (На ревью)")`
     - `@allure.id("<qaseCaseId>")`
4. **Обновление реестра ревью**:
   - Записывает метаданные сгенерированных тестов со статусом `"status": "pending_review"` в файл `tests/review/manifest.json`.

---

## 🚚 4. Верификация и Промоушн (`promote_review_tests.py`)

Скрипт `promote_review_tests.py` отвечает за проверку и перенос одобренных тестов в постоянное хранилище.

### Запуск команды:
```powershell
python promote_review_tests.py --verify --apply --jira-key KAN-4
```

### Алгоритм работы:
1. **Верификация (`--verify`)**:
   - Запускает `pytest` для указанных тестов из `tests/review/<JIRA_KEY>/`.
   - Если любой из тестов падает, промоушн прерывается.
2. **Перенос кода (`--apply`)**:
   - Перемещает файлы из `tests/review/<JIRA_KEY>/[ui|back|e2e]/` в постоянные директории `tests/ui/`, `tests/api/`, `tests/e2e/`.
   - Удаляет строку маркера `@pytest.mark.review`.
   - Удаляет пометку `(На ревью)` из декоратора Allure epic.
   - Удаляет пустые папки задачи в `tests/review/`.
3. **Обновление Манифестов**:
   - В `tests/review/manifest.json` у перенесенных тестов устанавливается `"status": "promoted"`.
   - В главный файл `tests/manifest.json` добавляются записи о новых постоянных автотестах.
4. **Интеграция с Qase TMS (PATCH)**:
   - Отправляет `PATCH`-запрос на `https://api.qase.io/v1/case/ROMEO/{clean_id}`:
     ```json
     {
       "custom_field": {
         "1": "Automated",
         "2": "UI",
         "3": "tests/ui/test_ui_knopka_moi_pokupki_otobrazhaetsya_na_glavnom_ekran.py",
         "4": "1162",
         "5": "Автотест успешно проверен и перенесен. Дата: 2026-08-30 20:00:00"
       }
     }
     ```
   - **Важно**: Системное поле `Automation Status` в Qase остаётся **`Manual`**.

---

## 🐳 5. Контейнеризация и Docker (`docker-compose-n8n.yml`)

Для локального запуска n8n используется файл [`docker-compose-n8n.yml`](file:///d:/One%20Drive/OneDrive/%D0%A0%D0%B0%D0%B1%D0%BE%D1%87%D0%B8%D0%B9%20%D1%81%D1%82%D0%BE%D0%BB/autotest_project/docker-compose-n8n.yml):

```yaml
version: '3.8'

services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: n8n-dev-instance
    ports:
      - "5678:5678"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - GENERIC_TIMEZONE=Europe/Moscow
      - N8N_ENCRYPTION_KEY=sminex-n8n-static-encryption-key-2026
      - QASE_API_TOKEN=0a18fa9527fd31956a9353995bb62ccc94a23e547272b959484224cfda98bce6
      - QASE_PROJECT_CODE=ROMEO
      - N8N_AGENT_TOKEN=n8n_agent_secret_token
      - JIRA_URL=https://romeo-timony.atlassian.net
    volumes:
      - n8n_data:/home/node/.local/share/n8n
    restart: unless-stopped
    depends_on:
      - searxng

  searxng:
    image: searxng/searxng:latest
    container_name: searxng-dev
    ports:
      - "8081:8080"
    environment:
      - SEARXNG_SECRET=searxng-secret-key-456
    volumes:
      - ./searxng:/etc/searxng
    restart: unless-stopped

volumes:
  n8n_data:
```

### Ключевые настройки Docker:
1. **`N8N_ENCRYPTION_KEY`**: Статический ключ шифрования. Гарантирует, что учетные записи, сессии и сохраненные креды n8n сохраняются навсегда и не сбрасываются при перезапусках.
2. **`extra_hosts`**: Пробрасывает `host.docker.internal` внутрь Docker, что позволяет n8n вызывать PyCharm Agent на порту `5000` хост-системы.

---

## 🐙 6. CI/CD и GitHub Actions (`.github/workflows/`)

Репозиторий проекта на GitHub: **`https://github.com/Romeo-Timony/sminex-mobile`**

### 1. `verify-review-tests.yml` (Автоматическая проверка в PR)
* **Триггер**: `pull_request` в ветки `main`/`master` при изменениях в `tests/review/**`.
* **Действия**: Разворачивает Node.js 22, запускает Appium на порту `4723` и выполняет `pytest tests/review/ -v -m review`.

### 2. `promote-approved-tests.yml` (Ручной промоушн)
* **Триггер**: `workflow_dispatch` (Ручной запуск во вкладке Actions).
* **Права доступа**: `permissions: contents: write` (Разрешает GitHub Actions коммитить и пушить результаты обратно в ветку `main`).
* **Параметры**:
  - `jira_key` (Необязательный): Фильтр задачи (например, `KAN-4`).
  - `verify` (Boolean, по умолчанию `true`): Флаг предварительного запуска pytest.
* **Действия**: Выполняет `promote_review_tests.py --apply`, делает PATCH в Qase TMS, коммитит перенесенные тесты под именем `github-actions[bot]` и выполняет `git push origin HEAD:main`.

---

## 💻 7. Инструкция для Разработчиков и QA в PyCharm

Для полноценной работы из PyCharm добавьте конфигурации запуска (**Run ➔ Edit Configurations**):

| Конфигурация | Тип | Исполняемый файл / Мишень | Параметры / Аргументы | Назначение |
| :--- | :--- | :--- | :--- | :--- |
| **Run Agent** | Python | `agent_codegen.py` | `--port 5000` | Запуск фонового агента генерации кода + Appium |
| **pytest Review** | pytest | `tests/review/` | `-v -m review` | Запуск и проверка тестов, находящихся на ревью |
| **Promote Tests**| Python | `promote_review_tests.py` | `--verify --apply --jira-key KAN-4` | Верификация и перенос тестов в основные папки |
| **pytest All** | pytest | `tests/` | `-v` | Прогон полного набора постоянных автотестов |

---

## 📝 8. Чек-Лист выполнения задачи (Командный Регламент)

1. Разработчик/QA переводит задачу в **Jira** в статус *In Testing*.
2. **n8n** генерирует чеклист в коммент Jira и отправляет JSON кейсы в **PyCharm Agent**.
3. **PyCharm Agent** создает тесты на ревью в `tests/review/<JIRA_KEY>/`.
4. QA запускает конфигурацию **"pytest Review"** в PyCharm.
5. При успешном прогоне QA отправляет коммит в репозиторий (`git push origin main`).
6. Во вкладке **GitHub Actions** ➔ **Promote Approved Tests** нажимается кнопка **Run workflow**.
7. Тесты перемещаются в `tests/ui/` (или `api`/`e2e`), а в **Qase TMS** автоматически проставляются отметки покрытых автотестов!
