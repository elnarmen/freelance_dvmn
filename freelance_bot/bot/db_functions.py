from freelance_bot.models import Customer, Tariff, Order


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


def create_order(name, description, telegram_file_id, customer_id):
    customer = Customer.objects.get(telegram_id=customer_id)
    Order.objects.create(
        name=name,
        description=description,
        telegram_file_id=telegram_file_id, 
        customer=customer
    )


def create_order_without_file(name, description, customer_id):
    customer = Customer.objects.get(telegram_id=customer_id)
    Order.objects.create(
        name=name,
        description=description,
        customer=customer
    )


def get_customer_orders(telegram_id):
    customer = Customer.objects.get(telegram_id=telegram_id)
    orders = customer.customer_orders.all()
    return orders


def delete_order(order_title):
    order = Order.objects.filter(name=order_title)
    order.delete()
