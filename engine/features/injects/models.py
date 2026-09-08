from django.db import models
from features.teams.models import Team
from features.competitions.models import Competition

# Create your models here.
class Inject(models.Model):
  competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="injects", null=True, blank=True)
  title = models.CharField(max_length=200)
  description = models.TextField(blank=True)
  start_time = models.DateTimeField()
  due_time = models.DateTimeField()
  points = models.IntegerField()

  def __str__(self):
    return self.title

class InjectSubmission(models.Model):
  inject = models.ForeignKey(Inject, on_delete=models.CASCADE, related_name="submissions")
  team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="inject_submissions")
  submitted_at = models.DateTimeField(null=True, blank=True)
  content = models.TextField(blank=True)
  graded_points = models.IntegerField(null=True, blank=True)
  graded_at = models.DateTimeField(null=True, blank=True)
  graded_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
  feedback = models.TextField(blank=True)

  class Meta:
    unique_together = ("inject", "team")
