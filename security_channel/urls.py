from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="security_channel_index"),
    path("clients/", views.clients_page, name="security_channel_clients"),
    path("clients/<int:client_index>/edit/", views.edit_client, name="security_channel_edit_client"),
]