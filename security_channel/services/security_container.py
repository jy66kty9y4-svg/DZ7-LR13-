import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lr11_matplotlib"))

import matplotlib
matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt

from .metrics import update_quality_metrics


ACCESS_KEY = os.getenv("ACCESS_KEY", "")


def security_container(data, output_dir=None):
    started_at = time.perf_counter()
    results = []
    errors_count = 0

    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    for client in data:
        client_token = client.get("token", "")
        requests_count = client.get("requests", 0)
        payload = client.get("payload", 0)
        timestamp = client.get("timestamp", 0)

        try:
            timestamp = int(timestamp)
            readable_time = time.localtime(timestamp)
        except (TypeError, ValueError, OSError, OverflowError):
            errors_count += 1
            timestamp = 0
            readable_time = time.localtime(timestamp)

        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", readable_time)

        if client_token == "ACCESS_KEY":
            client_token = ACCESS_KEY

        if client_token != ACCESS_KEY:
            status = "BLOCK"
            reason = "AUTH_ERROR"
        else:
            status = "ALLOW"
            reason = "AUTH_OK"

        result = {
            "client_id": client.get("client_id"),
            "ip": client.get("ip"),
            "channel": client.get("channel"),
            "requests": requests_count,
            "payload": payload,
            "status": status,
            "reason": reason,
            "timestamp": formatted_time,
            "timestamp_raw": timestamp,
        }

        results.append(result)

    df = pd.DataFrame(results)

    if df.empty:
        update_quality_metrics(
            total_count=0,
            allow_count=0,
            block_count=0,
            errors_count=errors_count,
            elapsed_seconds=time.perf_counter() - started_at,
        )
        return {
            "results": [],
            "allow_count": 0,
            "block_count": 0,
            "total_count": 0,
            "csv_file": None,
            "charts": {}
        }

    df = df.sort_values(by="timestamp_raw").reset_index(drop=True)

    df_for_csv = df.drop(columns=["timestamp_raw"])
    csv_path = output_dir / "1results.csv"
    df_for_csv.to_csv(csv_path, index=False, encoding="utf-8-sig")

    df["time_str"] = df["timestamp_raw"].apply(
        lambda x: datetime.fromtimestamp(x).strftime("%d.%m %H:%M")
    )

    status_counts = df["status"].value_counts()

    security_chart_path = output_dir / "1security_chart.png"
    fig1, ax1 = plt.subplots()
    ax1.pie(status_counts.values, labels=status_counts.index, autopct="%1.1f%%")
    ax1.set_title("Распределение решений контейнера")
    fig1.savefig(security_chart_path)
    plt.close(fig1)

    requests_chart_path = output_dir / "1requests_over_time.png"
    fig2, ax2 = plt.subplots()
    ax2.plot(df["time_str"], df["requests"], marker="o")
    ax2.set_title("Количество запросов клиентов по времени")
    ax2.set_xlabel("Дата и время")
    ax2.set_ylabel("Число запросов")
    plt.xticks(rotation=45, ha="right")
    fig2.tight_layout()
    fig2.savefig(requests_chart_path)
    plt.close(fig2)

    channel_chart_path = output_dir / "1channel_load_chart.png"
    channel_requests = (
        df.groupby("channel")["requests"].sum().sort_values(ascending=False)
    )

    fig3, ax3 = plt.subplots()
    ax3.bar(channel_requests.index, channel_requests.values)
    ax3.set_title("Суммарная нагрузка по виртуальным каналам")
    ax3.set_xlabel("Канал")
    ax3.set_ylabel("Сумма запросов")
    fig3.tight_layout()
    fig3.savefig(channel_chart_path)
    plt.close(fig3)

    results_for_site = df_for_csv.to_dict("records")
    allow_count = int((df["status"] == "ALLOW").sum())
    block_count = int((df["status"] == "BLOCK").sum())
    total_count = int(len(df))

    update_quality_metrics(
        total_count=total_count,
        allow_count=allow_count,
        block_count=block_count,
        errors_count=errors_count,
        elapsed_seconds=time.perf_counter() - started_at,
    )

    return {
        "results": results_for_site,
        "allow_count": allow_count,
        "block_count": block_count,
        "total_count": total_count,
        "csv_file": str(csv_path),
        "charts": {
            "security_chart": str(security_chart_path),
            "requests_over_time": str(requests_chart_path),
            "channel_load_chart": str(channel_chart_path),
        }
    }
