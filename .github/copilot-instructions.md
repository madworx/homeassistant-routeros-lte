# Copilot Instructions

## Workflow

1. **Branch**: For every new feature or fix, create a new branch from `main` with a descriptive name (e.g., `feature/add-signal-sensor`, `fix/connection-timeout`).
2. **Develop**: Make changes, **always run tests** (`pytest tests/ -v`) and **ruff lint** (`ruff check custom_components/ tests/`) before committing. Fix any failures before proceeding.
3. **Confirm scope**: Before pushing, **ask the user** if the changes are complete and ready for a PR. If the user requests additional changes, go back to step 2. Only proceed once the user confirms.
4. **Push & open PR**: Push the branch and open a pull request on GitHub with a clear title and description summarizing the change (`gh pr create -R madworx/homeassistant-routeros-lte --title "..." --body "..."`).
5. **Wait for CI**: Check GitHub Actions status (`gh pr checks <PR_NUMBER> -R madworx/homeassistant-routeros-lte --watch`) and wait for all checks to pass. Fix any failures before proceeding.
6. **Confirm merge**: Once checks are green, **ask the user** to confirm the PR is ready to be merged. If the user requests further changes, make them (new commits on the same branch), push, and repeat from step 5. Only proceed once the user confirms.
7. **Merge**: Squash-merge the PR into `main` and delete the branch (`gh pr merge <PR_NUMBER> -R madworx/homeassistant-routeros-lte --squash --delete-branch`).
8. **Return to main**: After merging, switch back to `main` and pull the latest changes (`git checkout main && git pull`).

## Git Identity

- This repo uses `github-copilot[bot]` as the local git user. Do not change it.

## Git Safety

- **NEVER** force-push (`git push --force`, `git push -f`, `git push --force-with-lease`).
- **NEVER** amend commits that have already been pushed (`git commit --amend` after push).
- To fix mistakes on a pushed branch, always create a **new commit** on the existing branch.

## Repository

- Always specify `madworx/homeassistant-routeros-lte` when using `gh` commands that target a repository.
