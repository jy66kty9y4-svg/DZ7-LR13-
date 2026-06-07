from pathlib import Path

import pytest

from security_channel.services import security_container as security_module
from security_channel.services.metrics import render_metrics


@pytest.fixture(autouse=True)
def configure_access_key(monkeypatch):
    monkeypatch.setenv("ACCESS_KEY", "test-secret-key")
    security_module.ACCESS_KEY = "test-secret-key"


def make_client(token="test-secret-key", client_id="client-001"):
    return {
        "client_id": client_id,
        "ip": "192.168.10.15",
        "channel": "VPN-01",
        "token": token,
        "requests": 12,
        "payload": 2048,
        "timestamp": 1710000000,
    }


def test_security_container_returns_result_list(tmp_path):
    result = security_module.security_container([make_client()], output_dir=tmp_path)

    assert isinstance(result["results"], list)
    assert len(result["results"]) == 1
    assert result["total_count"] == 1


def test_correct_token_gets_allow_and_auth_ok(tmp_path):
    result = security_module.security_container([make_client()], output_dir=tmp_path)
    row = result["results"][0]

    assert row["status"] == "ALLOW"
    assert row["reason"] == "AUTH_OK"
    assert result["allow_count"] == 1
    assert result["block_count"] == 0


def test_access_key_marker_gets_allow_and_auth_ok(tmp_path):
    result = security_module.security_container([make_client(token="ACCESS_KEY")], output_dir=tmp_path)
    row = result["results"][0]

    assert row["status"] == "ALLOW"
    assert row["reason"] == "AUTH_OK"


def test_wrong_token_gets_block_and_auth_error(tmp_path):
    result = security_module.security_container([make_client(token="wrong-token")], output_dir=tmp_path)
    row = result["results"][0]

    assert row["status"] == "BLOCK"
    assert row["reason"] == "AUTH_ERROR"
    assert result["allow_count"] == 0
    assert result["block_count"] == 1


def test_missing_token_gets_block_and_auth_error(tmp_path):
    client = make_client()
    client.pop("token")

    result = security_module.security_container([client], output_dir=tmp_path)
    row = result["results"][0]

    assert row["status"] == "BLOCK"
    assert row["reason"] == "AUTH_ERROR"


def test_multiple_records_keep_input_count(tmp_path):
    data = [
        make_client(token="test-secret-key", client_id="client-allow"),
        make_client(token="wrong-token", client_id="client-block"),
    ]

    result = security_module.security_container(data, output_dir=tmp_path)

    assert result["total_count"] == 2
    assert len(result["results"]) == 2
    assert result["allow_count"] == 1
    assert result["block_count"] == 1


def test_empty_dataset_returns_empty_result_without_files(tmp_path):
    result = security_module.security_container([], output_dir=tmp_path)

    assert result["results"] == []
    assert result["total_count"] == 0
    assert result["allow_count"] == 0
    assert result["block_count"] == 0
    assert result["csv_file"] is None
    assert result["charts"] == {}


def test_csv_file_is_created(tmp_path):
    result = security_module.security_container([make_client()], output_dir=tmp_path)

    csv_path = Path(result["csv_file"])
    assert csv_path.exists()
    assert csv_path.name == "1results.csv"
    assert csv_path.stat().st_size > 0


def test_chart_files_are_created(tmp_path):
    result = security_module.security_container([make_client()], output_dir=tmp_path)

    expected_chart_names = {
        "1security_chart.png",
        "1requests_over_time.png",
        "1channel_load_chart.png",
    }
    actual_chart_paths = [Path(path) for path in result["charts"].values()]

    assert {path.name for path in actual_chart_paths} == expected_chart_names
    assert all(path.exists() for path in actual_chart_paths)
    assert all(path.stat().st_size > 0 for path in actual_chart_paths)


def test_quality_metrics_are_updated_after_processing(tmp_path):
    security_module.security_container(
        [
            make_client(token="test-secret-key", client_id="client-allow"),
            make_client(token="wrong-token", client_id="client-block"),
        ],
        output_dir=tmp_path,
    )

    payload, content_type = render_metrics()
    metrics_text = payload.decode("utf-8")

    assert "text/plain" in content_type
    assert "processed_records_total 2.0" in metrics_text
    assert "allow_total 1.0" in metrics_text
    assert "block_total 1.0" in metrics_text
    assert "processing_errors_total 0.0" in metrics_text
    assert "container_up 1.0" in metrics_text
