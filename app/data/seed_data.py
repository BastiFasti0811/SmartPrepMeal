from __future__ import annotations

from datetime import date, timedelta
from urllib.parse import quote_plus

from app.models import MealKind, OfferItem, Protein, Recipe, Store


def _search_url(source: str, query: str) -> str:
    q = quote_plus(query)
    if source == "Chefkoch":
        return f"https://www.chefkoch.de/rs/s0/{q}/Rezepte.html"
    if source == "LIDL Kochen":
        return f"https://www.lidl-kochen.de/suche?query={q}"
    if source == "Familienkost":
        return f"https://www.familienkost.de/suche?q={q}"
    if source == "Emmi kocht einfach":
        return f"https://emmikochteinfach.de/?s={q}"
    return f"https://www.lecker.de/suche/{q}"


def get_recipe_catalog() -> list[Recipe]:
    return [
        Recipe(
            title="Zitronen-Haehnchen mit Brokkoli-Reis",
            kind=MealKind.LUNCH,
            prep_minutes=40,
            protein=Protein.POULTRY,
            source="Chefkoch",
            url=_search_url("Chefkoch", "Zitronen Haehnchen Brokkoli Reis"),
            rating=4.6,
            ingredients=["haehnchenbrust", "reis", "brokkoli", "zitrone", "joghurt"],
        ),
        Recipe(
            title="Puten-Gemuese-Pfanne mit Naturreis",
            kind=MealKind.LUNCH,
            prep_minutes=35,
            protein=Protein.POULTRY,
            source="LIDL Kochen",
            url=_search_url("LIDL Kochen", "Puten Gemuese Pfanne Reis"),
            rating=4.5,
            ingredients=["putenbrust", "paprika", "zucchini", "reis", "zwiebel"],
        ),
        Recipe(
            title="Haehnchen-Curry mit Kokosmilch",
            kind=MealKind.LUNCH,
            prep_minutes=45,
            protein=Protein.POULTRY,
            source="LECKER",
            url=_search_url("LECKER", "Haehnchen Curry Kokosmilch"),
            rating=4.7,
            ingredients=["haehnchenbrust", "kokosmilch", "karotte", "paprika", "reis"],
        ),
        Recipe(
            title="Rindergeschnetzeltes mit Paprika",
            kind=MealKind.LUNCH,
            prep_minutes=40,
            protein=Protein.BEEF,
            source="Chefkoch",
            url=_search_url("Chefkoch", "Rindergeschnetzeltes Paprika"),
            rating=4.7,
            ingredients=["rindfleisch", "paprika", "zwiebel", "sahne", "nudeln"],
        ),
        Recipe(
            title="Rindergulasch Schnelltopf",
            kind=MealKind.LUNCH,
            prep_minutes=45,
            protein=Protein.BEEF,
            source="Emmi kocht einfach",
            url=_search_url("Emmi kocht einfach", "Rindergulasch schnell"),
            rating=4.5,
            ingredients=["rindfleisch", "kartoffeln", "karotte", "zwiebel", "tomatenpassata"],
        ),
        Recipe(
            title="Ofenlachs mit Kartoffelspalten",
            kind=MealKind.LUNCH,
            prep_minutes=35,
            protein=Protein.FISH,
            source="LECKER",
            url=_search_url("LECKER", "Ofenlachs Kartoffelspalten"),
            rating=4.6,
            ingredients=["lachsfilet", "kartoffeln", "zitrone", "quark", "gurke"],
        ),
        Recipe(
            title="Kichererbsen-Spinat-Curry",
            kind=MealKind.LUNCH,
            prep_minutes=35,
            protein=Protein.VEGETARIAN,
            source="Familienkost",
            url=_search_url("Familienkost", "Kichererbsen Spinat Curry"),
            rating=4.5,
            ingredients=["kichererbsen", "spinat", "kokosmilch", "reis", "zwiebel"],
        ),
        Recipe(
            title="Gemuese-Lasagne mit Ricotta",
            kind=MealKind.LUNCH,
            prep_minutes=45,
            protein=Protein.VEGETARIAN,
            source="Chefkoch",
            url=_search_url("Chefkoch", "Gemuese Lasagne Ricotta"),
            rating=4.6,
            ingredients=["lasagneplatten", "zucchini", "paprika", "ricotta", "tomatenpassata"],
        ),
        Recipe(
            title="Brotzeit mit Kraeuterquark und Rohkost",
            kind=MealKind.DINNER,
            prep_minutes=15,
            protein=Protein.VEGETARIAN,
            source="Familienkost",
            url=_search_url("Familienkost", "Brotzeit Kraeuterquark Rohkost"),
            rating=4.4,
            ingredients=["vollkornbrot", "quark", "gurke", "karotte", "schnittlauch"],
        ),
        Recipe(
            title="Tomaten-Omelett mit Salat",
            kind=MealKind.DINNER,
            prep_minutes=20,
            protein=Protein.EGG,
            source="LIDL Kochen",
            url=_search_url("LIDL Kochen", "Tomaten Omelett Salat"),
            rating=4.5,
            ingredients=["eier", "tomaten", "blattsalat", "joghurt", "zwiebel"],
        ),
        Recipe(
            title="Bunter Couscous-Salat mit Feta",
            kind=MealKind.DINNER,
            prep_minutes=25,
            protein=Protein.VEGETARIAN,
            source="Chefkoch",
            url=_search_url("Chefkoch", "Couscous Salat Feta"),
            rating=4.4,
            ingredients=["couscous", "feta", "gurke", "paprika", "zitrone"],
        ),
        Recipe(
            title="Thunfisch-Bohnen-Salat",
            kind=MealKind.DINNER,
            prep_minutes=20,
            protein=Protein.FISH,
            source="LECKER",
            url=_search_url("LECKER", "Thunfisch Bohnen Salat"),
            rating=4.5,
            ingredients=["thunfisch", "bohnen", "mais", "zwiebel", "blattsalat"],
        ),
        Recipe(
            title="Spinat-Ruehrei mit Vollkorntoast",
            kind=MealKind.DINNER,
            prep_minutes=15,
            protein=Protein.EGG,
            source="Emmi kocht einfach",
            url=_search_url("Emmi kocht einfach", "Spinat Ruehrei Toast"),
            rating=4.4,
            ingredients=["eier", "spinat", "toast", "tomaten", "milch"],
        ),
        Recipe(
            title="Lammhack-Pfanne mit Couscous",
            kind=MealKind.DINNER,
            prep_minutes=25,
            protein=Protein.LAMB,
            source="Chefkoch",
            url=_search_url("Chefkoch", "Lammhack Pfanne Couscous"),
            rating=4.3,
            ingredients=["lammhack", "couscous", "paprika", "zwiebel", "joghurt"],
        ),
        Recipe(
            title="Ofenkartoffeln mit Kraeuterquark",
            kind=MealKind.DINNER,
            prep_minutes=30,
            protein=Protein.VEGETARIAN,
            source="Familienkost",
            url=_search_url("Familienkost", "Ofenkartoffeln Kraeuterquark"),
            rating=4.6,
            ingredients=["kartoffeln", "quark", "schnittlauch", "gurke", "zwiebel"],
        ),
    ]


def get_seed_offers(reference_date: date) -> list[OfferItem]:
    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_end = week_start + timedelta(days=6)
    next_week_start = week_start + timedelta(days=7)
    next_week_end = next_week_start + timedelta(days=6)

    return [
        OfferItem(Store.LIDL, "Frische Haehnchenbrustfilets", "1 kg", 7.99, 10.99, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.LIDL, "Naturjoghurt 3.5%", "500 g", 0.99, 1.39, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.LIDL, "Brokkoli", "500 g", 1.29, 1.99, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.LIDL, "Lachsfilet frisch", "400 g", 5.49, 7.49, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.LIDL, "Quark mild", "500 g", 0.89, 1.29, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.ALDI_SUED, "Putenbrust", "800 g", 6.49, 8.49, week_start + timedelta(days=1), week_start + timedelta(days=5)),
        OfferItem(Store.ALDI_SUED, "Langkornreis", "1 kg", 1.89, 2.49, week_start + timedelta(days=1), week_start + timedelta(days=6)),
        OfferItem(Store.ALDI_SUED, "Kichererbsen Konserve", "400 g", 0.79, 1.09, week_start + timedelta(days=1), week_start + timedelta(days=6)),
        OfferItem(Store.ALDI_SUED, "Spinat TK", "450 g", 1.39, 1.89, week_start + timedelta(days=1), week_start + timedelta(days=6)),
        OfferItem(Store.ALDI_SUED, "Eier Bodenhaltung", "10 Stk", 2.29, 2.99, week_start + timedelta(days=1), week_start + timedelta(days=6)),
        OfferItem(Store.NETTO, "Paprika Mix", "500 g", 1.69, 2.49, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.NETTO, "Zucchini", "500 g", 1.49, 1.99, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.NETTO, "Karotten", "1 kg", 0.99, 1.49, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.NETTO, "Kartoffeln", "2 kg", 2.49, 3.29, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.NETTO, "Vollkornbrot", "750 g", 1.79, 2.29, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.NETTO, "Speisezwiebeln", "2 kg", 1.79, 2.69, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.NETTO, "Milch 1.5%", "1 l", 0.99, 1.39, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.NETTO, "Vollkorntoast", "500 g", 1.19, 1.79, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.ALDI_SUED, "Penne", "500 g", 0.89, 1.29, week_start + timedelta(days=1), week_start + timedelta(days=6)),
        OfferItem(Store.ALDI_SUED, "Sahne", "200 ml", 0.89, 1.19, week_start + timedelta(days=1), week_start + timedelta(days=6)),
        OfferItem(Store.NETTO, "Thunfisch in eigenem Saft", "3x185 g", 3.49, 4.49, week_start + timedelta(days=3), week_end),
        OfferItem(Store.KAUFLAND, "Rindfleisch fuer Geschnetzeltes", "800 g", 8.99, 12.49, week_start + timedelta(days=3), week_end + timedelta(days=3)),
        OfferItem(Store.KAUFLAND, "Rinderhack", "500 g", 4.49, 6.29, week_start + timedelta(days=3), week_end + timedelta(days=3)),
        OfferItem(Store.KAUFLAND, "Lammhack", "400 g", 4.99, 6.49, week_start + timedelta(days=3), week_end + timedelta(days=3)),
        OfferItem(Store.KAUFLAND, "Ricotta", "250 g", 1.29, 1.89, week_start + timedelta(days=3), week_end + timedelta(days=3)),
        OfferItem(Store.KAUFLAND, "Lasagneplatten", "500 g", 1.19, 1.79, week_start + timedelta(days=3), week_end + timedelta(days=3)),
        OfferItem(Store.KAUFLAND, "Kokosmilch", "400 ml", 1.09, 1.59, week_start + timedelta(days=3), week_end + timedelta(days=3)),
        OfferItem(Store.NETTO, "Gurke", "Stk", 0.79, 1.19, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.NETTO, "Zitronen", "500 g", 1.49, 2.09, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.ALDI_SUED, "Mais Konserve", "300 g", 0.89, 1.19, week_start + timedelta(days=1), week_start + timedelta(days=6)),
        OfferItem(Store.ALDI_SUED, "Bohnen Konserve", "400 g", 0.85, 1.09, week_start + timedelta(days=1), week_start + timedelta(days=6)),
        OfferItem(Store.LIDL, "Tomatenpassata", "500 ml", 0.99, 1.29, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.LIDL, "Blattsalat Mix", "150 g", 1.19, 1.69, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.KAUFLAND, "Feta", "200 g", 1.59, 2.29, week_start + timedelta(days=3), week_end + timedelta(days=3)),
        OfferItem(Store.KAUFLAND, "Couscous", "500 g", 1.49, 2.09, week_start + timedelta(days=3), week_end + timedelta(days=3)),
        OfferItem(Store.LIDL, "Schnittlauch", "Bund", 0.69, 0.99, week_start, week_start + timedelta(days=5)),
        OfferItem(Store.LIDL, "Angebotsvorschau naechste Woche: Putenhack", "500 g", 3.99, 5.49, next_week_start, next_week_end),
        OfferItem(Store.ALDI_SUED, "Angebotsvorschau naechste Woche: Kabeljau TK", "400 g", 3.49, 4.99, next_week_start, next_week_end),
        OfferItem(Store.NETTO, "Angebotsvorschau naechste Woche: Bio Eier", "10 Stk", 2.19, 2.79, next_week_start, next_week_end),
        OfferItem(Store.KAUFLAND, "Angebotsvorschau naechste Woche: Rindersteak", "600 g", 9.99, 13.99, next_week_start, next_week_end),
    ]
