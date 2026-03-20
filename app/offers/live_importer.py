from __future__ import annotations

import html
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from app.data.seed_data import get_seed_offers
from app.models import OfferItem, Store

USER_AGENT = "Mozilla/5.0 (compatible; SmartMealPlanner/1.0; +https://localhost)"
CACHE_PATH = Path("app/data/cache/live_offers.json")


@dataclass(slots=True)
class OfferLoadResult:
    offers: list[OfferItem]
    source: str
    warnings: list[str]


def _normalize_name(value: str) -> str:
    text = value.strip().lower()
    text = (
        text.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def _parse_price(value: str) -> float | None:
    cleaned = value.replace("\xa0", " ").replace("EUR", "").replace("€", "").strip()
    compact = cleaned.replace(" ", "")
    m = re.search(r"(\d+[.,]\d{1,2})", compact)
    if not m:
        m = re.search(r"(\d+)\s*\.\s*(\d{2})", cleaned)
        if not m:
            return None
        return float(f"{m.group(1)}.{m.group(2)}")
    return float(m.group(1).replace(",", "."))


def _parse_date_dotted(value: str) -> date | None:
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", value)
    if not m:
        return None
    return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))


def _parse_date_dashed_range(value: str) -> tuple[date, date] | None:
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})\s*bis\s*(\d{2})-(\d{2})-(\d{4})", value)
    if not m:
        return None
    start = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    end = date(int(m.group(6)), int(m.group(5)), int(m.group(4)))
    return start, end


def _guess_amount_from_title(title: str) -> str:
    m = re.search(r"(\d+[.,]?\d*\s?(?:kg|g|ml|l|stk|stuck))", _normalize_name(title))
    if m:
        return m.group(1).replace("stuck", "Stk")
    return "k.A."


def _clean_amount(value: str) -> str:
    text = " ".join(value.split())
    text = re.sub(r"\s*1\s*kg\s*=\s*[\d.,]+", "", text, flags=re.I)
    text = re.sub(r"\s*1\s*l\s*=\s*[\d.,]+", "", text, flags=re.I)
    text = text.strip(" -")
    return text[:80] if text else "k.A."


def _dedupe(offers: list[OfferItem]) -> list[OfferItem]:
    unique: dict[tuple[str, str], OfferItem] = {}
    for offer in offers:
        key = (offer.store.value, _normalize_name(offer.name))
        existing = unique.get(key)
        if existing is None or offer.sale_price_eur < existing.sale_price_eur:
            unique[key] = offer
    return list(unique.values())


def _to_dict(offer: OfferItem) -> dict:
    return {
        "store": offer.store.value,
        "name": offer.name,
        "amount": offer.amount,
        "sale_price_eur": offer.sale_price_eur,
        "regular_price_eur": offer.regular_price_eur,
        "valid_from": offer.valid_from.isoformat(),
        "valid_to": offer.valid_to.isoformat(),
    }


def _from_dict(data: dict) -> OfferItem:
    return OfferItem(
        store=Store(data["store"]),
        name=data["name"],
        amount=data["amount"],
        sale_price_eur=float(data["sale_price_eur"]),
        regular_price_eur=float(data["regular_price_eur"]),
        valid_from=date.fromisoformat(data["valid_from"]),
        valid_to=date.fromisoformat(data["valid_to"]),
    )


def _load_cache(week_start: date, max_age_hours: int = 14) -> list[OfferItem] | None:
    if not CACHE_PATH.exists():
        return None
    try:
        payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(payload["cached_at"])
        if datetime.now() - cached_at > timedelta(hours=max_age_hours):
            return None
        if payload.get("week_start") != week_start.isoformat():
            return None
        return [_from_dict(item) for item in payload.get("offers", [])]
    except Exception:
        return None


def _write_cache(week_start: date, offers: list[OfferItem]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "cached_at": datetime.now().isoformat(timespec="seconds"),
        "week_start": week_start.isoformat(),
        "offers": [_to_dict(item) for item in offers],
    }
    CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _fetch_aldi_offers(week_start: date) -> list[OfferItem]:
    root_url = "https://publish.prod.emea.cms.aldi.cx/content/aldi/emea/de-aldisued/web/main/de.content.v1.api/content.json"
    response = requests.get(root_url, timeout=25, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    text = json.dumps(response.json(), ensure_ascii=False)
    urls = sorted(set(re.findall(r"https://www\.aldi-sued\.de/angebote/\d{4}-\d{2}-\d{2}[^\"\s]*", text)))
    urls = [url for url in urls if "utm_label=food" in url] or urls[:2]

    offers: list[OfferItem] = []
    for url in urls[:3]:
        html_text = requests.get(url, timeout=25, headers={"User-Agent": USER_AGENT}).text
        soup = BeautifulSoup(html_text, "html.parser")
        for tile in soup.select(".product-teaser-item"):
            title_el = tile.select_one(".product-tile__name p")
            price_el = tile.select_one(".base-price__regular")
            if not title_el or not price_el:
                continue
            sale = _parse_price(price_el.get_text(" ", strip=True))
            if sale is None:
                continue
            name = " ".join(title_el.get_text(" ", strip=True).split())
            old_el = tile.select_one(".base-price__old-price")
            regular = _parse_price(old_el.get_text(" ", strip=True) if old_el else "") or round(sale * 1.22, 2)
            amount_el = tile.select_one(".product-tile__unit-of-measurement p")
            amount = _clean_amount(amount_el.get_text(" ", strip=True)) if amount_el else _guess_amount_from_title(name)
            valid_label = tile.select_one(".base-label")
            valid_from = _parse_date_dotted(valid_label.get_text(" ", strip=True) if valid_label else "") or week_start
            valid_to = valid_from + timedelta(days=5)
            offers.append(
                OfferItem(
                    store=Store.ALDI_SUED,
                    name=name,
                    amount=amount,
                    sale_price_eur=round(sale, 2),
                    regular_price_eur=round(max(regular, sale), 2),
                    valid_from=valid_from,
                    valid_to=valid_to,
                )
            )
    return offers


def _fetch_kaufland_offers(week_start: date) -> list[OfferItem]:
    url = "https://filiale.kaufland.de/angebote.html"
    html_text = requests.get(url, timeout=25, headers={"User-Agent": USER_AGENT}).text
    soup = BeautifulSoup(html_text, "html.parser")
    page_text = " ".join(soup.get_text(" ", strip=True).split())
    dates = re.findall(r"\d{2}\.\d{2}\.\d{4}", page_text)
    if len(dates) >= 2:
        valid_from = _parse_date_dotted(dates[0]) or (week_start + timedelta(days=3))
        valid_to = _parse_date_dotted(dates[1]) or (valid_from + timedelta(days=6))
    else:
        valid_from = week_start + timedelta(days=3)
        valid_to = valid_from + timedelta(days=6)

    offers: list[OfferItem] = []
    for tile in soup.select(".k-product-tile")[:120]:
        title_el = tile.select_one(".k-product-tile__title")
        if not title_el:
            continue
        subtitle_el = tile.select_one(".k-product-tile__subtitle")
        name = " ".join(title_el.get_text(" ", strip=True).split())
        subtitle = " ".join(subtitle_el.get_text(" ", strip=True).split()) if subtitle_el else ""
        if subtitle:
            name = f"{subtitle} {name}"
        price_el = tile.select_one(".k-price-tag__price")
        sale = _parse_price(price_el.get_text(" ", strip=True) if price_el else "")
        if sale is None:
            continue
        old_el = tile.select_one(".k-price-tag__old-price")
        regular = _parse_price(old_el.get_text(" ", strip=True) if old_el else "") or round(sale * 1.2, 2)
        amount_el = tile.select_one(".k-product-tile__unit-price")
        amount = _clean_amount(amount_el.get_text(" ", strip=True)) if amount_el else _guess_amount_from_title(name)
        offers.append(
            OfferItem(
                store=Store.KAUFLAND,
                name=name,
                amount=amount,
                sale_price_eur=round(sale, 2),
                regular_price_eur=round(max(regular, sale), 2),
                valid_from=valid_from,
                valid_to=valid_to,
            )
        )
    return offers


def _fetch_netto_offers(week_start: date) -> list[OfferItem]:
    url = "https://www.netto.de/angebote/"
    html_text = requests.get(url, timeout=25, headers={"User-Agent": USER_AGENT}).text
    soup = BeautifulSoup(html_text, "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    date_range = _parse_date_dashed_range(text)
    if date_range:
        valid_from, valid_to = date_range
    else:
        valid_from = week_start
        valid_to = week_start + timedelta(days=5)

    offers: list[OfferItem] = []
    for h4 in soup.find_all("h4"):
        title = " ".join(h4.get_text(" ", strip=True).split())
        if len(title) < 4:
            continue
        ancestor = h4
        wrapper = None
        for _ in range(7):
            if ancestor.parent is None:
                break
            ancestor = ancestor.parent
            price_candidate = ancestor.find("h3")
            if price_candidate and re.search(r"\d", price_candidate.get_text(" ", strip=True)):
                wrapper = ancestor
                break
        if wrapper is None:
            continue
        price_text = " ".join(wrapper.find("h3").get_text(" ", strip=True).split())
        sale = _parse_price(price_text)
        if sale is None:
            continue
        detail_el = h4.find_next("p")
        amount = _clean_amount(detail_el.get_text(" ", strip=True)) if detail_el else _guess_amount_from_title(title)
        offers.append(
            OfferItem(
                store=Store.NETTO,
                name=title,
                amount=amount,
                sale_price_eur=round(sale, 2),
                regular_price_eur=round(sale * 1.2, 2),
                valid_from=valid_from,
                valid_to=valid_to,
            )
        )
    return offers


def _fetch_lidl_offers(week_start: date) -> list[OfferItem]:
    raw_html = requests.get("https://www.lidl.de/", timeout=25, headers={"User-Agent": USER_AGENT}).text
    decoded = html.unescape(raw_html)
    valid_from = week_start
    valid_to = week_start + timedelta(days=5)
    pattern = re.compile(
        r'"(?:fullTitle|title)"\s*:\s*"(?P<title>[^\"]{6,140})".{0,2500}?"price"\s*:\s*\{.{0,1000}?"price"\s*:\s*(?P<price>\d+(?:\.\d+)?)',
        re.S,
    )

    offers: list[OfferItem] = []
    for match in pattern.finditer(decoded):
        title = " ".join(match.group("title").split())
        if "{" in title or "}" in title:
            continue
        sale = float(match.group("price"))
        if sale <= 0.05 or sale > 300:
            continue
        fragment = decoded[match.start() : match.end() + 250]
        old_match = re.search(r'"oldPrice"\s*:\s*(\d+(?:\.\d+)?)', fragment)
        regular = float(old_match.group(1)) if old_match else round(sale * 1.18, 2)
        offers.append(
            OfferItem(
                store=Store.LIDL,
                name=title,
                amount=_guess_amount_from_title(title),
                sale_price_eur=round(sale, 2),
                regular_price_eur=round(max(regular, sale), 2),
                valid_from=valid_from,
                valid_to=valid_to,
            )
        )
        if len(offers) >= 120:
            break
    return offers


def _fetch_live_offers(week_start: date) -> tuple[list[OfferItem], list[str]]:
    providers = [
        (Store.LIDL, _fetch_lidl_offers),
        (Store.ALDI_SUED, _fetch_aldi_offers),
        (Store.NETTO, _fetch_netto_offers),
        (Store.KAUFLAND, _fetch_kaufland_offers),
    ]
    collected: list[OfferItem] = []
    warnings: list[str] = []

    for store, provider in providers:
        try:
            offers = provider(week_start)
            if not offers:
                warnings.append(f"{store.value}: Keine Live-Angebote erkannt, Seed-Fallback wird verwendet.")
            collected.extend(offers)
        except Exception as exc:
            warnings.append(f"{store.value}: Live-Import fehlgeschlagen ({type(exc).__name__}), Seed-Fallback wird verwendet.")

    return _dedupe(collected), warnings


def load_offers(
    reference_date: date,
    mode: str = "auto",
    preferred_stores: set[Store] | None = None,
) -> OfferLoadResult:
    week_start = reference_date - timedelta(days=reference_date.weekday())
    mode_clean = mode.lower().strip()
    preferred = preferred_stores or {Store.LIDL, Store.ALDI_SUED, Store.NETTO, Store.KAUFLAND}

    seed_all = get_seed_offers(week_start)
    seed_filtered = [offer for offer in seed_all if offer.store in preferred]

    if mode_clean == "seed":
        return OfferLoadResult(offers=seed_filtered, source="seed", warnings=[])

    warnings: list[str] = []
    cached = _load_cache(week_start)
    live_offers: list[OfferItem]
    source = "live"

    if cached:
        live_offers = [offer for offer in cached if offer.store in preferred]
        source = "live-cache"
    else:
        live_offers, warnings = _fetch_live_offers(week_start)
        live_offers = [offer for offer in live_offers if offer.store in preferred]
        if live_offers:
            _write_cache(week_start, live_offers)

    if mode_clean == "live":
        if live_offers:
            return OfferLoadResult(offers=live_offers, source=source, warnings=warnings)
        return OfferLoadResult(offers=seed_filtered, source="seed-fallback", warnings=warnings)

    # Auto mode: complete missing stores from seed data.
    live_by_store = {store: [offer for offer in live_offers if offer.store == store] for store in preferred}
    merged = list(live_offers)
    for store in preferred:
        if len(live_by_store[store]) < 10:
            fallback = [offer for offer in seed_filtered if offer.store == store]
            merged.extend(fallback)
            if len(live_by_store[store]) == 0:
                warnings.append(f"{store.value}: Vollstaendig auf Seed-Angebote zurueckgefallen.")
            else:
                warnings.append(f"{store.value}: Live-Angebote mit Seed-Angeboten ergaenzt.")

    return OfferLoadResult(offers=_dedupe(merged), source=f"{source}+seed", warnings=warnings)
