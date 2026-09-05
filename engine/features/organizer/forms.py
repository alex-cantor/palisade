from django import forms
from features.competitions.models import Competition, MachineTemplate, CompetitionMachine
from features.announcements.models import Announcement
from features.injects.models import Inject


class CompetitionForm(forms.ModelForm):
  class Meta:
    model = Competition
    fields = [
      "name", "start_time", "end_time",
      "difficulty", "industry",
      "scoring_interval_minutes",
    ]
    widgets = {
      "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
      "end_time":   forms.DateTimeInput(attrs={"type": "datetime-local"}),
    }


class MachineTemplateForm(forms.ModelForm):
  class Meta:
    model = MachineTemplate
    fields = ["name", "os_family", "role", "description", "proxmox_vmid"]
    widgets = {
      "description": forms.Textarea(attrs={"rows": 3}),
    }


class AddMachineForm(forms.Form):
  template = forms.ModelChoiceField(
    queryset=MachineTemplate.objects.all(),
    label="Machine Template",
  )
  quantity = forms.IntegerField(min_value=1, max_value=20, initial=1)


class ProvisionTeamsForm(forms.Form):
  num_teams    = forms.IntegerField(min_value=1, max_value=50, initial=10)
  username_prefix  = forms.CharField(max_length=20, initial="team")
  default_password = forms.CharField(max_length=50, initial="changeme")


class AddTeamForm(forms.Form):
  name = forms.CharField(max_length=50, label="Team Name")


class AddMemberForm(forms.Form):
  team      = forms.ModelChoiceField(queryset=None, label="Team")
  full_name = forms.CharField(max_length=150, label="Full Name", help_text="e.g. Jane Smith")
  username  = forms.CharField(max_length=150, help_text="Used to log in")
  password  = forms.CharField(max_length=150)

  def __init__(self, *args, competition=None, **kwargs):
    super().__init__(*args, **kwargs)
    if competition:
      from features.teams.models import Team
      self.fields["team"].queryset = Team.objects.filter(competition=competition)


class EditMemberForm(forms.Form):
  full_name = forms.CharField(max_length=150, label="Full Name")
  username  = forms.CharField(max_length=150)


class ResetPasswordForm(forms.Form):
  new_password = forms.CharField(max_length=50, label="New Password")


class AnnouncementForm(forms.ModelForm):
  class Meta:
    model = Announcement
    fields = ["title", "scheduled_for"]
    widgets = {
      "scheduled_for": forms.DateTimeInput(attrs={"type": "datetime-local"}),
    }


class InjectForm(forms.ModelForm):
  class Meta:
    model = Inject
    fields = ["title", "description", "start_time", "due_time", "points"]
    widgets = {
      "description": forms.Textarea(attrs={"rows": 3}),
      "start_time":  forms.DateTimeInput(attrs={"type": "datetime-local"}),
      "due_time":    forms.DateTimeInput(attrs={"type": "datetime-local"}),
    }
