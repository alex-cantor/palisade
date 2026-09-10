import time
from django.core.management.base import BaseCommand
from features.competitions.models import Competition
from features.network.checker import run_checks


class Command(BaseCommand):
    help = "Check service availability for all live competitions and record results."

    def add_arguments(self, parser):
        parser.add_argument("--competition", type=int, default=None)
        parser.add_argument("--loop", action="store_true",
            help="Run continuously, sleeping scoring_interval_minutes between rounds.")

    def handle(self, *args, **options):
        while True:
            competitions = (
                Competition.objects.filter(pk=options["competition"])
                if options["competition"]
                else Competition.objects.filter(status="live")
            )

            for comp in competitions:
                results = run_checks(comp)
                up = sum(1 for r in results if r["is_up"])
                down = len(results) - up
                self.stdout.write(f"{comp.name}: {up} up, {down} down")

            if not options["loop"]:
                break

            comps = list(competitions)
            interval = min((c.scoring_interval_minutes for c in comps), default=10)
            time.sleep(interval * 60)
