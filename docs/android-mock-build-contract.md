# Android mock-build contract for Appium UI tests

The supplied `app-dev.apk` is not debuggable (`adb shell run-as` is rejected)
and its network security configuration disallows cleartext HTTP. A test suite
cannot redirect its Retrofit traffic to local WireMock without an Android
test artifact. Do not patch or re-sign the supplied APK for CI.

## Required Android artifact

The mobile repository must publish a signed `mockDebug` (or `uiTest`) APK with
these properties:

1. Retrofit's base URL is read from `BuildConfig.API_BASE_URL`.
2. The mock flavor sets `API_BASE_URL` to a CI property, for example
   `http://10.0.2.2:8080/` for a local emulator.
3. Only this flavor permits cleartext traffic to `10.0.2.2`; production and
   ordinary dev flavors continue to require HTTPS.
4. Its application id and launch activity remain
   `com.sminex.sminex_app` / `com.sminex.sminex_app.MainActivity`, or are
   supplied through `APP_PACKAGE` and `APP_ACTIVITY`.

Illustrative Gradle setup:

```kotlin
android {
    flavorDimensions += "testMode"
    productFlavors {
        create("mock") {
            dimension = "testMode"
            buildConfigField(
                "String",
                "API_BASE_URL",
                "\\\"${providers.gradleProperty("testApiBaseUrl")
                    .getOrElse("http://10.0.2.2:8080/")}\\\"",
            )
        }
    }
}
```

The Retrofit factory must use `BuildConfig.API_BASE_URL`, not a literal URL.

## CI execution

1. Start `docker compose -f docker-compose.test.yml up -d wiremock`.
2. Install the `mockDebug` APK and set `APP_MODE=apk` / `APP_PATH`.
3. Set `BACKEND_MODE=mock`,
   `WIREMOCK_ADMIN_URL=http://127.0.0.1:8080`, and
   `APP_API_BASE_URL=http://10.0.2.2:8080`.
4. Run `pytest -m ui_mock`.

`test_otp_login_with_mocked_code_1111` registers the real auth routes:

- `POST /api/v1/auth/send` returns `{"code":"1111"}`;
- `POST /api/v1/auth/token` returns a deterministic token response.

Add stable WireMock mappings for the post-login data requests listed in
`docs/backend-endpoints.md` as each home-screen component is brought under UI
test coverage. Captured traffic may be used as input, but must be sanitized
before committing it.
