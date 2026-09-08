from django.urls import path
from . import views

app_name = "injects"

urlpatterns = [
    path("", views.inject_list, name="inject_list"),
    path("<int:inject_pk>/submit/", views.inject_submit, name="inject_submit"),
]
