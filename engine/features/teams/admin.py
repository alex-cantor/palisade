from django.contrib import admin
from .models import Team, TeamMember


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
  list_display = ("name", "competition", "member_count")
  list_filter = ("competition",)
  search_fields = ("name",)

  def member_count(self, obj):
    return obj.members.count()
  member_count.short_description = "Members"


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
  list_display = ("user", "team", "competition")
  list_filter = ("team__competition",)
  search_fields = ("user__username", "user__first_name", "user__last_name", "team__name")

  def competition(self, obj):
    return obj.team.competition
  competition.short_description = "Competition"
