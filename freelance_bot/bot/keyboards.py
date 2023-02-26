from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from freelance_bot.models import Customer


def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Заказчик", callback_data='customer')],
        [InlineKeyboardButton("Фрилансер", callback_data='freelancer')],
    ]
    return InlineKeyboardMarkup(keyboard)


def customer_menu_keyboard(customer: Customer):
    if customer.tariff:
        keyboard = [
            [InlineKeyboardButton("Создать заказ", callback_data='create_order')],
            [InlineKeyboardButton("Мои заказы", callback_data='customer_orders')],
            [InlineKeyboardButton("К выбору роли", callback_data='back_to_main_menu')]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Выбрать тариф", callback_data='choose_tariff')],
        ]
    
    return InlineKeyboardMarkup(keyboard)


def freelancer_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Выбрать заказ", callback_data='choose_order')],
        [InlineKeyboardButton("Мои заказы", callback_data='freelancer_orders')],
        [InlineKeyboardButton("К выбору роли", callback_data='back_to_main_menu')]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def subscribe_keyboard():
    keyboard = [
        [InlineKeyboardButton("Эконом", callback_data='economy_tariff')],
        [InlineKeyboardButton("Стандарт", callback_data='standart_tariff')],
        [InlineKeyboardButton("VIP", callback_data='vip_tariff')]
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("К выбору роли", callback_data='back_to_main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)


def orders_keyboard(*orders, current_orders_index=None):
    keyboard = [[
        InlineKeyboardButton(
            f"{order.name}",
            callback_data=f"{order.name}")
    ] for order in orders]

    if len(orders) == 5:
        if current_orders_index == 0:
            keyboard.append([InlineKeyboardButton("Еще", callback_data="next")])
        else:
            keyboard.append([
                InlineKeyboardButton("Назад", callback_data="previous"),
                InlineKeyboardButton("Еще", callback_data="next"),
            ])
        keyboard.append([InlineKeyboardButton("Главное меню", callback_data="freelancer")])
    else:
        if current_orders_index != 0:
            keyboard.append([InlineKeyboardButton("Назад", callback_data="previous")])
        keyboard.append([InlineKeyboardButton("Главное меню", callback_data="freelancer")])

    return InlineKeyboardMarkup(keyboard)



def available_order_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Взять в работу", callback_data="take_order"),
            InlineKeyboardButton("Назад", callback_data="back")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def freelancer_order_keyboard():
    keyboard = [
        [InlineKeyboardButton("Назад", callback_data="back")],
        [InlineKeyboardButton("Отказаться от заказа", callback_data="cancel_order")]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_document_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Приложить файл", callback_data="attach_file"),
            InlineKeyboardButton("Не прикладывать", callback_data="not_attach_file")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)
