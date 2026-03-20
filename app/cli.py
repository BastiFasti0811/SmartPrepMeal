from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from app.planner import PlannerInput, generate_weekly_plan, weekly_plan_to_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="SmartMeal Wochenplan als Markdown erzeugen.")
    parser.add_argument("--week-start", type=str, help="Montag im Format YYYY-MM-DD")
    parser.add_argument("--family-size", type=int, default=4)
    parser.add_argument("--budget-min", type=float, default=85.0)
    parser.add_argument("--budget-max", type=float, default=95.0)
    parser.add_argument("--offer-mode", type=str, default="auto", choices=["auto", "live", "seed"])
    parser.add_argument("--out", type=str, default="weekly_plan.md")
    args = parser.parse_args()

    week_start = date.fromisoformat(args.week_start) if args.week_start else None
    plan = generate_weekly_plan(
        PlannerInput(
            family_size=args.family_size,
            budget_min_eur=args.budget_min,
            budget_max_eur=args.budget_max,
            week_start=week_start,
            offer_mode=args.offer_mode,
        )
    )
    markdown = weekly_plan_to_markdown(plan)
    output = Path(args.out)
    output.write_text(markdown, encoding="utf-8")
    print(f"Plan gespeichert: {output.resolve()}")


if __name__ == "__main__":
    main()
