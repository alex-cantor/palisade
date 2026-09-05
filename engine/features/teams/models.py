from django.db import models
from django.contrib.auth.models import User
from features.competitions.models import Competition


class Team(models.Model):
  competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="teams")
  name = models.CharField(max_length=50)

  def __str__(self):
    return f"{self.name} ({self.competition.name})"


class TeamMember(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="team_membership")
  team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")

  def __str__(self):
    return f"{self.user.username} — {self.team.name}"
