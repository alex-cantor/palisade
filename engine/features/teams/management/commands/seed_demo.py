from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from features.competitions.models import Competition
from features.teams.models import Team, TeamMember
from features.announcements.models import Announcement
from features.injects.models import Inject, InjectSubmission
from features.network.models import Service


# (team_name, [(username, full_name), ...])
TEAMS = [
    ("Firewall FC",    [("jsmith",    "Jane Smith"),    ("bwilson",   "Bob Wilson")]),
    ("Null Pointers",  [("agarcia",   "Ana Garcia"),    ("tlee",      "Tom Lee")]),
    ("Stack Smashers", [("cpatel",    "Chris Patel"),   ("mrogers",   "Maya Rogers")]),
    ("Root Access",    [("dkumar",    "Dev Kumar"),     ("sfoster",   "Sara Foster")]),
    ("Packet Raiders", [("nwang",     "Nina Wang"),     ("jmartinez", "Jose Martinez")]),
]

ANNOUNCEMENTS = [
    "Welcome to the Palisade Demo Competition. Good luck!",
    "Reminder: all service credentials are in your team packet.",
    "Inject 1 (Heartbeat) is now available. Due in 10 minutes.",
    "Scoring check complete. Standings updated on the scoreboard.",
]

INJECTS = [
    ("Heartbeat",               -60,   10,  10),
    ("Phishing Infographic",    -30,   30,  25),
    ("Bug Bounty Write-up",       0,   90,  50),
    ("Add acantor as Admin",     15,   45,  20),
    ("Password Policy Report",   30,  120,  40),
]

SERVICES = [
    ("HTTP",  "10.0.1.10", True),
    ("SSH",   "10.0.1.11", True),
    ("SMTP",  "10.0.1.12", False),
    ("RDP",   "10.0.1.13", True),
    ("DNS",   "10.0.1.14", False),
]

DEMO_PASSWORD = "demo"
COMPETITION_NAME = "Demo Competition"


class Command(BaseCommand):
    help = "Seed a demo competition with teams, members, announcements, injects, and services."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo data and re-seed from scratch.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            Competition.objects.filter(name=COMPETITION_NAME).delete()
            all_usernames = [u for _, members in TEAMS for u, _ in members]
            User.objects.filter(username__in=all_usernames).delete()
            Service.objects.filter(host_ip__startswith="10.0.1.").delete()
            self.stdout.write("Cleared existing demo data.")

        if Competition.objects.filter(name=COMPETITION_NAME).exists():
            self.stdout.write("Demo competition already exists. Run with --reset to start fresh.")
            return

        now = timezone.now()

        competition = Competition.objects.create(
            name=COMPETITION_NAME,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=7),
            is_active=True,
            scoring_interval_minutes=5,
            difficulty="intermediate",
            industry="tech",
            generation_mode="random",
            random_machine_count=5,
            status="live",
        )
        self.stdout.write(f"Created competition: {competition.name}")

        teams = []
        for team_name, members in TEAMS:
            team = Team.objects.create(competition=competition, name=team_name)
            for username, full_name in members:
                first, _, last = full_name.partition(" ")
                user = User.objects.create_user(
                    username=username, password=DEMO_PASSWORD,
                    first_name=first, last_name=last,
                )
                TeamMember.objects.create(user=user, team=team)
            teams.append(team)

        total_members = sum(len(m) for _, m in TEAMS)
        self.stdout.write(f"Created {len(teams)} teams, {total_members} members (password: '{DEMO_PASSWORD}')")

        for title in ANNOUNCEMENTS:
            Announcement.objects.create(competition=competition, title=title, read=False)
        self.stdout.write(f"Created {len(ANNOUNCEMENTS)} announcements")

        injects = []
        for title, start_offset_min, duration_min, points in INJECTS:
            inject = Inject.objects.create(
                competition=competition,
                title=title,
                start_time=now + timedelta(minutes=start_offset_min),
                due_time=now + timedelta(minutes=start_offset_min + duration_min),
                points=points,
            )
            injects.append(inject)
        self.stdout.write(f"Created {len(injects)} injects")

        submissions = [
            (injects[0], [0, 1, 2, 3, 4]),
            (injects[1], [0, 2, 4]),
            (injects[2], [1]),
        ]
        for inject, team_indices in submissions:
            for i in team_indices:
                InjectSubmission.objects.create(
                    inject=inject, team=teams[i],
                    submitted_at=now - timedelta(minutes=5),
                )
        self.stdout.write("Seeded inject submissions")

        for name, ip, is_up in SERVICES:
            Service.objects.get_or_create(name=name, host_ip=ip, defaults={"is_up": is_up, "last_checked": now})
        self.stdout.write(f"Created {len(SERVICES)} services")

        self.stdout.write("")
        self.stdout.write("Demo ready")
        self.stdout.write(f"  Login at:  /login/   password for all: '{DEMO_PASSWORD}'")
        for team_name, members in TEAMS:
            self.stdout.write(f"  {team_name}")
            for username, full_name in members:
                self.stdout.write(f"    {full_name:<20}  {username}")
