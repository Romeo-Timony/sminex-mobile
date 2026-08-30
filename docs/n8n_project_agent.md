# n8n → проект PyCharm

Локальный сервис получает задачу от n8n, отправляет её в OpenAI Responses API и возвращает набор изменений. По умолчанию он работает в режиме предварительного просмотра: файлы не меняются, пока n8n не отправит `"apply": true`.

## Запуск в Windows

В PowerShell задайте значения только для текущего окна:

```powershell
$env:OPENAI_API_KEY = "ваш API-ключ OpenAI"
$env:N8N_AGENT_TOKEN = "длинный-случайный-секрет"
& ".\run\venv\start_n8n_agent.bat"
```

Проверьте запуск: `http://localhost:5000/health`.

## Узел n8n

Используйте узел **HTTP Request**:

- Method: `POST`
- URL при n8n в Docker на том же ПК: `http://host.docker.internal:5000/agent/trigger-codegen`
- Header: `Authorization: Bearer <значение N8N_AGENT_TOKEN>`
- Body (JSON):

```json
{
  "task": "Сгенерируй автотесты по ручным тест-кейсам",
  "platform": "android",
  "jiraKey": "KAN-1",
  "testCases": [
    {
      "id": "AUTH-001",
      "title": "Успешная авторизация",
      "steps": [
        {"action": "Ввести корректные учётные данные", "expected": "Данные введены"},
        {"action": "Нажать Войти", "expected": "Открыт главный экран"}
      ]
    }
  ],
  "apply": false,
  "replaceReview": true
}
```

Сначала используйте `apply: false` и проверьте поле `changes`. Только затем включайте `apply: true`.

При `apply: true` сервис создаёт тесты только в `tests/review/<jiraKey>/` и добавляет их в `tests/review/manifest.json` со статусом `pending_review`. Он не изменяет боевые каталоги `tests/ui`, `tests/api` и `tests/e2e`.

При повторной генерации для одного `jiraKey` параметр `replaceReview` по умолчанию равен `true`: старый набор review-тестов этой задачи заменяется новым, чтобы устаревшие варианты не накапливались.

Для Android-кейсов типа `UI` или `E2E` сервис автоматически проверяет Appium и запускает его на `APPIUM_SERVER` (по умолчанию `http://127.0.0.1:4723`), если сервер не запущен. В ответе n8n поле `appium_ready` будет равно `true`. Для запуска требуется доступное Android-устройство или эмулятор; Appium Server сам устройство не создаёт.

Каждый сгенерированный тест помечен `@pytest.mark.review`. Перед переносом его в боевой каталог проверьте сбор тестов:

```powershell
pytest tests/review/KAN-1/ --collect-only
```

После ручной замены заглушек на вызовы Page Object или API-клиентов удалите маркер `review` и перенесите проверенный файл в соответствующий боевой каталог.

Если n8n находится на другом сервере, локальный порт 5000 нужно опубликовать через защищённый туннель или VPN. Не добавляйте API-ключ в workflow n8n: он хранится только в переменной окружения локального сервиса.
