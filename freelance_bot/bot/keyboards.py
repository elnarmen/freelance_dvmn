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