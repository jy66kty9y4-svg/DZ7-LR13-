import ast
import csv
import json
import tokenize
from dataclasses import dataclass
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".tools",
    "migrations",
    "node_modules",
    "staticfiles",
    "dist",
    "build",
    "reports",
}

EXCLUDED_FILES = {
    "economic_calculation.py",
}

TEST_FILE_PATTERNS = (
    "test_",
    "tests.py",
)


@dataclass(frozen=True)
class CalculationConfig:
    accepted_avc: int = 19
    hours_per_person_month: int = 160
    rely: float = 1.15
    rcpx: float = 1.33
    ruse: float = 1.00
    pdif: float = 1.00
    prex: float = 1.00
    fcil: float = 0.87
    sced: float = 1.00
    additional_testing_hours: int = 35
    security_review_hours: int = 30
    documentation_hours: int = 25
    management_hours: int = 20
    platform_cost: int = 11000
    maintenance_cost: int = 40000
    training_cost: int = 44000


def should_skip_path(path):
    return any(part in EXCLUDED_DIRS for part in path.parts)


def is_test_file(path):
    return path.name.startswith(TEST_FILE_PATTERNS[0]) or path.name == TEST_FILE_PATTERNS[1] or "tests" in path.parts


def iter_python_files(root):
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if should_skip_path(relative):
            continue
        if path.name in EXCLUDED_FILES:
            continue
        if relative.parts[0] == "scripts":
            continue
        yield path


def count_effective_lines(path):
    effective_lines = set()

    with path.open("rb") as file:
        for token in tokenize.tokenize(file.readline):
            if token.type in {
                tokenize.COMMENT,
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.ENCODING,
                tokenize.ENDMARKER,
                tokenize.INDENT,
                tokenize.DEDENT,
            }:
                continue
            effective_lines.add(token.start[0])

    return len(effective_lines)


def count_file_metrics(path):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)

    return {
        "file": str(path),
        "physical_lines": len(text.splitlines()),
        "effective_lines": count_effective_lines(path),
        "functions": sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree)),
        "classes": sum(isinstance(node, ast.ClassDef) for node in ast.walk(tree)),
    }


def empty_metrics():
    return {
        "files": [],
        "physical_lines": 0,
        "effective_lines": 0,
        "functions": 0,
        "classes": 0,
    }


def add_file_metrics(total, file_metrics, root):
    total["files"].append(str(Path(file_metrics["file"]).relative_to(root)))
    total["physical_lines"] += file_metrics["physical_lines"]
    total["effective_lines"] += file_metrics["effective_lines"]
    total["functions"] += file_metrics["functions"]
    total["classes"] += file_metrics["classes"]


def collect_code_metrics(root):
    root = Path(root).resolve()
    product = empty_metrics()
    tests = empty_metrics()

    for path in iter_python_files(root):
        metrics = count_file_metrics(path)

        if is_test_file(path.relative_to(root)):
            add_file_metrics(tests, metrics, root)
        else:
            add_file_metrics(product, metrics, root)

    all_code = {
        "files": product["files"] + tests["files"],
        "physical_lines": product["physical_lines"] + tests["physical_lines"],
        "effective_lines": product["effective_lines"] + tests["effective_lines"],
        "functions": product["functions"] + tests["functions"],
        "classes": product["classes"] + tests["classes"],
    }

    return {
        "product": product,
        "tests": tests,
        "all": all_code,
    }


def build_multiplier(config):
    return config.rely * config.rcpx * config.ruse * config.pdif * config.prex * config.fcil * config.sced


def build_personnel_costs(development_hours, config):
    return [
        {
            "role": "Программист Python / Django",
            "work": "Доработка Django-приложения, сервисной логики и автоматизации расчета",
            "hours": development_hours,
            "rate": 3000,
            "cost": development_hours * 3000,
        },
        {
            "role": "Специалист по информационной безопасности",
            "work": "Проверка логики ACCESS_KEY, блокировок, обработки ошибок и метрик",
            "hours": config.security_review_hours,
            "rate": 4000,
            "cost": config.security_review_hours * 4000,
        },
        {
            "role": "Тестировщик",
            "work": "pytest, проверка CSV/JSON, сценарии ALLOW/BLOCK и воспроизводимость",
            "hours": config.additional_testing_hours,
            "rate": 2500,
            "cost": config.additional_testing_hours * 2500,
        },
        {
            "role": "Технический писатель",
            "work": "Отчет, таблицы, расчеты, выводы и оформление ЛР13",
            "hours": config.documentation_hours,
            "rate": 2000,
            "cost": config.documentation_hours * 2000,
        },
        {
            "role": "Аналитик / руководитель проекта",
            "work": "Декомпозиция работ, календарный план, контроль расчетов и план найма",
            "hours": config.management_hours,
            "rate": 3500,
            "cost": config.management_hours * 3500,
        },
    ]


def build_calculation(root, config=None):
    root = Path(root).resolve()
    config = config or CalculationConfig()
    code_metrics = collect_code_metrics(root)
    product = code_metrics["product"]

    if product["functions"] == 0:
        raise ValueError("Не удалось рассчитать AVC: в основном продукте не найдены функции или методы.")

    physical_avc = product["physical_lines"] / product["functions"]
    effective_avc = product["effective_lines"] / product["functions"]
    loc = product["functions"] * config.accepted_avc
    kdsi = loc / 1000
    multiplier_m = build_multiplier(config)
    person_months = 2.4 * (kdsi ** 1.05) * multiplier_m
    development_hours = round(person_months * config.hours_per_person_month)
    additional_hours = (
        config.additional_testing_hours
        + config.security_review_hours
        + config.documentation_hours
        + config.management_hours
    )
    total_hours = development_hours + additional_hours
    personnel_items = build_personnel_costs(development_hours, config)
    personnel_cost = sum(item["cost"] for item in personnel_items)
    total_cost = personnel_cost + config.platform_cost + config.maintenance_cost + config.training_cost

    return {
        "project": {
            "variant": "57",
            "student": "Семенов С. С.",
            "group": "КП-23-17",
            "name": "Контейнер безопасности для контроля доступа к виртуальным каналам передачи данных",
            "implementation": "Python/Django-микросервис security_channel",
        },
        "code_metrics": code_metrics,
        "coefficients": {
            "accepted_avc": config.accepted_avc,
            "hours_per_person_month": config.hours_per_person_month,
            "RELY": config.rely,
            "RCPX": config.rcpx,
            "RUSE": config.ruse,
            "PDIF": config.pdif,
            "PREX": config.prex,
            "FCIL": config.fcil,
            "SCED": config.sced,
        },
        "work_hours": {
            "additional_testing_hours": config.additional_testing_hours,
            "security_review_hours": config.security_review_hours,
            "documentation_hours": config.documentation_hours,
            "management_hours": config.management_hours,
            "additional_hours": additional_hours,
        },
        "costs": {
            "personnel": personnel_items,
            "platform_cost": config.platform_cost,
            "maintenance_cost": config.maintenance_cost,
            "training_cost": config.training_cost,
        },
        "results": {
            "physical_lines": product["physical_lines"],
            "effective_lines": product["effective_lines"],
            "functions": product["functions"],
            "classes": product["classes"],
            "test_physical_lines": code_metrics["tests"]["physical_lines"],
            "test_functions": code_metrics["tests"]["functions"],
            "physical_avc": physical_avc,
            "effective_avc": effective_avc,
            "accepted_avc": config.accepted_avc,
            "loc": loc,
            "kdsi": kdsi,
            "multiplier_m": multiplier_m,
            "person_months": person_months,
            "development_hours": development_hours,
            "total_hours": total_hours,
            "personnel_cost": personnel_cost,
            "total_cost": total_cost,
        },
    }


def format_number(value, digits=2):
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}".replace(".", ",")


def build_csv_rows(calculation):
    results = calculation["results"]

    return [
        ("Физические строки основного продукта", results["physical_lines"]),
        ("Непустые строки без комментариев", results["effective_lines"]),
        ("Число функций/методов основного продукта", results["functions"]),
        ("Число классов основного продукта", results["classes"]),
        ("Физические строки тестов", results["test_physical_lines"]),
        ("Функции тестов", results["test_functions"]),
        ("AVC физический", format_number(results["physical_avc"])),
        ("AVC эффективный", format_number(results["effective_avc"])),
        ("Принятое AVC", results["accepted_avc"]),
        ("LOC", results["loc"]),
        ("KDSI", format_number(results["kdsi"], 3)),
        ("M", format_number(results["multiplier_m"], 3)),
        ("PM", format_number(results["person_months"])),
        ("Трудоемкость разработки, ч", results["development_hours"]),
        ("Полная трудоемкость проекта, ч", results["total_hours"]),
        ("Стоимость персонала, руб.", results["personnel_cost"]),
        ("Полная стоимость проекта, руб.", results["total_cost"]),
    ]


def save_calculation_reports(calculation, reports_dir):
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / "economic_calculation.json"
    csv_path = reports_dir / "economic_calculation.csv"

    json_path.write_text(
        json.dumps(calculation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Показатель", "Значение"])
        writer.writerows(build_csv_rows(calculation))

    return {
        "json": json_path,
        "csv": csv_path,
    }
