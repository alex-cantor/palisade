from django.db import models
from features.competitions.models import Competition, MachineTemplate
from features.teams.models import Team


class ServiceDefinition(models.Model):
    PROTOCOL_CHOICES = [("tcp", "TCP"), ("udp", "UDP")]

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="service_definitions")
    name = models.CharField(max_length=100)
    port = models.PositiveIntegerField()
    protocol = models.CharField(max_length=3, choices=PROTOCOL_CHOICES, default="tcp")
    machine_template = models.ForeignKey(
        MachineTemplate, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Which VM type hosts this service. Leave blank to check all team VMs.",
    )
    points_per_check = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.name} :{self.port}/{self.protocol} ({self.competition.name})"


class ServiceCheck(models.Model):
    service = models.ForeignKey(ServiceDefinition, on_delete=models.CASCADE, related_name="checks")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="service_checks")
    checked_at = models.DateTimeField(auto_now_add=True)
    is_up = models.BooleanField()

    class Meta:
        indexes = [models.Index(fields=["service", "team", "checked_at"])]

    def __str__(self):
        return f"{self.service.name} — {self.team.name} — {'UP' if self.is_up else 'DOWN'}"
