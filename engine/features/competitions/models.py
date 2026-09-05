from django.db import models

DIFFICULTY_CHOICES = [
  ("beginner", "Beginner"),
  ("intermediate", "Intermediate"),
  ("advanced", "Advanced"),
]

INDUSTRY_CHOICES = [
  ("finance", "Finance"),
  ("healthcare", "Healthcare"),
  ("retail", "Retail"),
  ("government", "Government"),
  ("energy", "Energy"),
  ("education", "Education"),
  ("technology", "Technology"),
  ("other", "Other"),
]

GENERATION_MODE_CHOICES = [
  ("random", "Random"),
  ("precise", "Precise"),
]

STATUS_CHOICES = [
  ("draft", "Draft"),
  ("provisioning", "Provisioning"),
  ("live", "Live"),
  ("completed", "Completed"),
]

# Create your models here.
class Competition(models.Model):
  name = models.CharField(max_length=100)
  start_time = models.DateTimeField()
  end_time = models.DateTimeField()
  is_active = models.BooleanField(default=False)
  scoring_interval_minutes = models.IntegerField(default=10)

  difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="beginner")
  industry = models.CharField(max_length=20, choices=INDUSTRY_CHOICES, default="other")
  generation_mode = models.CharField(max_length=10, choices=GENERATION_MODE_CHOICES, default="random")
  random_machine_count = models.PositiveIntegerField(default=5, blank=True, null=True)
  status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

  def __str__(self):
    return self.name

  def save(self, *args, **kwargs):
    if self.is_active:
      Competition.objects.exclude(pk=self.pk).update(is_active=False)
    super().save(*args, **kwargs)


class MachineTemplate(models.Model):
  OS_FAMILY_CHOICES = [
    ("windows", "Windows"),
    ("linux", "Linux"),
    ("network", "Network Appliance"),
    ("other", "Other"),
  ]

  name = models.CharField(max_length=100)
  os_family = models.CharField(max_length=20, choices=OS_FAMILY_CHOICES, default="linux")
  role = models.CharField(max_length=100, blank=True)
  description = models.TextField(blank=True)
  proxmox_vmid = models.PositiveIntegerField(
      null=True, blank=True,
      help_text="ProxMox template VMID (e.g. 9001 for tmpl-debian8)"
  )

  def __str__(self):
    return self.name


class CompetitionMachine(models.Model):
  competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="machines")
  machine_template = models.ForeignKey(MachineTemplate, on_delete=models.CASCADE)
  quantity = models.PositiveIntegerField(default=1)

  def __str__(self):
    return f"{self.quantity}x {self.machine_template.name} ({self.competition.name})"


class ProvisionedMachine(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("stopped", "Stopped"),
        ("error", "Error"),
    ]
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="provisioned_machines")
    team = models.ForeignKey("teams.Team", on_delete=models.CASCADE, related_name="vms")
    machine_template = models.ForeignKey(MachineTemplate, on_delete=models.CASCADE)
    vmid = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (VMID {self.vmid})"
