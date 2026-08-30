# Sminex Android autotests

Automated checks for the Android application: Appium UI, API contracts and
critical end-to-end journeys. The project follows Page Object and explicit
application-state fixtures.

## Layout

- `clients/` — HTTP clients based on `requests`.
- `config/` — typed environment settings and test data.
- `pages/` — one Page Object per application or system screen.
- `tests/ui`, `tests/api`, `tests/e2e` — test layers.

## Local setup

1. Create a project-local virtual environment and install locked dependencies:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python -m pip install -r requirements.lock
   ```

2. Copy `.env.example` to `.env` and configure a dedicated test account.
3. Start Appium and an emulator or connect a device.
4. Run the required suite:

   ```powershell
   pytest -m ui
   pytest -m api
   pytest -m e2e
   ```

## Test rules

- UI/E2E tests must use the explicit `logged_out_driver` fixture if login state
  is required.
- Use `resource-id` or Compose `testTag` locators before visible text.
- OTP debug extraction is permitted only when `DEBUG_OTP_ENABLED=true` and only
  for a test/debug build.
- Do not copy test phone numbers or credentials into test modules; obtain them
  through fixtures backed by environment settings.
- Every new critical scenario must have Allure ID, severity and feature.

## Allure

Pytest writes results to `allure-results`; failed Appium checks attach a
screenshot, page source and screen recording. Open a local report with:

```powershell
allure serve allure-results
```

## Isolated UI tests with WireMock

Start the mock service before the test job:

```powershell
docker compose -f docker-compose.test.yml up -d wiremock
```

Use `BACKEND_MODE=mock`, `WIREMOCK_ADMIN_URL=http://127.0.0.1:8080` and the
API address reachable by the Android runtime in `APP_API_BASE_URL`. A local
Android Emulator normally reaches the host at `http://10.0.2.2:8080`.

The mobile mock/debug build must support this endpoint override. Once it does,
run mock infrastructure checks with `pytest -m mock`, and isolated UI checks
with `pytest -m ui_mock`.

For a deterministic OTP UI flow, configure `MOCK_OTP_REQUEST_PATH` with the
Retrofit OTP-request route. The `ui_mock` scenario registers a WireMock
response `{"code":"1111"}` and asserts that the OTP UI displays and submits
that exact four-digit value.

## Capturing backend contracts

Use `docker-compose.record.yml` to run WireMock as a recording reverse proxy
against the dedicated dev/test backend. Captures are deliberately stored in
the ignored `mocks/recordings/` directory; sanitize them before promoting
selected mappings to `mocks/wiremock/`. See [mocks/README.md](mocks/README.md)
for the Android record-build requirements and commands.
