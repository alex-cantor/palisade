from features.injects.models import InjectSubmission


def compute_scoreboard(competition):
  teams = list(competition.teams.order_by("name"))

  graded = InjectSubmission.objects.filter(
    inject__competition=competition,
    graded_points__isnull=False,
  ).values("team_id", "graded_points")

  scores = {}
  for row in graded:
    scores[row["team_id"]] = scores.get(row["team_id"], 0) + row["graded_points"]

  rows = [{"team": t, "score": scores.get(t.id, 0)} for t in teams]
  rows.sort(key=lambda r: r["score"], reverse=True)

  for i, row in enumerate(rows):
    row["rank"] = i + 1

  return rows
