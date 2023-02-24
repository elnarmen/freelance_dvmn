from freelance_bot.models import Customer, Tariff


def get_or_create_customer(telegram_id, first_name, last_name, nickname):

    customer = Customer.objects.get_or_create(
        telegram_id=telegram_id,
        first_name=first_name,
        last_name=last_name,
        nickname=nickname
    )

    return customer[0]


def get_customer(telegram_id):
    return Customer.objects.get(telegram_id=telegram_id)


def get_tariff(tariff_name):
    if tariff_name == 'economy_tariff':
        return Tariff.objects.get(name='Эконом')
    elif tariff_name == 'standart_tariff':
        return Tariff.objects.get(name='Стандарт')
    else:
        return Tariff.objects.get(name='VIP')


def set_tariff_to_customer(telegram_id, tariff):
    Customer.objects.filter(telegram_id=telegram_id).update(tariff=tariff)