# AI Review Setup

This repository is configured for AI-assisted review and free security checks.

## 1) Gemini Code Assist (GitHub App)

1. Open: `https://github.com/apps/gemini-code-assist`
2. Click **Install** and select `BastiFasti0811/SmartPrepMeal`.
3. Keep access restricted to this repository.
4. Ensure `.gemini/styleguide.md` is present (already added) so Gemini follows project rules.

## 2) Automated AI PR reviews via GitHub Actions

Workflow file: `.github/workflows/ai-pr-review.yml`

Two optional jobs are configured:

- `Gemini Review` (requires `GEMINI_API_KEY`)
- `OpenAI Review` (requires `OPENAI_API_KEY`, works as Codex-style reviewer)

Required repository secrets:

- `GEMINI_API_KEY` (for Gemini job)
- `OPENAI_API_KEY` (for OpenAI job)

Optional repository variables:

- `GEMINI_REVIEW_MODEL` (default: `gemini-2.5-flash`)
- `OPENAI_REVIEW_MODEL` (default: `gpt-4.1-mini`)

Behavior:

- Trigger: PR opened/synchronized/reopened/ready-for-review
- Bot posts/updates one sticky comment per provider
- Only diff excerpts are reviewed (token-safe truncation)
- No untrusted PR code execution (workflow runs on `pull_request_target` and checks out base branch)

## 3) Free static code review/security gate

Workflow file: `.github/workflows/pr-quality.yml`

- Ruff linting
- Bandit SAST scan
- `pip-audit` dependency vulnerability check

Existing baseline:

- Dependabot config: `.github/dependabot.yml`
- CodeQL scan workflow: `.github/workflows/codeql.yml`
- CI test workflow: `.github/workflows/ci.yml`

## 4) Branch protection expectations

- Required status checks: `test`, `Analyze (python)`
- 1 required approving review
- Code owner review required
- Conversation resolution required

## 5) Recommended operating mode

- Create feature branches from `main`
- Open PRs early
- Let static checks and AI reviewer annotate findings
- Human owner confirms merge safety
