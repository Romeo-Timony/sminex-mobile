# Promoting reviewed generated tests

Generated tests remain in `tests/review/<JIRA>/` until they are ready. Use the
promotion command to move only the completed tests to the main test suites:

```powershell
run\review\promote_review_tests.bat KAN-2 --kind api --verify
run\review\promote_review_tests.bat KAN-2 --kind api --verify --apply
```

The first command is a dry run. The second command runs the selected tests,
removes `@pytest.mark.review`, moves files to `tests/api`, `tests/ui`, or
`tests/e2e`, and changes the matching manifest entry to `promoted`.

Promotion stops before changing files if a candidate contains a `skip` marker,
`pass`, `TODO`, or `placeholder`, or if a destination filename already exists.
Use `--kind ui`, `--kind api`, or `--kind e2e` to promote independently ready
parts of one task.
