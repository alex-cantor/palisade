from django.urls import path
from . import views

app_name = "organizer"

urlpatterns = [
  # Competition list + create
  path("", views.competition_list, name="competition_list"),
  path("new/", views.competition_create, name="competition_create"),

  # Machine templates
  path("templates/", views.template_list, name="template_list"),
  path("templates/new/", views.template_create, name="template_create"),
  path("templates/<int:pk>/edit/", views.template_edit, name="template_edit"),
  path("templates/<int:pk>/delete/", views.template_delete, name="template_delete"),

  # Competition detail + provisioning
  path("<int:pk>/", views.competition_detail, name="competition_detail"),
  path("<int:pk>/provision-teams/", views.competition_provision_teams, name="competition_provision_teams"),
  path("<int:pk>/provision-baseline/", views.competition_provision_baseline, name="competition_provision_baseline"),
  path("<int:pk>/provision-infra/", views.competition_provision_infra, name="competition_provision_infra"),
  path("<int:pk>/go-live/", views.competition_go_live, name="competition_go_live"),

  # Machine management
  path("<int:pk>/machines/", views.competition_machines, name="competition_machines"),
  path("<int:pk>/machines/add/", views.competition_machine_add, name="competition_machine_add"),
  path("<int:pk>/machines/<int:cm_pk>/remove/", views.competition_machine_remove, name="competition_machine_remove"),
  path("<int:pk>/machines/vm/<int:vm_pk>/browser/", views.competition_machine_browser, name="competition_machine_browser"),

  # Teams
  path("<int:pk>/teams/", views.competition_teams, name="competition_teams"),
  path("<int:pk>/teams/create/", views.team_create, name="team_create"),
  path("<int:pk>/teams/<int:team_pk>/delete/", views.team_delete, name="team_delete"),
  # Members
  path("<int:pk>/members/add/", views.member_add, name="member_add"),
  path("<int:pk>/members/<int:member_pk>/edit/", views.member_edit, name="member_edit"),
  path("<int:pk>/members/<int:member_pk>/reset-password/", views.member_reset_password, name="member_reset_password"),
  path("<int:pk>/members/<int:member_pk>/delete/", views.member_delete, name="member_delete"),

  # Announcements + injects + scoreboard
  path("<int:pk>/announcements/", views.competition_announcements, name="competition_announcements"),
  path("<int:pk>/injects/", views.competition_injects, name="competition_injects"),
  path("<int:pk>/injects/<int:inject_pk>/delete/", views.inject_delete, name="inject_delete"),
  path("<int:pk>/scoreboard/", views.competition_scoreboard, name="competition_scoreboard"),
]
