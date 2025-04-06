from django.urls import path
from . import views

app_name = "booth"

urlpatterns = [
    path("", views.dashboard_form_view, name="oee_form"),
    path("fetch-data/", views.fetch_torque_data, name="fetch_torque_data"),
    path("edit/<int:pk>/", views.edit_oee_record, name="edit_oee_record"),
    path("get-part-numbers/", views.get_part_numbers, name="get_part_numbers"),
    path("manual-entry/", views.manual_entry_view, name="manual_entry"),
]
