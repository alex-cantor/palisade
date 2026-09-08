from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from features.injects.models import Inject, InjectSubmission
from features.teams.models import TeamMember


@login_required
def inject_list(request):
    try:
        member = TeamMember.objects.select_related("team__competition").get(user=request.user)
    except TeamMember.DoesNotExist:
        return redirect("dashboard")

    competition = member.team.competition
    if not competition:
        return redirect("dashboard")

    injects = list(competition.injects.order_by("start_time"))
    submissions = {
        s.inject_id: s
        for s in InjectSubmission.objects.filter(team=member.team, inject__in=injects)
    }
    now = timezone.now()
    rows = []
    for inject in injects:
        rows.append({
            "inject": inject,
            "submission": submissions.get(inject.id),
            "open": inject.start_time <= now,
            "overdue": now > inject.due_time,
        })

    return render(request, "competitor/injects.html", {
        "team": member.team,
        "competition": competition,
        "rows": rows,
    })


@login_required
def inject_submit(request, inject_pk):
    try:
        member = TeamMember.objects.select_related("team__competition").get(user=request.user)
    except TeamMember.DoesNotExist:
        return redirect("dashboard")

    inject = get_object_or_404(Inject, pk=inject_pk, competition=member.team.competition)

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            submission, _ = InjectSubmission.objects.get_or_create(
                inject=inject, team=member.team
            )
            submission.content = content
            submission.submitted_at = timezone.now()
            submission.save()

    return redirect("injects:inject_list")
