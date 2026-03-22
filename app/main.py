from __future__ import annotations

import os
from datetime import date

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.models import Store
from app.planner import PlannerInput, generate_weekly_plan, next_monday, weekly_plan_to_markdown
from app.security import RateLimitMiddleware, SecurityHeadersMiddleware, create_csrf_token, validate_csrf_token

app = FastAPI(title="SmartMeal Weekly Planner", version="0.1.0")
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=50)

allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=[host.strip() for host in allowed_hosts if host.strip()])

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

APP_SECRET = os.getenv("APP_SECRET", "smartmeal-dev-secret-change-me")
STORE_OPTIONS = [Store.LIDL, Store.ALDI_SUED, Store.NETTO, Store.KAUFLAND]
REGION_OPTIONS = [
    ("bundesweit", "Bundesweit"),
    ("nord", "Nord"),
    ("west", "West"),
    ("ost", "Ost"),
    ("sued", "Sued"),
    ("metropole", "Metropole"),
    ("laendlich", "Laendlich"),
]


def _client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _render_index(
    request: Request,
    *,
    error: str | None = None,
    result=None,
    markdown_output: str = "",
    defaults: dict | None = None,
) -> HTMLResponse:
    defaults = defaults or {}
    token = create_csrf_token(APP_SECRET, _client_id(request))
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "csrf_token": token,
            "error": error,
            "result": result,
            "markdown_output": markdown_output,
            "store_options": STORE_OPTIONS,
            "region_options": REGION_OPTIONS,
            "defaults": {
                "family_size": defaults.get("family_size", 4),
                "budget_min": defaults.get("budget_min", 85),
                "budget_max": defaults.get("budget_max", 95),
                "week_start": defaults.get("week_start", next_monday(date.today()).isoformat()),
                "stores": defaults.get("stores", [store.value for store in STORE_OPTIONS]),
                "offer_mode": defaults.get("offer_mode", "auto"),
                "region": defaults.get("region", "bundesweit"),
                "babies": defaults.get("babies", 0),
                "toddlers": defaults.get("toddlers", 0),
                "children": defaults.get("children", 0),
                "teenagers": defaults.get("teenagers", 0),
                "adults": defaults.get("adults", 0),
            },
        },
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return _render_index(request)


@app.post("/plan", response_class=HTMLResponse)
async def build_plan(
    request: Request,
    csrf_token: str = Form(...),
    family_size: int = Form(4),
    budget_min: float = Form(85.0),
    budget_max: float = Form(95.0),
    week_start: str = Form(...),
    offer_mode: str = Form("auto"),
    region: str = Form("bundesweit"),
    babies: int = Form(0),
    toddlers: int = Form(0),
    children: int = Form(0),
    teenagers: int = Form(0),
    adults: int = Form(0),
    stores: list[str] = Form(default=[]),
) -> HTMLResponse:
    defaults = {
        "family_size": family_size,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "week_start": week_start,
        "offer_mode": offer_mode,
        "region": region,
        "babies": babies,
        "toddlers": toddlers,
        "children": children,
        "teenagers": teenagers,
        "adults": adults,
        "stores": stores,
    }
    if not validate_csrf_token(APP_SECRET, _client_id(request), csrf_token):
        return _render_index(request, error="Sicherheits-Token ist ungueltig oder abgelaufen.", defaults=defaults)

    try:
        if family_size < 1 or family_size > 8:
            raise ValueError("Personenzahl muss zwischen 1 und 8 liegen.")
        if budget_min < 10 or budget_max > 300 or budget_min > budget_max:
            raise ValueError("Budget muss plausibel sein und Min <= Max.")
        for label, value in (
            ("Babys", babies),
            ("Kleinkinder", toddlers),
            ("Kinder", children),
            ("Jugendliche", teenagers),
            ("Erwachsene", adults),
        ):
            if value < 0 or value > 8:
                raise ValueError(f"{label} muessen zwischen 0 und 8 liegen.")
        composition_total = babies + toddlers + children + teenagers + adults
        if composition_total > 0:
            family_size = composition_total
            defaults["family_size"] = family_size
        if family_size < 1 or family_size > 10:
            raise ValueError("Gesamthaushalt muss zwischen 1 und 10 Personen liegen.")

        parsed_week_start = date.fromisoformat(week_start)
        if parsed_week_start.weekday() != 0:
            raise ValueError("Bitte einen Montag als Startdatum waehlen.")
        mode = offer_mode.lower().strip()
        if mode not in {"auto", "live", "seed"}:
            raise ValueError("Angebotsmodus muss auto, live oder seed sein.")
        region_value = region.lower().strip()
        if region_value not in {value for value, _label in REGION_OPTIONS}:
            raise ValueError("Region ist ungueltig.")
        selected_stores = {Store(store_name) for store_name in stores} if stores else set(STORE_OPTIONS)

        plan = generate_weekly_plan(
            PlannerInput(
                family_size=family_size,
                budget_min_eur=budget_min,
                budget_max_eur=budget_max,
                week_start=parsed_week_start,
                preferred_stores=selected_stores,
                offer_mode=mode,
                region=region_value,
                babies=babies,
                toddlers=toddlers,
                children=children,
                teenagers=teenagers,
                adults=adults,
            )
        )
        markdown_output = weekly_plan_to_markdown(plan)
        return _render_index(request, result=plan, markdown_output=markdown_output, defaults=defaults)
    except ValueError as exc:
        return _render_index(request, error=str(exc), defaults=defaults)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
