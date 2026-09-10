from django.contrib import admin
from .models import ServiceDefinition, ServiceCheck


@admin.register(ServiceDefinition)
class ServiceDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "port", "protocol", "machine_template", "points_per_check", "competition")
    list_filter = ("competition", "protocol")


@admin.register(ServiceCheck)
class ServiceCheckAdmin(admin.ModelAdmin):
    list_display = ("service", "team", "is_up", "checked_at")
    list_filter = ("service__competition", "service", "is_up")
    ordering = ("-checked_at",)
