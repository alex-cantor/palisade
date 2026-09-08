from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from features.announcements.views import dashboard
from features.network.views import services

urlpatterns = [
    path('admin/', admin.site.urls),
    path("organizer/", include("features.organizer.urls")),
    path("injects/", include("features.injects.urls", namespace="injects")),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", dashboard, name="dashboard"),
    path("services/", services, name="services"),
]
