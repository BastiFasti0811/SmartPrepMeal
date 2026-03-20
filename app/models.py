from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Store(str, Enum):
    LIDL = "Lidl"
    ALDI_SUED = "Aldi Sued"
    NETTO = "Netto"
    KAUFLAND = "Kaufland"
    SONSTIGES = "Sonstiges"


class MealKind(str, Enum):
    LUNCH = "Mittagessen"
    DINNER = "Abendessen"


class Protein(str, Enum):
    VEGETARIAN = "Vegetarisch"
    FISH = "Fisch"
    POULTRY = "Gefluegel"
    BEEF = "Rind"
    EGG = "Ei"
    LAMB = "Lamm"


@dataclass(slots=True)
class OfferItem:
    store: Store
    name: str
    amount: str
    sale_price_eur: float
    regular_price_eur: float
    valid_from: date
    valid_to: date


@dataclass(slots=True)
class Recipe:
    title: str
    kind: MealKind
    prep_minutes: int
    protein: Protein
    source: str
    url: str
    rating: float
    ingredients: list[str]


@dataclass(slots=True)
class DayMeals:
    day_name: str
    date_value: date
    lunch: Recipe
    dinner: Recipe


@dataclass(slots=True)
class ShoppingEntry:
    ingredient: str
    amount: str
    store: Store
    sale_price_eur: float
    regular_price_eur: float
    valid_from: date | None
    valid_to: date | None
    used_for: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PlanMetrics:
    family_size: int
    budget_min_eur: float
    budget_max_eur: float
    weekly_cost_eur: float
    weekly_regular_cost_eur: float
    savings_eur: float
    savings_pct: float
    offer_usage_pct: float
    offer_usage_ratio: str


@dataclass(slots=True)
class HouseholdComposition:
    babies: int = 0
    toddlers: int = 0
    children: int = 0
    teenagers: int = 0
    adults: int = 0

    @property
    def total_people(self) -> int:
        return self.babies + self.toddlers + self.children + self.teenagers + self.adults

    @property
    def weighted_units(self) -> float:
        return (
            self.babies * 0.35
            + self.toddlers * 0.55
            + self.children * 0.8
            + self.teenagers * 1.15
            + self.adults * 1.0
        )


@dataclass(slots=True)
class WeeklyPlan:
    start_date: date
    end_date: date
    days: list[DayMeals]
    shopping_by_store: dict[Store, list[ShoppingEntry]]
    metrics: PlanMetrics
    preview_offers: list[OfferItem]
    quality_checks: dict[str, bool]
    offers_source: str
    offers_count: int
    region: str = "Bundesweit"
    household: HouseholdComposition = field(default_factory=HouseholdComposition)
    import_warnings: list[str] = field(default_factory=list)
