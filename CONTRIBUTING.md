# Contributing to II-Researcher

Thank you for your interest in contributing to II-Researcher! We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, and code.

## Getting Started

1. **Fork** the repository and clone your fork:

   ```bash
   git clone https://github.com/<your-username>/ii-researcher.git
   cd ii-researcher
   ```

2. **Install** the package in development mode with dev dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up pre-commit hooks** (we use [ruff](https://github.com/astral-sh/ruff) for linting and formatting):

   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Create a branch** for your change:

   ```bash
   git checkout -b feat/my-feature
   ```

## Running Tests

We use `pytest`. Please make sure the test suite passes before opening a pull request:

```bash
pip install pytest pytest-asyncio
pytest tests
```

If you add new functionality, please add tests that cover it. Tests live in the `tests/` directory and mirror the structure of the `ii_researcher/` package.

## Code Style

- Formatting and linting are enforced by **ruff** via pre-commit hooks — run `pre-commit run --all-files` before pushing.
- Keep lines under 120 characters.
- Prefer clear, descriptive names over comments.
- Follow the patterns already used in the codebase (async-first, type hints on public interfaces).

## Submitting a Pull Request

1. Keep pull requests focused — one logical change per PR.
2. Write a clear title and description: what the change does and why.
3. Link any related issues (e.g. `Fixes #123`).
4. Make sure CI passes (lint + tests run automatically on every PR).
5. A maintainer will review your PR. We may ask for changes — that's a normal part of the process!

## Reporting Bugs and Requesting Features

- **Bugs:** open a [bug report](https://github.com/Intelligent-Internet/ii-researcher/issues/new?template=bug_report.yml) with steps to reproduce, expected vs. actual behavior, and your environment (OS, Python version, provider configuration).
- **Features:** open a [feature request](https://github.com/Intelligent-Internet/ii-researcher/issues/new?template=feature_request.yml) describing the problem you want to solve.
- **Security issues:** please do **not** open a public issue — see our [Security Policy](SECURITY.md).

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

## License

By contributing to II-Researcher, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
