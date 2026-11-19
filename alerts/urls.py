from django.urls import path

from . import views

urlpatterns = [
    path("", views.alert_list, name="alert_list"),
    path("alerts/new/", views.alert_edit, name="alert_create"),
    path("alerts/<int:pk>/edit/", views.alert_edit, name="alert_update"),
    path("alerts/<int:pk>/delete/", views.alert_delete, name="alert_delete"),
]
