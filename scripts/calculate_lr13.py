from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from security_channel.economic_calculation import build_calculation
from security_channel.economic_calculation import format_number
from security_channel.economic_calculation import save_calculation_reports



def main():
    calculation = build_calculation(ROOT)
    metrics = calculation["code_metrics"]["product"]
    results = calculation["results"]

    n_functions = metrics["functions"]
    loc = results["loc"]
    kdsi = results["kdsi"]
    pm = results["person_months"]
    dev_hours = results["development_hours"]
    total_hours = results["total_hours"]
    total_cost = results["total_cost"]

    report_paths = save_calculation_reports(calculation, ROOT / "reports")

    print("Автоматизированный расчет ЛР13")
    print(f"Проект: {calculation['project']['name']}")
    print(f"Функции/методы основного продукта: {n_functions}")
    print(f"LOC: {loc}")
    print(f"KDSI: {format_number(kdsi, 3)}")
    print(f"M: {format_number(results['multiplier_m'], 3)}")
    print(f"PM: {format_number(pm)} чел.-мес.")
    print(f"Трудоемкость разработки: {dev_hours} ч")
    print(f"Полная трудоемкость проекта: {total_hours} ч")
    print(f"Полная стоимость проекта: {total_cost:,} руб.".replace(",", " "))
    print(f"JSON сохранен: {report_paths['json']}")
    print(f"CSV сохранен: {report_paths['csv']}")


if __name__ == "__main__":
    main()
