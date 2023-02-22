from django.db import migrations

def tariffs_values(apps, schema_editor):
    Tariff = apps.get_model('freelance_bot', 'Tariff')

    Tariff.objects.create(
        name='Эконом',
        description = 'До 5 заявок в месяц на помощь, по заявке ответят в течение суток',
        price=100
    )

    Tariff.objects.create(
        name='Стандарт',
        description = 'До 15 заявок в месяц, возможность закрепить подрядчика за собой, заявка будет рассмотрена в течение часа',
        price=300
    )

    Tariff.objects.create(
        name='VIP',
        description = 'До 60 заявок в месяц, возможность увидеть контакты подрядчика, заявка будет рассмотрена в течение часа',
        price=600
    )

class Migration(migrations.Migration):

    dependencies = [
        ('freelance_bot', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(tariffs_values)
    ]