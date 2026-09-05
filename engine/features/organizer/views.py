import json
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from features.competitions.models import Competition, MachineTemplate, CompetitionMachine, ProvisionedMachine
from features.injects.models import Inject, InjectSubmission
from features.teams.models import Team, TeamMember

from . import provisioning, scoring
from .forms import (
  CompetitionForm, MachineTemplateForm, AddMachineForm,
  ProvisionTeamsForm, AddTeamForm, AddMemberForm, EditMemberForm, ResetPasswordForm,
  AnnouncementForm, InjectForm,
)


@staff_member_required
def competition_list(request):
  competitions = Competition.objects.order_by("-start_time")
  return render(request, "organizer/competition_list.html", {"competitions": competitions})


@staff_member_required
def competition_create(request):
  if request.method == "POST":
    form = CompetitionForm(request.POST)
    if form.is_valid():
      competition = form.save()
      messages.success(request, f"Created competition '{competition.name}'.")
      return redirect("organizer:competition_detail", pk=competition.pk)
  else:
    form = CompetitionForm()
  return render(request, "organizer/competition_form.html", {"form": form})


@staff_member_required
def competition_detail(request, pk):
  competition = get_object_or_404(Competition, pk=pk)
  machines = competition.machines.select_related("machine_template")
  has_baseline = competition.provisioned_machines.exists()
  return render(request, "organizer/competition_detail.html", {
    "competition": competition,
    "machines": machines,
    "has_baseline": has_baseline,
    "provision_form": ProvisionTeamsForm(),
  })


@staff_member_required
def competition_provision_teams(request, pk):
  competition = get_object_or_404(Competition, pk=pk)
  if request.method == "POST":
    form = ProvisionTeamsForm(request.POST)
    if form.is_valid():
      teams = provisioning.provision_teams(
        competition,
        form.cleaned_data["num_teams"],
        form.cleaned_data["username_prefix"],
        form.cleaned_data["default_password"],
      )
      if competition.status == "draft":
        competition.status = "provisioning"
        competition.save()
      messages.success(request, f"Provisioned {len(teams)} team(s).")
    else:
      messages.error(request, "Could not provision teams — check the form values.")
  return redirect("organizer:competition_detail", pk=competition.pk)


@staff_member_required
def competition_provision_baseline(request, pk):
  """Phase 1: provision VMs for a single baseline team for vulnerability injection."""
  competition = get_object_or_404(Competition, pk=pk)
  if request.method == "POST":
    # TODO: call provisioning.provision_baseline(competition) when implemented
    messages.info(request, "Baseline provisioning queued — not yet wired to PVE. "
                           "VMs for the baseline team will appear here once connected.")
  return redirect("organizer:competition_machines", pk=pk)


@staff_member_required
def competition_provision_infra(request, pk):
  """Phase 2: full provision — clone baseline to all teams on their subnets."""
  competition = get_object_or_404(Competition, pk=pk)
  if request.method == "POST":
    result = provisioning.provision_infrastructure(competition)
    if result["status"] == "done":
      messages.success(request, f"Provisioned {len(result['provisioned'])} VM(s) successfully.")
    elif result["status"] == "partial":
      messages.warning(request, f"Provisioned {len(result['provisioned'])} VM(s) with {len(result['errors'])} error(s): {'; '.join(result['errors'])}")
    else:
      messages.error(request, result.get("detail") or "; ".join(result.get("errors", ["Unknown error"])))
  return redirect("organizer:competition_detail", pk=competition.pk)


@staff_member_required
def competition_go_live(request, pk):
  competition = get_object_or_404(Competition, pk=pk)
  if request.method == "POST":
    competition.status = "live"
    competition.is_active = True
    competition.save()
    messages.success(request, f"{competition.name} is now live.")
  return redirect("organizer:competition_detail", pk=competition.pk)

@staff_member_required
def competition_machines(request, pk):
  competition = get_object_or_404(Competition, pk=pk)
  assigned = competition.machines.select_related("machine_template")
  provisioned = competition.provisioned_machines.select_related("machine_template", "team")
  available = MachineTemplate.objects.exclude(
    id__in=assigned.values_list("machine_template_id", flat=True)
  )
  add_form = AddMachineForm()
  add_form.fields["template"].queryset = MachineTemplate.objects.all()
  return render(request, "organizer/competition_machines.html", {
    "competition": competition,
    "assigned": assigned,
    "provisioned": provisioned,
    "add_form": add_form,
  })


@staff_member_required
def competition_machine_add(request, pk):
  competition = get_object_or_404(Competition, pk=pk)
  if request.method == "POST":
    form = AddMachineForm(request.POST)
    if form.is_valid():
      template = form.cleaned_data["template"]
      quantity = form.cleaned_data["quantity"]
      obj, created = CompetitionMachine.objects.get_or_create(
        competition=competition,
        machine_template=template,
        defaults={"quantity": quantity},
      )
      if not created:
        obj.quantity = quantity
        obj.save()
      messages.success(request, f"Added {quantity}x {template.name}.")
    else:
      messages.error(request, "Invalid machine selection.")
  return redirect("organizer:competition_machines", pk=pk)


@staff_member_required
def competition_machine_remove(request, pk, cm_pk):
  competition = get_object_or_404(Competition, pk=pk)
  cm = get_object_or_404(CompetitionMachine, pk=cm_pk, competition=competition)
  if request.method == "POST":
    name = cm.machine_template.name
    cm.delete()
    messages.success(request, f"Removed {name} from this competition.")
  return redirect("organizer:competition_machines", pk=pk)


@staff_member_required
def competition_machine_browser(request, pk, vm_pk):
  """Placeholder — will open Guacamole or similar remote console."""
  messages.info(request, "Browser-based VM console not yet connected. "
                         "This will open a Guacamole session when implemented.")
  return redirect("organizer:competition_machines", pk=pk)

@staff_member_required
def competition_announcements(request, pk):
  competition = get_object_or_404(Competition, pk=pk)
  if request.method == "POST":
    form = AnnouncementForm(request.POST)
    if form.is_valid():
      announcement = form.save(commit=False)
      announcement.competition = competition
      announcement.read = False
      announcement.save()
      if announcement.scheduled_for:
        messages.success(request, f"Announcement scheduled for {announcement.scheduled_for}.")
      else:
        messages.success(request, "Announcement posted.")
      return redirect("organizer:competition_announcements", pk=competition.pk)
  else:
    form = AnnouncementForm()

  announcements = competition.announcements.order_by("-published_at")
  return render(request, "organizer/announcements.html", {
    "competition": competition,
    "announcements": announcements,
    "form": form,
  })

def _load_inject_library():
  path = os.path.join(settings.BASE_DIR, "..", "injects", "injects.json")
  path = os.path.normpath(path)
  try:
    with open(path, encoding="utf-8") as f:
      return json.load(f)
  except (FileNotFoundError, json.JSONDecodeError):
    return []


@staff_member_required
def competition_injects(request, pk):
  competition = get_object_or_404(Competition, pk=pk)

  if request.method == "POST":
    form = InjectForm(request.POST)
    if form.is_valid():
      inject = form.save(commit=False)
      inject.competition = competition
      inject.save()
      messages.success(request, "Inject created.")
      return redirect("organizer:competition_injects", pk=competition.pk)
  else:
    form = InjectForm()

  teams = list(competition.teams.order_by("name"))
  injects = list(competition.injects.order_by("start_time"))

  submitted_pairs = set(
    InjectSubmission.objects.filter(
      inject__in=injects, team__in=teams, submitted_at__isnull=False,
    ).values_list("inject_id", "team_id")
  )

  rows = []
  for inject in injects:
    rows.append({
      "inject": inject,
      "cells": [(inject.id, team.id) in submitted_pairs for team in teams],
    })

  library = _load_inject_library()
  categories = sorted({item["category"] for item in library})

  return render(request, "organizer/injects.html", {
    "competition": competition,
    "form": form,
    "teams": teams,
    "rows": rows,
    "library": json.dumps(library),
    "categories": categories,
  })


@staff_member_required
def inject_delete(request, pk, inject_pk):
  competition = get_object_or_404(Competition, pk=pk)
  inject = get_object_or_404(Inject, pk=inject_pk, competition=competition)
  if request.method == "POST":
    inject.delete()
    messages.success(request, f"Deleted inject '{inject.title}'.")
  return redirect("organizer:competition_injects", pk=pk)

@staff_member_required
def competition_scoreboard(request, pk):
  competition = get_object_or_404(Competition, pk=pk)
  rows = scoring.compute_scoreboard(competition)
  return render(request, "organizer/scoreboard.html", {
    "competition": competition,
    "rows": rows,
  })

@staff_member_required
def template_list(request):
  templates = MachineTemplate.objects.order_by("os_family", "name")
  return render(request, "organizer/template_list.html", {"templates": templates})


@staff_member_required
def template_create(request):
  if request.method == "POST":
    form = MachineTemplateForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, "Template created.")
      return redirect("organizer:template_list")
  else:
    form = MachineTemplateForm()
  return render(request, "organizer/template_form.html", {"form": form, "editing": False})


@staff_member_required
def template_edit(request, pk):
  template = get_object_or_404(MachineTemplate, pk=pk)
  if request.method == "POST":
    form = MachineTemplateForm(request.POST, instance=template)
    if form.is_valid():
      form.save()
      messages.success(request, "Template updated.")
      return redirect("organizer:template_list")
  else:
    form = MachineTemplateForm(instance=template)
  return render(request, "organizer/template_form.html", {"form": form, "editing": True, "template": template})


@staff_member_required
def template_delete(request, pk):
  template = get_object_or_404(MachineTemplate, pk=pk)
  if request.method == "POST":
    template.delete()
    messages.success(request, f"Deleted template '{template.name}'.")
  return redirect("organizer:template_list")

@staff_member_required
def competition_teams(request, pk):
  competition = get_object_or_404(Competition, pk=pk)
  teams = competition.teams.prefetch_related("members__user").order_by("name")
  return render(request, "organizer/competition_teams.html", {
    "competition": competition,
    "teams": teams,
    "add_team_form": AddTeamForm(),
    "add_member_form": AddMemberForm(competition=competition),
  })


@staff_member_required
def team_create(request, pk):
  competition = get_object_or_404(Competition, pk=pk)
  if request.method == "POST":
    form = AddTeamForm(request.POST)
    if form.is_valid():
      Team.objects.create(competition=competition, name=form.cleaned_data["name"])
      messages.success(request, f"Created team '{form.cleaned_data['name']}'.")
    else:
      messages.error(request, "Invalid team name.")
  return redirect("organizer:competition_teams", pk=pk)


@staff_member_required
def team_delete(request, pk, team_pk):
  competition = get_object_or_404(Competition, pk=pk)
  team = get_object_or_404(Team, pk=team_pk, competition=competition)
  if request.method == "POST":
    # Delete all member user accounts, then the team
    for member in team.members.select_related("user"):
      member.user.delete()
    team.delete()
    messages.success(request, f"Deleted team '{team.name}' and all member accounts.")
  return redirect("organizer:competition_teams", pk=pk)


@staff_member_required
def member_add(request, pk):
  competition = get_object_or_404(Competition, pk=pk)
  if request.method == "POST":
    form = AddMemberForm(request.POST, competition=competition)
    if form.is_valid():
      team      = form.cleaned_data["team"]
      username  = form.cleaned_data["username"]
      full_name = form.cleaned_data["full_name"]
      password  = form.cleaned_data["password"]
      first, _, last = full_name.partition(" ")
      if User.objects.filter(username=username).exists():
        messages.error(request, f"Username '{username}' is already taken.")
      else:
        user = User.objects.create_user(
          username=username, password=password,
          first_name=first, last_name=last,
        )
        TeamMember.objects.create(user=user, team=team)
        messages.success(request, f"Added {full_name} to {team.name}.")
    else:
      messages.error(request, "Check all fields.")
  return redirect("organizer:competition_teams", pk=pk)


@staff_member_required
def member_edit(request, pk, member_pk):
  competition = get_object_or_404(Competition, pk=pk)
  member = get_object_or_404(TeamMember, pk=member_pk, team__competition=competition)
  if request.method == "POST":
    form = EditMemberForm(request.POST)
    if form.is_valid():
      new_username  = form.cleaned_data["username"]
      new_full_name = form.cleaned_data["full_name"]
      if new_username != member.user.username and User.objects.filter(username=new_username).exists():
        messages.error(request, f"Username '{new_username}' is already taken.")
      else:
        first, _, last = new_full_name.partition(" ")
        member.user.username   = new_username
        member.user.first_name = first
        member.user.last_name  = last
        member.user.save(update_fields=["username", "first_name", "last_name"])
        messages.success(request, f"Updated {new_full_name}.")
    else:
      messages.error(request, "Invalid form.")
  return redirect("organizer:competition_teams", pk=pk)


@staff_member_required
def member_reset_password(request, pk, member_pk):
  competition = get_object_or_404(Competition, pk=pk)
  member = get_object_or_404(TeamMember, pk=member_pk, team__competition=competition)
  if request.method == "POST":
    form = ResetPasswordForm(request.POST)
    if form.is_valid():
      member.user.set_password(form.cleaned_data["new_password"])
      member.user.save(update_fields=["password"])
      messages.success(request, f"Password reset for {member.user.get_full_name() or member.user.username}.")
    else:
      messages.error(request, "Invalid password.")
  return redirect("organizer:competition_teams", pk=pk)


@staff_member_required
def member_delete(request, pk, member_pk):
  competition = get_object_or_404(Competition, pk=pk)
  member = get_object_or_404(TeamMember, pk=member_pk, team__competition=competition)
  if request.method == "POST":
    name = member.user.get_full_name() or member.user.username
    member.user.delete()
    messages.success(request, f"Removed {name}.")
  return redirect("organizer:competition_teams", pk=pk)
