# APK analysis: `app-dev.apk` 3.2.0

Analysis was performed against a read-only copy of the supplied development APK
using JADX 1.5.5 and Android build tools.

## Confirmed observations

- Package: `com.sminex.sminex_app`; version: `3.2.0`.
- The development build contains the backend base URL
  `https://apigateway-sc-dev.sminex.digital/`.
- The authentication module contains `SignInRemoteAPI`, `OTPRemoteAPI`,
  `TokensRemoteAPI`, `LoginByPhoneRequest`, `OtpResponse` and `OtpCodeDto`.
- The navigation contract to the OTP screen contains the keys
  `otp_screen_auth_type`, `otp_screen_debug_code`, `otp_screen_retry_after`
  and `otp_screen_user_data`.
- The debug OTP value is therefore part of the login response/navigation
  contract, not an Appium-only artefact. The existing E2E test reads it from
  the displayed OTP screen.
- `network_security_config.xml` rejects cleartext traffic. Its
  `debug-overrides` section trusts user-installed certificates.

## Implication for mocked UI tests

WireMock can provide deterministic responses only after the application points
to the WireMock URL. This must be implemented in the Android application as a
test/mock build configuration (for example `BuildConfig.API_BASE_URL` set from
`TEST_API_BASE_URL`). The production and ordinary dev endpoints must remain
unchanged.

Do not use host-file replacement or a MITM proxy as the CI architecture: the
app uses HTTPS, the emulator is a production image without `adb root`, and
such a setup is less reproducible than a dedicated test build.

## Next Android-side change

1. Add a `mockDebug` (or `uiTest`) product flavor.
2. Read the backend URL from `BuildConfig.API_BASE_URL` when creating Retrofit.
3. Make the value injectable through a Gradle property for CI.
4. Publish that APK as a CI artifact and run `pytest -m ui` against it with
   `BACKEND_MODE=mock`, `APP_API_BASE_URL=http://wiremock:8080`.

The Python suite and Docker WireMock administration client are already ready
for this contract; endpoint mappings should be filled from the Retrofit
interfaces once the application source or an endpoint specification is
available.
