from django.db import models
from features.competitions.models import Competition

# Create your models here.
class Announcement(models.Model):
  competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="announcements", null=True, blank=True)
  title = models.CharField(max_length=200)
  published_at = models.DateTimeField(auto_now_add=True)
  scheduled_for = models.DateTimeField(null=True, blank=True, help_text="Leave blank to publish immediately. If set, competitors won't see this until that time.")
  read = models.BooleanField(default=False)

  def __str__(self):
    return self.title
