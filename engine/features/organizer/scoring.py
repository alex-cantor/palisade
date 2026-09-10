from django.db.models import Sum
from features.injects.models import InjectSubmission
from features.network.models import ServiceDefinition, ServiceCheck


def compute_scoreboard(competition):
    teams = list(competition.teams.order_by("name"))

    inject_scores = {
        row["team_id"]: row["total"]
        for row in InjectSubmission.objects.filter(
            inject__competition=competition,
            graded_points__isnull=False,
        ).values("team_id").annotate(total=Sum("graded_points"))
    }

    service_scores = {
        row["team_id"]: row["points"]
        for row in ServiceCheck.objects.filter(
            service__competition=competition,
            is_up=True,
        ).values("team_id").annotate(points=Sum("service__points_per_check"))
    }

    service_defs = list(ServiceDefinition.objects.filter(competition=competition))

    # Most recent check result per (service, team)
    recent_map = {}
    for chk in ServiceCheck.objects.filter(
        service__competition=competition
    ).order_by("service_id", "team_id", "-checked_at").values("service_id", "team_id", "is_up"):
        key = (chk["service_id"], chk["team_id"])
        if key not in recent_map:
            recent_map[key] = chk["is_up"]

    rows = []
    for team in teams:
        inject_pts = inject_scores.get(team.id, 0)
        service_pts = service_scores.get(team.id, 0)
        rows.append({
            "team": team,
            "inject_score": inject_pts,
            "service_score": service_pts,
            "score": inject_pts + service_pts,
            "service_statuses": [
                {"name": svc.name, "port": svc.port, "last_up": recent_map.get((svc.id, team.id))}
                for svc in service_defs
            ],
        })

    rows.sort(key=lambda r: r["score"], reverse=True)
    for i, row in enumerate(rows):
        row["rank"] = i + 1

    return rows, service_defs
