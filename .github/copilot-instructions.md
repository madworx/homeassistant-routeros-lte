# Copilot Instructions

## Workflow

- After every code change, **always run tests** (`pytest tests/ -v`) and **ruff lint** (`ruff check custom_components/ tests/`) before committing.
- Fix any failures before proceeding.
- Commit and push after each logical change.
- After pushing, check GitHub Actions status (`gh run list -R madworx/homeassistant-routeros-lte -L 1`) and wait for completion. Fix any failures before proceeding.

## Git Identity

- This repo uses `github-copilot[bot]` as the local git user. Do not change it.

## Repository

- Always specify `madworx/homeassistant-routeros-lte` when using `gh` commands that target a repository.
