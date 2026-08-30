# 📘 Полная База Знаний и Руководство Проекта: Sminex Mobile Autotest Framework

Настоящий документ содержит все технические знания, архитектурные решения, конфигурации и инструкции для ведения и управления проектом прямо из **PyCharm**.

---

## 🛠️ 1. Общий обзор и Архитектура Проекта

Проект представляет собой автоматизированный фреймворк генерации, верификации и промоушна автотестов (UI Appium Android, API, E2E) с двухсторонней связью с **Jira**, **n8n**, **Qase TMS** и **GitHub Actions**.

### Схема взаимодействия компонентов:

```mermaid
flowchart TD
    A[Jira Issue (In Testing)] -->|Webhook| B[n8n Workflow]
    B -->|LLM Normalization & Qase Fetch| C[PyCharm Agent (agent_codegen.py:5000)]
    C -->|Auto-Start Appium:4723| D[Генерация тестов на ревью: tests/review/<JIRA_KEY>/]
    D -->|Pytest Check| E[QA Review в PyCharm / GitHub PR CI]
    E -->|promote_review_tests.py --verify --apply| F[Перенос в tests/ui, tests/api, tests/e2e]
    F -->|PATCH Custom Fields| G[Qase TMS (Status remains Manual, fields updated)]
    F -->|Git Commit & Push| H[GitHub Repository sminex-mobile]
```

---

## 📁 2. Структура Проекта и Назначение Файлов

```text
autotest_mobile/
├── agent_codegen.py              # HTTP-сервер агента (порт 5000) + автозапуск Appium (:4723)
├── promote_review_tests.py       # Скрипт верификации, переноса тестов и обновления Qase
├── sync_autotests.py             # Вспомогательный скрипт экспорта автотестов в Qase / n8n
├── docker-compose-n8n.yml        # Docker Compose файл n8n (со статическим N8N_ENCRYPTION_KEY)
├── n8n_workflow_template.json    # Выверенный готовый воркфлоу n8n (со встроенными Auth заголовками)
├── requirements.txt              # Зависимости Python (pytest, allure-pytest, Appium-Python-Client)
├── Dockerfile / docker-compose.yml # Конфигурации контейнеризации для тест-раннера
├── .github/workflows/
│   ├── verify-review-tests.yml   # CI на GitHub: проверка PR изменений в tests/review/
│   └── promote-approved-tests.yml # CD на GitHub: ручной промоушн тестов через workflow_dispatch
└── tests/
    ├── manifest.json             # Главный реестр перенесенных автотестов
    ├── review/
    │   ├── manifest.json         # Реестр тестов на ревью (status: pending_review | promoted)
    │   └── <JIRA_KEY>/           # Папки сгенерированных тестов на ревью (ui, back, e2e)
    ├── ui/                       # Постоянные UI автотесты
    ├── api/                      # Постоянные API автотесты
    └── e2e/                      # Постоянные E2E автотесты
```

---

## 🔑 3. Ключевые Переменные Окружения и Секреты

| Переменная | Значение по умолчанию | Назначение |
| :--- | :--- | :--- |
| `QASE_API_TOKEN` | `0a18fa9527fd31956a9353995bb62ccc94a23e547272b959484224cfda98bce6` | Токен авторизации Qase API |
| `QASE_PROJECT_CODE` | `ROMEO` | Код проекта в Qase TMS |
| `N8N_AGENT_TOKEN` | `n8n_agent_secret_token` | Bearer-токен защиты `/agent/trigger-codegen` |
| `N8N_ENCRYPTION_KEY` | `sminex-n8n-static-encryption-key-2026` | Ключ сохранения сессий n8n между перезапусками |

---

## 🎯 4. Специфика Интеграции с Qase TMS

В соответствии с правилами проекта:
1. **Отдельные автотесты в Qase НЕ создаются** (избегаем дублирования мануальных кейсов).
2. **Системное поле `Automation Status` НЕ меняется** (остаётся в значении `Manual`).
3. При промоушне тестов через `promote_review_tests.py` выполняется `PATCH`-запрос к `https://api.qase.io/v1/case/ROMEO/{qaseCaseId}` и заполняются **кастомные поля**:
   - `ID 1` (**Automation Coverage**) = `Automated`
   - `ID 2` (**Automation Type**) = `UI` / `API` / `E2E`
   - `ID 3` (**Automation Code Path**) = путь к тесту, например: `tests/ui/test_ui_...py`
   - `ID 4` (**Automation Test ID**) = `Allure ID` (числовой Qase Case ID)
   - `ID 5` (**Automation Note**) = отметка времени успешной проверки и переноса.

---

## 💻 5. Настройка PyCharm для Управления Проектом

Чтобы удобно управлять всем циклом прямо из PyCharm, настройте следующие **Run Configurations**:

### 1️⃣ Запуск Агента Генерации (Agent Codegen)
* **Type**: Python
* **Script path**: `agent_codegen.py`
* **Parameters**: `--port 5000`
* **Working directory**: `D:\One Drive\OneDrive\Рабочий стол\autotest_mobile`
*(При запуске агент сам проверит и поднимет Appium-сервер на порту 4723).*

### 2️⃣ Прогон Тестов на Ревью (pytest Review)
* **Type**: pytest
* **Target**: `Custom` -> `tests/review/`
* **Additional Arguments**: `-v -m review`

### 3️⃣ Локальный Промоушн Тестов (Promote Review Tests)
* **Type**: Python
* **Script path**: `promote_review_tests.py`
* **Parameters**: `--verify --apply --jira-key KAN-4` *(или без `--jira-key` для всех)*

### 4️⃣ Прогон Всех Постоянных Тестов (pytest Main)
* **Type**: pytest
* **Target**: `Custom` -> `tests/`

---

## 🔄 6. Полный жизненный цикл задачи (Cheat-Sheet)

1. **Jira**: Задача переходит в статус *In Testing*.
2. **n8n**: Отправляет данные задачи в локальный агент `http://host.docker.internal:5000/agent/trigger-codegen`.
3. **Agent**: Создает автотест в `tests/review/<JIRA_KEY>/` с маркерами `@pytest.mark.review` и `@pytest.mark.qase_case("<qaseCaseId>")`.
4. **PyCharm**: Вы запускаете конфигурацию **"pytest Review"** для проверки.
5. **Git**: Делаете `git push origin main`.
6. **GitHub Actions**:
   - Автоматически проверяет PR (`Verify Review Tests CI`).
   - По нажатию кнопки **Run workflow** в `Promote Approved Tests` автоматически переносит тесты в `tests/ui`, снимает маркер `@pytest.mark.review`, обновляет поля в Qase TMS и делает коммит в репозиторий.
