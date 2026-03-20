# SmartPrepMeal Gemini Review Guide

This file provides repository-specific review guidance for Gemini Code Assist in GitHub.

## Primary goals

- Keep weekly meal planning deterministic and family-friendly.
- Maintain hard no-pork rules across planner logic and seed/live offer handling.
- Prefer secure-by-default changes.
- Avoid breaking automation and CI behavior.

## Review priorities

1. Security first:
   - Input validation in `app/main.py` and form handlers.
   - CSRF, security headers, and rate limiting in `app/security.py`.
   - No secrets in source, docs, workflows, or commits.
2. Planning correctness:
   - No pork in recipes or inferred ingredients.
   - Offer usage quota and quality checks stay intact.
   - Costs and savings remain plausible.
3. Reliability:
   - Live importers must degrade gracefully to seed data.
   - Scheduled automation (`app/automation.py`) must keep working.
4. UX:
   - Keep forms and outputs accessible and clear on mobile/desktop.

## Code conventions

- Use Python type hints and dataclasses where already established.
- Keep functions focused and side effects explicit.
- Keep user-facing text in German where already used in UI.
- Prefer ASCII in source files.

## Test expectations

- Any planner or importer logic change should include/adjust tests in `tests/`.
- CI must pass (`CI / test`).
- If changing workflows/security, include a short rationale in PR description.
