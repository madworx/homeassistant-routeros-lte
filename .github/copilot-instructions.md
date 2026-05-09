# Copilot Instructions

## Workflow

1. **Branch**: For every new feature or fix, create a new branch from `main` with a descriptive name (e.g., `feature/add-signal-sensor`, `fix/connection-timeout`).
2. **Develop**: Make changes, **always run tests** (`pytest tests/ -v`) and **ruff lint** (`ruff check custom_components/ tests/`) before committing. Fix any failures before proceeding.
3. **Push & open PR**: Push the branch and open a pull request on GitHub with a clear title and description summarizing the change (`gh pr create -R madworx/homeassistant-routeros-lte --title "..." --body "..."`).
4. **Wait for CI**: Check GitHub Actions status (`gh pr checks <PR_NUMBER> -R madworx/homeassistant-routeros-lte --watch`) and wait for all checks to pass. Fix any failures before proceeding.
5. **Merge**: Once checks are green, squash-merge the PR into `main` and delete the branch (`gh pr merge <PR_NUMBER> -R madworx/homeassistant-routeros-lte --squash --delete-branch`).
6. **Return to main**: After merging, switch back to `main` and pull the latest changes (`git checkout main && git pull`).

## Git Identity

- This repo uses `github-copilot[bot]` as the local git user. Do not change it.

## Git Safety

- **NEVER** force-push (`git push --force`, `git push -f`, `git push --force-with-lease`).
- **NEVER** amend commits that have already been pushed (`git commit --amend` after push).
- To fix mistakes on a pushed branch, always create a **new commit** on the existing branch.

## Repository

- Always specify `madworx/homeassistant-routeros-lte` when using `gh` commands that target a repository.
