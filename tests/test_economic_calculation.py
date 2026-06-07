import csv
import json
import math

from security_channel.economic_calculation import build_calculation
from security_channel.economic_calculation import save_calculation_reports


def test_loc_is_functions_multiplied_by_accepted_avc():
    calculation = build_calculation(".")
    results = calculation["results"]

    assert results["loc"] == results["functions"] * results["accepted_avc"]


def test_kdsi_is_loc_divided_by_thousand():
    calculation = build_calculation(".")
    results = calculation["results"]

    assert results["kdsi"] == results["loc"] / 1000


def test_multiplier_m_is_product_of_cocomo_factors():
    calculation = build_calculation(".")
    coefficients = calculation["coefficients"]
    results = calculation["results"]
    expected = (
        coefficients["RELY"]
        * coefficients["RCPX"]
        * coefficients["RUSE"]
        * coefficients["PDIF"]
        * coefficients["PREX"]
        * coefficients["FCIL"]
        * coefficients["SCED"]
    )

    assert math.isclose(results["multiplier_m"], expected)


def test_pm_uses_cocomo_formula():
    calculation = build_calculation(".")
    results = calculation["results"]

    expected = 2.4 * (results["kdsi"] ** 1.05) * results["multiplier_m"]

    assert math.isclose(results["person_months"], expected)


def test_total_hours_include_development_and_additional_hours():
    calculation = build_calculation(".")
    results = calculation["results"]
    work_hours = calculation["work_hours"]

    assert results["total_hours"] == results["development_hours"] + work_hours["additional_hours"]


def test_total_cost_includes_personnel_and_project_cost_blocks():
    calculation = build_calculation(".")
    results = calculation["results"]
    costs = calculation["costs"]

    expected = (
        results["personnel_cost"]
        + costs["platform_cost"]
        + costs["maintenance_cost"]
        + costs["training_cost"]
    )

    assert results["total_cost"] == expected


def test_json_report_is_created(tmp_path):
    calculation = build_calculation(".")
    paths = save_calculation_reports(calculation, tmp_path)

    assert paths["json"].exists()
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["results"]["loc"] == calculation["results"]["loc"]


def test_csv_report_is_created(tmp_path):
    calculation = build_calculation(".")
    paths = save_calculation_reports(calculation, tmp_path)

    assert paths["csv"].exists()
    with paths["csv"].open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file, delimiter=";"))

    assert rows[0] == ["Показатель", "Значение"]
    assert ["LOC", str(calculation["results"]["loc"])] in rows
