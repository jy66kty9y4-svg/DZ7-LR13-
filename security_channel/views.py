import json
from pathlib import Path

from django.http import HttpResponse
from django.shortcuts import render, redirect

from .services.security_container import security_container
from .services.metrics import render_metrics


def get_app_dir():
    return Path(__file__).resolve().parent


def get_clients_path():
    return get_app_dir() / "data" / "clients.json"


def load_clients():
    data_path = get_clients_path()

    with open(data_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_clients(clients):
    data_path = get_clients_path()

    with open(data_path, "w", encoding="utf-8") as file:
        json.dump(clients, file, ensure_ascii=False, indent=2)


def index(request):
    app_dir = get_app_dir()
    output_dir = app_dir / "static" / "security_channel" / "generated"

    clients = load_clients()
    container_result = security_container(clients, output_dir=output_dir)

    context = {
        "results": container_result["results"],
        "allow_count": container_result["allow_count"],
        "block_count": container_result["block_count"],
        "total_count": container_result["total_count"],
        "security_chart_url": "security_channel/generated/1security_chart.png",
        "requests_chart_url": "security_channel/generated/1requests_over_time.png",
        "channel_chart_url": "security_channel/generated/1channel_load_chart.png",
    }

    return render(request, "security_channel/index.html", context)


def metrics(request):
    payload, content_type = render_metrics()
    return HttpResponse(payload, content_type=content_type)


def metrics_view(request):
    payload, _ = render_metrics()
    return render(
        request,
        "security_channel/metrics_view.html",
        {"metrics_text": payload.decode("utf-8")},
    )


def quality_dashboard(request):
    return redirect("http://127.0.0.1:3000/d/security-channel-quality/kachestvo-kontejnera-bezopasnosti")


def clients_page(request):
    clients = load_clients()

    indexed_clients = []
    for index, client in enumerate(clients):
        indexed_clients.append({
            "index": index,
            "client": client,
        })

    context = {
        "indexed_clients": indexed_clients,
        "clients_count": len(clients),
    }

    return render(request, "security_channel/clients.html", context)


def edit_client(request, client_index):
    clients = load_clients()

    if client_index < 0 or client_index >= len(clients):
        return redirect("security_channel_clients")

    client = clients[client_index]

    if request.method == "POST":
        client["client_id"] = request.POST.get("client_id", "").strip()
        client["ip"] = request.POST.get("ip", "").strip()
        client["channel"] = request.POST.get("channel", "").strip()
        client["token"] = request.POST.get("token", "").strip()

        try:
            client["requests"] = int(request.POST.get("requests", 0))
        except ValueError:
            client["requests"] = 0

        try:
            client["payload"] = int(request.POST.get("payload", 0))
        except ValueError:
            client["payload"] = 0

        try:
            client["timestamp"] = int(request.POST.get("timestamp", 0))
        except ValueError:
            client["timestamp"] = 0

        clients[client_index] = client
        save_clients(clients)

        return redirect("security_channel_clients")

    context = {
        "client": client,
        "client_index": client_index,
    }

    return render(request, "security_channel/edit_client.html", context)
