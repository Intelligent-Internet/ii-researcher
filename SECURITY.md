# Security Policy

## Supported Versions

We provide security fixes for the latest release of II-Researcher on the `main` branch and the most recent version published to [PyPI](https://pypi.org/project/ii-researcher/).

## Reporting a Vulnerability

We take the security of II-Researcher seriously. If you believe you have found a security vulnerability, please report it to us **privately** — do not open a public issue.

**Preferred:** report it through [GitHub private vulnerability reporting](https://github.com/Intelligent-Internet/ii-researcher/security/advisories/new).

**Alternatively:** email us at [emad@ii.inc](mailto:emad@ii.inc) with:

- A description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Any relevant configuration (providers, deployment mode)

We will acknowledge your report as soon as possible, keep you informed of our progress, and credit you in the fix release if you would like.

## Scope Notes

- II-Researcher executes searches and fetches untrusted web content by design. Deployments should treat scraped content as untrusted input.
- The FastAPI backend (`api.py`) ships with permissive CORS defaults intended for local development. Harden CORS, authentication, and network exposure before deploying it publicly.
- Never commit API keys. Use environment variables or an `.env` file (see `.env.example`), which is git-ignored.
