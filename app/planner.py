from __future__ import annotations

import math
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from app.data.seed_data import get_recipe_catalog, get_seed_offers
from app.models import (
    DayMeals,
    HouseholdComposition,
    MealKind,
    OfferItem,
    PlanMetrics,
    Protein,
    Recipe,
    ShoppingEntry,
    Store,
    WeeklyPlan,
)
from app.offers.live_importer import load_offers

DAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
STORE_ORDER = [Store.LIDL, Store.ALDI_SUED, Store.NETTO, Store.KAUFLAND, Store.SONSTIGES]
BANNED_WORDS = {"schwein", "speck", "bacon", "schinken", "wurst", "pork"}
REGIONAL_PRICE_FACTOR = {
    "bundesweit": 1.00,
    "nord": 1.01,
    "west": 1.03,
    "ost": 0.98,
    "sued": 1.04,
    "metropole": 1.10,
    "laendlich": 0.95,
}


@dataclass(slots=True)
class PlannerInput:
    family_size: int = 4
    budget_min_eur: float = 85.0
    budget_max_eur: float = 95.0
    week_start: date | None = None
    preferred_stores: set[Store] | None = None
    offer_mode: str = "auto"
    region: str = "bundesweit"
    babies: int = 0
    toddlers: int = 0
    children: int = 0
    teenagers: int = 0
    adults: int = 0


def next_monday(today: date) -> date:
    days_ahead = (7 - today.weekday()) % 7
    days_ahead = 7 if days_ahead == 0 else days_ahead
    return today + timedelta(days=days_ahead)


def normalize_text(value: str) -> str:
    text = value.strip().lower()
    text = (
        text.replace("ae", "ae")
        .replace("oe", "oe")
        .replace("ue", "ue")
        .replace("a", "a")
    )
    text = (
        text.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def _offer_matches_ingredient(offer_name: str, ingredient: str) -> bool:
    offer_n = normalize_text(offer_name)
    ingredient_n = normalize_text(ingredient)
    if not ingredient_n:
        return False
    return ingredient_n in offer_n or any(part == ingredient_n for part in offer_n.split())


def _is_offer_usable_for_week(offer: OfferItem, week_start: date, week_end: date) -> bool:
    return offer.valid_from <= week_end and offer.valid_to >= week_start


def _recipe_offer_score(recipe: Recipe, offers: list[OfferItem], week_start: date, week_end: date) -> float:
    if not recipe.ingredients:
        return 0.0
    matches = 0
    for ingredient in recipe.ingredients:
        if any(_offer_matches_ingredient(offer.name, ingredient) and _is_offer_usable_for_week(offer, week_start, week_end) for offer in offers):
            matches += 1
    return matches / len(recipe.ingredients)


def _pick_recipe(
    candidates: list[Recipe],
    offers: list[OfferItem],
    week_start: date,
    week_end: date,
    already_used: set[str],
) -> Recipe:
    ranked = sorted(
        candidates,
        key=lambda rec: (_recipe_offer_score(rec, offers, week_start, week_end), rec.rating, -rec.prep_minutes),
        reverse=True,
    )
    for recipe in ranked:
        if recipe.title not in already_used:
            return recipe
    return ranked[0]


def _validate_recipe(recipe: Recipe) -> bool:
    combined = " ".join([recipe.title, *recipe.ingredients]).lower()
    return not any(bad in combined for bad in BANNED_WORDS)


def _select_week_recipes(catalog: list[Recipe], offers: list[OfferItem], week_start: date, week_end: date) -> list[tuple[Recipe, Recipe]]:
    lunch_targets = [
        Protein.POULTRY,
        Protein.BEEF,
        Protein.FISH,
        Protein.POULTRY,
        Protein.BEEF,
        Protein.VEGETARIAN,
        Protein.POULTRY,
    ]
    dinner_targets = [
        Protein.VEGETARIAN,
        Protein.EGG,
        Protein.LAMB,
        Protein.VEGETARIAN,
        Protein.EGG,
        Protein.FISH,
        Protein.VEGETARIAN,
    ]
    used_titles: set[str] = set()
    selected: list[tuple[Recipe, Recipe]] = []

    for idx in range(7):
        lunch_candidates = [
            recipe
            for recipe in catalog
            if recipe.kind == MealKind.LUNCH and recipe.protein == lunch_targets[idx] and 30 <= recipe.prep_minutes <= 45 and _validate_recipe(recipe)
        ]
        dinner_candidates = [
            recipe
            for recipe in catalog
            if recipe.kind == MealKind.DINNER and recipe.protein == dinner_targets[idx] and 15 <= recipe.prep_minutes <= 30 and _validate_recipe(recipe)
        ]
        lunch = _pick_recipe(lunch_candidates, offers, week_start, week_end, used_titles)
        used_titles.add(lunch.title)
        dinner = _pick_recipe(dinner_candidates, offers, week_start, week_end, used_titles)
        used_titles.add(dinner.title)
        selected.append((lunch, dinner))

    return selected


def _build_shopping_list(
    days: list[DayMeals],
    offers: list[OfferItem],
    week_start: date,
    week_end: date,
    household_units: float,
    regional_factor: float,
) -> tuple[dict[Store, list[ShoppingEntry]], float, float, float]:
    ingredient_usage: dict[str, list[str]] = defaultdict(list)
    ingredient_count: dict[str, int] = defaultdict(int)
    total_ingredients = 0
    offer_matched_ingredients = 0

    for day in days:
        for kind_label, recipe in (("Mittag", day.lunch), ("Abend", day.dinner)):
            for ingredient in recipe.ingredients:
                ingredient_count[ingredient] += 1
                ingredient_usage[ingredient].append(f"{kind_label} {day.day_name}: {recipe.title}")
                total_ingredients += 1

    grouped: dict[Store, list[ShoppingEntry]] = {store: [] for store in STORE_ORDER}
    weekly_cost = 0.0
    weekly_regular = 0.0
    person_factor = household_units / 4

    for ingredient, uses in ingredient_usage.items():
        matching_offers = [
            offer
            for offer in offers
            if _offer_matches_ingredient(offer.name, ingredient) and _is_offer_usable_for_week(offer, week_start, week_end)
        ]
        amount_multiplier = min(2.5, max(1.0, ingredient_count[ingredient] * 0.55)) * person_factor

        if matching_offers:
            best = min(matching_offers, key=lambda offer: offer.sale_price_eur)
            offer_matched_ingredients += ingredient_count[ingredient]
            sale = round(best.sale_price_eur * amount_multiplier * regional_factor, 2)
            regular = round(best.regular_price_eur * amount_multiplier * regional_factor, 2)
            entry = ShoppingEntry(
                ingredient=ingredient,
                amount=f"ca. {math.ceil(amount_multiplier)}x",
                store=best.store,
                sale_price_eur=sale,
                regular_price_eur=regular,
                valid_from=best.valid_from,
                valid_to=best.valid_to,
                used_for=sorted(set(uses)),
            )
            grouped[best.store].append(entry)
        else:
            fallback_sale = round(1.49 * amount_multiplier * regional_factor, 2)
            fallback_regular = round(1.89 * amount_multiplier * regional_factor, 2)
            entry = ShoppingEntry(
                ingredient=ingredient,
                amount=f"ca. {math.ceil(amount_multiplier)}x",
                store=Store.SONSTIGES,
                sale_price_eur=fallback_sale,
                regular_price_eur=fallback_regular,
                valid_from=None,
                valid_to=None,
                used_for=sorted(set(uses)),
            )
            grouped[Store.SONSTIGES].append(entry)

        weekly_cost += entry.sale_price_eur
        weekly_regular += entry.regular_price_eur

    for store in STORE_ORDER:
        grouped[store].sort(key=lambda item: item.ingredient)

    offer_usage = offer_matched_ingredients / total_ingredients if total_ingredients else 0.0
    return grouped, round(weekly_cost, 2), round(weekly_regular, 2), offer_usage


def _normalize_region(value: str) -> str:
    cleaned = normalize_text(value)
    return cleaned if cleaned in REGIONAL_PRICE_FACTOR else "bundesweit"


def _resolve_household(input_data: PlannerInput) -> HouseholdComposition:
    if any([input_data.babies, input_data.toddlers, input_data.children, input_data.teenagers, input_data.adults]):
        household = HouseholdComposition(
            babies=input_data.babies,
            toddlers=input_data.toddlers,
            children=input_data.children,
            teenagers=input_data.teenagers,
            adults=input_data.adults,
        )
        if household.total_people > 0:
            return household

    return HouseholdComposition(adults=max(1, input_data.family_size))


def _quality_checks(
    plan_days: list[DayMeals],
    shopping: dict[Store, list[ShoppingEntry]],
    offer_usage: float,
) -> dict[str, bool]:
    all_links_present = all(day.lunch.url.startswith("https://") and day.dinner.url.startswith("https://") for day in plan_days)
    no_pork = all(_validate_recipe(day.lunch) and _validate_recipe(day.dinner) for day in plan_days)
    offer_ratio_ok = offer_usage >= 0.6

    lunch_proteins = [day.lunch.protein for day in plan_days]
    spaced = True
    for idx, protein in enumerate(lunch_proteins):
        for prev in range(max(0, idx - 2), idx):
            if lunch_proteins[prev] == protein:
                spaced = False
                break
        if not spaced:
            break

    validity_dates = True
    for store, entries in shopping.items():
        if store == Store.SONSTIGES:
            continue
        for entry in entries:
            if entry.valid_from is None or entry.valid_to is None:
                validity_dates = False
                break
        if not validity_dates:
            break

    return {
        "alle_links_vorhanden": all_links_present,
        "kein_schweinefleisch": no_pork,
        "mindestens_60_prozent_angebote": offer_ratio_ok,
        "hauptzutat_mittag_3_tage_varianz": spaced,
        "gueltigkeitsdaten_vollstaendig": validity_dates,
    }


def generate_weekly_plan(input_data: PlannerInput) -> WeeklyPlan:
    week_start = input_data.week_start or next_monday(date.today())
    week_end = week_start + timedelta(days=6)
    normalized_region = _normalize_region(input_data.region)
    regional_factor = REGIONAL_PRICE_FACTOR[normalized_region]
    household = _resolve_household(input_data)
    family_size = household.total_people

    if input_data.offer_mode.lower().strip() == "seed":
        offers = get_seed_offers(week_start)
        source = "seed"
        warnings: list[str] = []
    else:
        offer_result = load_offers(
            reference_date=week_start,
            mode=input_data.offer_mode,
            preferred_stores=input_data.preferred_stores,
        )
        offers = offer_result.offers
        source = offer_result.source
        warnings = offer_result.warnings

    if input_data.preferred_stores:
        offers = [offer for offer in offers if offer.store in input_data.preferred_stores or offer.store == Store.SONSTIGES]

    catalog = get_recipe_catalog()
    selected_pairs = _select_week_recipes(catalog, offers, week_start, week_end)
    days: list[DayMeals] = []
    for idx, (lunch, dinner) in enumerate(selected_pairs):
        days.append(
            DayMeals(
                day_name=DAY_NAMES[idx],
                date_value=week_start + timedelta(days=idx),
                lunch=lunch,
                dinner=dinner,
            )
        )

    shopping, weekly_cost, weekly_regular, offer_usage = _build_shopping_list(
        days=days,
        offers=offers,
        week_start=week_start,
        week_end=week_end,
        household_units=household.weighted_units,
        regional_factor=regional_factor,
    )
    savings = round(weekly_regular - weekly_cost, 2)
    savings_pct = round((savings / weekly_regular * 100.0), 1) if weekly_regular else 0.0
    preview = sorted(
        [offer for offer in get_seed_offers(week_start) if offer.valid_from > week_end],
        key=lambda offer: (offer.valid_from, offer.store.value),
    )[:8]

    quality = _quality_checks(days, shopping, offer_usage)
    metrics = PlanMetrics(
        family_size=family_size,
        budget_min_eur=input_data.budget_min_eur,
        budget_max_eur=input_data.budget_max_eur,
        weekly_cost_eur=weekly_cost,
        weekly_regular_cost_eur=weekly_regular,
        savings_eur=savings,
        savings_pct=savings_pct,
        offer_usage_pct=round(offer_usage * 100.0, 1),
        offer_usage_ratio=f"{round(offer_usage * 100)}%",
    )

    return WeeklyPlan(
        start_date=week_start,
        end_date=week_end,
        days=days,
        shopping_by_store=shopping,
        metrics=metrics,
        preview_offers=preview,
        quality_checks=quality,
        offers_source=source,
        offers_count=len(offers),
        region=normalized_region.capitalize() if normalized_region != "laendlich" else "Laendlich",
        household=household,
        import_warnings=warnings,
    )


def weekly_plan_to_markdown(plan: WeeklyPlan) -> str:
    lines: list[str] = []
    lines.append(f"# SmartMeal Wochenplan ({plan.start_date.isoformat()} bis {plan.end_date.isoformat()})")
    lines.append("")
    lines.append("## Angebotsquelle")
    lines.append(f"- Quelle: **{plan.offers_source}**")
    lines.append(f"- Anzahl importierte Angebote: **{plan.offers_count}**")
    lines.append(f"- Region: **{plan.region}**")
    lines.append(
        "- Haushalt: "
        f"{plan.household.adults} Erwachsene, {plan.household.teenagers} Jugendliche, "
        f"{plan.household.children} Kinder, {plan.household.toddlers} Kleinkinder, {plan.household.babies} Babys"
    )
    if plan.import_warnings:
        for warning in plan.import_warnings:
            lines.append(f"- Hinweis: {warning}")
    lines.append("")
    lines.append("## 1. Taeglicher Speiseplan")
    for day in plan.days:
        lines.append(f"### {day.day_name} ({day.date_value.isoformat()})")
        lines.append(f"- Mittagessen: **{day.lunch.title}** ({day.lunch.prep_minutes} Min) - [{day.lunch.source}]({day.lunch.url})")
        lines.append(f"- Abendessen: **{day.dinner.title}** ({day.dinner.prep_minutes} Min) - [{day.dinner.source}]({day.dinner.url})")
    lines.append("")
    lines.append("## 2. Einkaufsliste nach Geschaeften")
    for store, entries in plan.shopping_by_store.items():
        if not entries:
            continue
        lines.append(f"### {store.value}")
        for entry in entries:
            validity = (
                f"{entry.valid_from.isoformat()} bis {entry.valid_to.isoformat()}"
                if entry.valid_from and entry.valid_to
                else "ohne Aktionszeitraum"
            )
            lines.append(
                f"- [ ] {entry.ingredient} ({entry.amount}) - {entry.sale_price_eur:.2f} EUR | gueltig: {validity} | fuer: {', '.join(entry.used_for[:2])}"
            )
    lines.append("")
    lines.append("## 3. Kosten & Ersparnis")
    lines.append(f"- Wochenkosten (geschaetzt): **{plan.metrics.weekly_cost_eur:.2f} EUR**")
    lines.append(f"- Ohne Angebote (geschaetzt): {plan.metrics.weekly_regular_cost_eur:.2f} EUR")
    lines.append(f"- Ersparnis: **{plan.metrics.savings_eur:.2f} EUR ({plan.metrics.savings_pct:.1f}%)**")
    lines.append(f"- Angebotsnutzung: **{plan.metrics.offer_usage_pct:.1f}%**")
    lines.append("")
    lines.append("## 4. Vorschau kommende Wochenangebote")
    for offer in plan.preview_offers:
        lines.append(
            f"- {offer.store.value}: {offer.name} ({offer.sale_price_eur:.2f} EUR, {offer.valid_from.isoformat()} bis {offer.valid_to.isoformat()})"
        )
    lines.append("")
    lines.append("## 5. Einkaufs-Tipps & Route")
    lines.append("- Starte bei Netto (Gemuesebasis), dann Aldi Sued (Grundnahrungsmittel), danach Lidl (Protein + Milch), zum Schluss Kaufland (Rind/Lamm/Fisch).")
    lines.append("- Kaufe frischen Fisch und Salat zuletzt, Tiefkuehlprodukte direkt vor Heimfahrt.")
    lines.append("- Budgettipp: Bei Preisabweichung zuerst Sonstiges-Artikel durch Eigenmarken ersetzen.")
    lines.append("")
    lines.append("## Qualitaetschecks")
    for check_name, is_ok in plan.quality_checks.items():
        lines.append(f"- {'OK' if is_ok else 'NICHT OK'}: {check_name}")
    return "\n".join(lines)
