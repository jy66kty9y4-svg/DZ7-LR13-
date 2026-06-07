CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

QUALITY_METRICS = {
    "processed_records_total": {
        "description": "Number of client records processed during the latest security container run.",
        "value": 0,
    },
    "allow_total": {
        "description": "Number of ALLOW decisions during the latest security container run.",
        "value": 0,
    },
    "block_total": {
        "description": "Number of BLOCK decisions during the latest security container run.",
        "value": 0,
    },
    "processing_errors_total": {
        "description": "Number of processing errors during the latest security container run.",
        "value": 0,
    },
    "response_time_seconds": {
        "description": "Security container processing time in seconds for the latest run.",
        "value": 0,
    },
    "container_up": {
        "description": "Security container availability flag: 1 when the application can serve metrics.",
        "value": 1,
    },
}


def update_quality_metrics(total_count, allow_count, block_count, errors_count, elapsed_seconds):
    QUALITY_METRICS["processed_records_total"]["value"] = total_count
    QUALITY_METRICS["allow_total"]["value"] = allow_count
    QUALITY_METRICS["block_total"]["value"] = block_count
    QUALITY_METRICS["processing_errors_total"]["value"] = errors_count
    QUALITY_METRICS["response_time_seconds"]["value"] = elapsed_seconds
    QUALITY_METRICS["container_up"]["value"] = 1


def render_metrics():
    QUALITY_METRICS["container_up"]["value"] = 1
    lines = []

    for name, metric in QUALITY_METRICS.items():
        lines.append(f"# HELP {name} {metric['description']}")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {float(metric['value'])}")

    return ("\n".join(lines) + "\n").encode("utf-8"), CONTENT_TYPE_LATEST


def get_quality_metrics():
    return {
        name: {
            "description": metric["description"],
            "value": float(metric["value"]),
        }
        for name, metric in QUALITY_METRICS.items()
    }
