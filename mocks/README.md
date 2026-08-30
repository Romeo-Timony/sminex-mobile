# WireMock contracts

`mappings/` contains stable baseline mappings. Test-specific mappings must be
registered through the WireMock Admin API and reset after every test.

Before enabling a UI scenario, align its request path and JSON body with the
mobile API OpenAPI contract. Do not use a permissive catch-all mapping: it
would hide an unintended request from the application.

The Android debug/mock build must read `APP_API_BASE_URL`. For a local Android
Emulator this is normally `http://10.0.2.2:8080`; in containerized CI use the
Docker service address reachable from the emulator.

## Recording from the test backend

Use recording only with a dedicated test account and a test/dev backend:

```powershell
$env:WIREMOCK_PROXY_TARGET = "https://apigateway-sc-dev.sminex.digital"
docker compose -f docker-compose.record.yml up -d wiremock-recorder
```

Configure a dedicated `record` Android build to use
`http://10.0.2.2:8081` as its API base URL and to permit that cleartext host in
the **record flavor's** network-security config. The supplied APK rejects
cleartext traffic, so do not patch smali or redirect a production build.

WireMock proxies unmatched requests to `WIREMOCK_PROXY_TARGET` and writes the
observed mappings and response bodies to `mocks/recordings/`. Those files are
ignored by Git because they can contain bearer tokens, personal data and test
account identifiers. Review and sanitize every capture, then copy only the
minimal deterministic mappings into `mocks/wiremock/` for version control.

After recording, stop the recorder with:

```powershell
docker compose -f docker-compose.record.yml down
```
