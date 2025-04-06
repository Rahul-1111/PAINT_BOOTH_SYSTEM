from django.urls import path
from . import views

app_name = "booth"

urlpatterns = [
    path("", views.dashboard_form_view, name="oee_form"),
    path("fetch-data/", views.fetch_torque_data, name="fetch_torque_data"),
]
