from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import ServiceDefinition, ServiceCheck
from features.competitions.models import Competition


@login_required
def services(request):
    competition = Competition.objects.filter(is_active=True).first()
    if not competition:
        return render(request, "services.html", {"service_types": [], "grid": []})

    service_defs = list(ServiceDefinition.objects.filter(competition=competition))
    teams = list(competition.teams.order_by("name"))

    # Most recent check result per (service, team)
    recent_map = {}
    for chk in ServiceCheck.objects.filter(
        service__competition=competition
    ).order_by("service_id", "team_id", "-checked_at").values("service_id", "team_id", "is_up"):
        key = (chk["service_id"], chk["team_id"])
        if key not in recent_map:
            recent_map[key] = chk["is_up"]

    grid = [
        {
            "team": team.name,
            "statuses": [recent_map.get((svc.id, team.id)) for svc in service_defs],
        }
        for team in teams
    ]

    return render(request, "services.html", {
        "service_types": [svc.name for svc in service_defs],
        "grid": grid,
    })
