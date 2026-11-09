from django.core.management.base import BaseCommand

from kreo.referentials.loaders import load_cities, load_disciplines


class Command(BaseCommand):
    help = "Charge (ou met à jour) les disciplines et les 19 communes bruxelloises."

    def handle(self, *args, **options):
        d = load_disciplines()
        c = load_cities()
        self.stdout.write(self.style.SUCCESS(f"{d} disciplines, {c} communes chargées."))
