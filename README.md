# SmartMeal Weekly Planner

MVP-Webapp, die aus deinem Agent-Briefing eine benutzbare Anwendung macht:

- 7-Tage-Plan (Montag bis Sonntag) mit 2 Gerichten pro Tag
- Angebotsorientierte Planung (Lidl, Aldi Sued, Netto, Kaufland)
- Live-Angebotsimport mit resilientem Fallback auf Seed-Daten
- Ausschluss von Schweinefleisch
- Einkaufsliste nach Geschaeften inkl. Gueltigkeitszeitraum
- Kosten- und Ersparnis-Abschaetzung
- Markdown-Export

## Stack

- FastAPI
- Jinja2 Templates
- Vanilla CSS/JS
- Pytest

## Starten

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

App im Browser: `http://127.0.0.1:8000`

## Tests

```powershell
pytest -q
```

## CLI-Export (z. B. fuer Sonntagslauf)

```powershell
python -m app.cli --week-start 2026-03-23 --out weekly_plan.md
```

Mit Live-Import:

```powershell
python -m app.cli --week-start 2026-03-23 --offer-mode auto --out weekly_plan.md
```

## Sonntags-Autolauf

Einmalig Scheduled Task anlegen (Windows):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register_weekly_task.ps1 -Time 07:30
```

Manuell sofort ausfuehren:

```powershell
python -m app.automation --output-dir exports --offer-mode auto
```

## Security-Verbesserungen im MVP

- CSRF-Schutz fuer POST-Requests
- Security Headers (CSP, X-Frame-Options, no-sniff, Referrer Policy)
- Trusted Host Middleware
- Einfaches In-Memory Rate Limiting
- Serverseitige Input-Validierung

## Kostenlose Security-Automation (GitHub)

- Dependabot Updates: `.github/dependabot.yml`
- CodeQL SAST Scan: `.github/workflows/codeql.yml`
- CI Test-Gate: `.github/workflows/ci.yml`
- PR Quality Gate (Ruff, Bandit, pip-audit): `.github/workflows/pr-quality.yml`
- Optionale AI-PR-Reviews (Gemini/OpenAI): `.github/workflows/ai-pr-review.yml`

## UX-Verbesserungen im MVP

- Mobile-taugliches, klares Formular
- Tageskarten mit Rezeptlinks
- Checklisten pro Geschaeft
- Budget-Status und Angebotsquote sichtbar
- Ein-Klick Markdown-Kopie

## Hinweis zu Angebotsdaten

Der Importer verwendet pro Markt eine eigene Strategie:

- Aldi Sued: Produkt-Tiles aus den aktuellen Angebotsseiten
- Kaufland: Produkt-Tiles aus der Angebotsseite mit globalem Gueltigkeitszeitraum
- Netto: Angebotskarten aus der Angebotsseite
- Lidl: eingebettete Produkt/Preis-Daten der Startseite

Wenn Live-Daten fehlen oder ein Parser ausfaellt, erfolgt automatisch ein Fallback auf Seed-Angebote.

## AI Review Setup

- Gemini Styleguide: `.gemini/styleguide.md`
- Setup-Hinweise: `docs/ai-review-setup.md`
