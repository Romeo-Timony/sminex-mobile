# GitHub Actions: promotion of mobile review tests

`Promote Approved Tests` runs on a **self-hosted Windows runner**. GitHub-hosted
Ubuntu runners do not contain the installed Sminex app or a reusable Android
emulator, so they cannot validate these UI and E2E tests.

Before the first run, register a Windows self-hosted Actions runner for this
repository and ensure its runner account can access Android Platform Tools
(`adb`), an online emulator/device, Appium, and the Sminex Android app
(`com.sminex.sminex_app`). Add `TEST_PHONE` and `QASE_API_TOKEN` as repository
secrets.

The workflow verifies selected review tests, moves them into `tests/ui`,
`tests/api`, or `tests/e2e`, removes `@pytest.mark.review`, updates
`tests/review/manifest.json`, and records coverage on the linked manual Qase
case. A test must carry `@pytest.mark.qase_case("<numeric Qase case ID>")` for
the Qase update.

Dispatch **Actions → Promote Approved Tests → Run workflow**, enter the Jira
key, and leave verification enabled. The workflow commits and pushes resulting
changes under `tests/`.
