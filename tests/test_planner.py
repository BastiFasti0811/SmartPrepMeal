from datetime import date

from app.planner import PlannerInput, generate_weekly_plan


def test_generates_full_week_plan():
    plan = generate_weekly_plan(
        PlannerInput(
            family_size=4,
            budget_min_eur=85,
            budget_max_eur=95,
            week_start=date(2026, 3, 23),
            offer_mode="seed",
        )
    )
    assert len(plan.days) == 7
    assert plan.start_date == date(2026, 3, 23)
    assert plan.end_date == date(2026, 3, 29)


def test_no_pork_and_quality_checks():
    plan = generate_weekly_plan(PlannerInput(week_start=date(2026, 3, 23), offer_mode="seed"))
    assert plan.quality_checks["kein_schweinefleisch"] is True
    assert plan.quality_checks["alle_links_vorhanden"] is True
    assert plan.quality_checks["gueltigkeitsdaten_vollstaendig"] is True


def test_offer_ratio_and_budget_signal():
    plan = generate_weekly_plan(PlannerInput(week_start=date(2026, 3, 23), offer_mode="seed"))
    assert plan.metrics.offer_usage_pct >= 60.0
    assert plan.metrics.weekly_cost_eur > 0
    assert plan.metrics.savings_eur > 0


def test_lunch_main_ingredient_spacing():
    plan = generate_weekly_plan(PlannerInput(week_start=date(2026, 3, 23), offer_mode="seed"))
    assert plan.quality_checks["hauptzutat_mittag_3_tage_varianz"] is True


def test_plan_exposes_offer_source_metadata():
    plan = generate_weekly_plan(PlannerInput(week_start=date(2026, 3, 23), offer_mode="seed"))
    assert plan.offers_source == "seed"
    assert plan.offers_count > 0
