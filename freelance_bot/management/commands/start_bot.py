from django.core.management import BaseCommand

from freelance_bot.bot.tg_bot import start_bot


class Command(BaseCommand):
    help = 'Телеграм бот'

    def handle(self, *args, **options):
        start_bot()
