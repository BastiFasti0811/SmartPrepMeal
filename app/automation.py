from __future__ import annotations

import argparse
import subprocess
from datetime import date, datetime
from pathlib import Path

from app.planner import PlannerInput, generate_weekly_plan, weekly_plan_to_markdown


TASK_NAME = "SmartMealWeeklyPlannerSunday"


def run_weekly_export(
    output_dir: Path,
    family_size: int = 4,
    budget_min: float = 85.0,
    budget_max: float = 95.0,
    offer_mode: str = "auto",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    plan = generate_weekly_plan(
        PlannerInput(
            family_size=family_size,
            budget_min_eur=budget_min,
            budget_max_eur=budget_max,
            week_start=None,
            offer_mode=offer_mode,
        )
    )
    markdown = weekly_plan_to_markdown(plan)
    filename = output_dir / f"weekly_plan_{plan.start_date.isoformat()}.md"
    latest = output_dir / "latest_weekly_plan.md"
    filename.write_text(markdown, encoding="utf-8")
    latest.write_text(markdown, encoding="utf-8")
    log = output_dir / "automation.log"
    with log.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{datetime.now().isoformat(timespec='seconds')} | generated {filename.name} | source={plan.offers_source} | offers={plan.offers_count}\n"
        )
    print(f"Plan exportiert: {filename.resolve()} (heute: {today.isoformat()})")
    return filename


def register_windows_task(project_root: Path, output_dir: Path, run_time: str = "07:30") -> None:
    command = (
        f'cmd /c "cd /d {project_root} && python -m app.automation --output-dir {output_dir} --offer-mode auto"'
    )
    subprocess.run(
        [
            "schtasks",
            "/Create",
            "/SC",
            "WEEKLY",
            "/D",
            "SUN",
            "/TN",
            TASK_NAME,
            "/TR",
            command,
            "/ST",
            run_time,
            "/F",
        ],
        check=True,
    )
    print(f"Scheduled Task angelegt: {TASK_NAME} (Sonntag {run_time})")


def show_task_status() -> None:
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Task nicht gefunden.")
        return
    print(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description="SmartMeal Sonntags-Automation")
    parser.add_argument("--output-dir", type=str, default="exports")
    parser.add_argument("--family-size", type=int, default=4)
    parser.add_argument("--budget-min", type=float, default=85.0)
    parser.add_argument("--budget-max", type=float, default=95.0)
    parser.add_argument("--offer-mode", type=str, default="auto", choices=["auto", "live", "seed"])
    parser.add_argument("--register-task", action="store_true")
    parser.add_argument("--task-time", type=str, default="07:30")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir

    if args.register_task:
        register_windows_task(project_root=project_root, output_dir=output_dir, run_time=args.task_time)
        return
    if args.status:
        show_task_status()
        return

    run_weekly_export(
        output_dir=output_dir,
        family_size=args.family_size,
        budget_min=args.budget_min,
        budget_max=args.budget_max,
        offer_mode=args.offer_mode,
    )


if __name__ == "__main__":
    main()
