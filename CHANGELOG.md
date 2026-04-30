# Changelog

## v1.0.2

- Add detailed JSON output option with `--json` flag
- Add option to save output to a file with `--output [file]`
- Add `--version` and improve `--help` readability
- Bump dependencies and fully support Python 3.15
- Refactor tests and typing, add `ty`
- Tests no longer overwrite the dataset, add fuzzing to CLI tests
- Prefer `pathlib.Path` over `os.path`
- Enable Dependabot

## v1.0.1

- Housekeeping release
- Swap `click` for `rich-click`
- Refactor pixi.toml, GitHub Actions, linting, coverage
- Drop Python 3.10 support

## v1.0.0

- Initial release
