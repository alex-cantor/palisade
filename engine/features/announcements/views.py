from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Announcement
from features.injects.models import Inject, InjectSubmission
from features.teams.models import TeamMember


@login_required
def dashboard(request):
  if request.user.is_staff:
    return redirect("organizer:competition_list")

  try:
    membership = request.user.team_membership
    team = membership.team
  except TeamMember.DoesNotExist:
    return render(request, "waiting.html")

  now = timezone.now()
  announcements = Announcement.objects.filter(
    Q(scheduled_for__isnull=True) | Q(scheduled_for__lte=now)
  ).order_by("-published_at")[:5]

  injects = list(Inject.objects.order_by("start_time"))
  submitted_ids = set(
    InjectSubmission.objects.filter(
      team=team, submitted_at__isnull=False
    ).values_list("inject_id", flat=True)
  )
  for inject in injects:
    inject.is_submitted = inject.id in submitted_ids

  return render(request, "dashboard.html", {
    "team": team,
    "member": membership,
    "announcements": announcements,
    "injects": injects,
  })
