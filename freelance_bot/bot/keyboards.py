from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Заказчик", callback_data='customer')],
        [InlineKeyboardButton("Фрилансер", callback_data='freelancer')],
    ]
    return InlineKeyboardMarkup(keyboard)


def customer_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Выбрать тариф", callback_data='choose_tariff')],
    ]
    return InlineKeyboardMarkup(keyboard)


def subscribe_keyboard():
    keyboard = [
        [InlineKeyboardButton("Эконом", callback_data='economy_tariff')],
        [InlineKeyboardButton("Стандарт", callback_data='standart_tariff')],
        [InlineKeyboardButton("VIP", callback_data='vip_tariff')],
        []
    ]
    return InlineKeyboardMarkup(keyboard)
