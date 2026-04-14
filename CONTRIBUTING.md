# Contributing Guidelines

Thank you for contributing to the AI-Based Risk Assessment Database!

## Branching Strategy
We use a standard Feature Branch Workflow. 
1. The `main` branch is the source of truth and represents the stable, deployable code.
2. All new development, features, and bug fixes must occur on a new branch created from `main` (e.g., `feature/ppe-recommendations`, `bugfix/db-connection`).

## Pull Request & Merge Strategy
1. **Never push directly to `main`.** All changes must go through a Pull Request (PR).
2. **Use the PR Template:** Fill out the checklist provided in `.github/PULL_REQUEST_TEMPLATE.md`.
3. **Approvals:** All PRs require at least **one (1) approving review** from a fellow team member before they can be merged.
4. **Code Quality Requirements:**
   - All unit tests must pass (`pytest tests/python/`).
   - The code must be formatted using Black (`black --check api/`).
   - The code must pass Flake8 linting (`flake8 api/`).
   - If proposing API changes, ensure the README.md is updated.

## Setup for Local Development
Refer to the instructions in the main `README.md` to set up your local development environment.
Install the development tools via:
```bash
pip install -r api/requirements.txt
pip install -r api/requirements-dev.txt
```
