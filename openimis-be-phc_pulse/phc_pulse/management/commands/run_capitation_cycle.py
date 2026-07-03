from datetime import date

from django.core.management.base import BaseCommand, CommandError

from core.models import User
from phc_pulse.services import MissingCapitationRateError, run_capitation_cycle


class Command(BaseCommand):
    help = (
        "Runs a PHC Pulse capitation cycle for the given period, creating a "
        "draft PaymentBatch. CLI wrapper around phc_pulse.services.run_capitation_cycle "
        "for testing/demo purposes outside the GraphQL API."
    )

    def add_arguments(self, parser):
        parser.add_argument("period_start", type=str, help="YYYY-MM-DD")
        parser.add_argument("period_end", type=str, help="YYYY-MM-DD")
        parser.add_argument(
            "--username",
            type=str,
            default=None,
            help="core.User username to attribute the batch to "
            "(defaults to the first interactive user found)",
        )

    def handle(self, *args, **options):
        period_start = date.fromisoformat(options["period_start"])
        period_end = date.fromisoformat(options["period_end"])

        username = options.get("username")
        if username:
            user = User.objects.filter(username=username).first()
            if user is None:
                raise CommandError(f"No core.User found with username={username}")
        else:
            user = User.objects.filter(i_user__isnull=False).order_by("id").first()
            if user is None:
                raise CommandError(
                    "No core.User found to attribute this run to; pass --username explicitly."
                )

        try:
            batch = run_capitation_cycle(period_start, period_end, user)
        except MissingCapitationRateError as exc:
            self.stdout.write(self.style.WARNING(str(exc)))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Created PaymentBatch {batch.id} with {batch.lines.count()} "
                f"line(s) for {period_start}..{period_end}"
            )
        )
