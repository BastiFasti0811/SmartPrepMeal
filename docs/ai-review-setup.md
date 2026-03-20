# AI Review Setup

This repository is configured for AI-assisted review and free security checks.

## 1) Gemini Code Assist (GitHub App)

1. Open: `https://github.com/apps/gemini-code-assist`
2. Click **Install** and select `BastiFasti0811/SmartPrepMeal`.
3. Keep access restricted to this repository.
4. Ensure `.gemini/styleguide.md` is present (already added) so Gemini follows project rules.

## 2) GitHub Copilot / Codex usage notes

- Copilot code review and coding-agent flows are available in GitHub.
- On free plans, premium requests are limited.
- For this repository, prefer using Copilot for targeted PR reviews, not bulk regeneration.

## 3) Free built-in security automation now enabled

- Dependabot config: `.github/dependabot.yml`
- CodeQL scan workflow: `.github/workflows/codeql.yml`
- CI workflow: `.github/workflows/ci.yml`

## 4) Branch protection expectations

- Required status checks: `CI / test`
- 1 required approving review
- Code owner review required
- Conversation resolution required

## 5) Recommended operating mode

- Create feature branches from `main`
- Open PRs early
- Let AI reviewer annotate findings
- Human owner confirms merge safety
