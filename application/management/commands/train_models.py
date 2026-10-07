from django.core.management.base import BaseCommand, CommandError
from application.ml import train_all

class Command(BaseCommand):
    help = "Train the Bi-LSTM, Bi-GRU and hybrid models."

    def add_arguments(self, parser):
        parser.add_argument("--dataset", default="data/malicious_phish.csv")
        parser.add_argument("--epochs", type=int, default=5)

    def handle(self, *args, **options):
        try:
            result = train_all(options["dataset"], epochs=options["epochs"])
        except Exception as exc:
            raise CommandError(str(exc))
        for name, m in result.items():
            self.stdout.write(
                f"{name}: accuracy={m['accuracy']:.4f}, "
                f"precision={m['precision']:.4f}, recall={m['recall']:.4f}, f1={m['f1']:.4f}"
            )
