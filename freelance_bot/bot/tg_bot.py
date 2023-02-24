from telegram import Update
from telegram.ext import CallbackContext, Updater, ConversationHandler, CommandHandler, CallbackQueryHandler
from django.conf import settings

import os
from dotenv import load_dotenv

from freelance_bot.bot.keyboards import main_menu_keyboard, customer_menu_keyboard, subscribe_keyboard
from freelance_bot.bot.keyboards import back_to_main_menu_keyboard, freelancer_menu_keyboard
from freelance_bot.bot.db_functions import get_or_create_customer, get_customer, get_tariff
from freelance_bot.bot.db_functions import set_tariff_to_customer

from freelance_bot.models import Customer

ROLE, CUSTOMER, TARIFF_PAYMENT, FREELANCER, NOT_FREELANCER = range(5)


def start(update: Update, context: CallbackContext):
    keyboard = main_menu_keyboard()
    update.message.reply_text(
        'Здравствуйте! Вас приветствует бот поддержки PHP. '
        'Вы Заказчик или Фрилансер?',
        reply_markup=keyboard
    )
    return ROLE


def main_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = main_menu_keyboard()
    query.edit_message_text(
        'Выберите роль',
        reply_markup=keyboard
    )
    return ROLE


def customer_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    
    user_id = update.effective_user
    customer = get_or_create_customer(
        telegram_id=user_id['id'],
        first_name=user_id['first_name'],
        last_name=user_id['last_name'],
        nickname=user_id['username']
    )

    keyboard = customer_menu_keyboard(customer)
    query.edit_message_reply_markup(keyboard)
    return CUSTOMER


def freelancer_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    
    user_id = update.effective_user
    customer = get_or_create_customer(
        telegram_id=user_id['id'],
        first_name=user_id['first_name'],
        last_name=user_id['last_name'],
        nickname=user_id['username']
    )

    if not customer.is_freelancer:
        keyboard = back_to_main_menu_keyboard()
        query.edit_message_text(
            'Вы не фрилансер. Для получения статуса фрилансера обратитесь '
            'к администратору.',
            reply_markup=keyboard
        )

        return NOT_FREELANCER
    else:
        keyboard = freelancer_menu_keyboard()
        query.edit_message_reply_markup(keyboard)
        return FREELANCER


def subscribe_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = subscribe_keyboard()
    query.edit_message_reply_markup(keyboard)
    return TARIFF_PAYMENT


def create_order(update: Update, context: CallbackContext):
    query = update.callback_query
    query.edit_message_text(
        'Создание заказа.'
    )
    return ROLE


def show_customer_orders(update: Update, context: CallbackContext):
    query = update.callback_query
    query.edit_message_text(
        'Заказы заказчика.'
    )

    return ROLE


def choose_order(update: Update, context: CallbackContext):
    query = update.callback_query
    query.edit_message_text(
        'Выберите заказ.'
    )
    return ROLE


def show_freelancer_orders(update: Update, context: CallbackContext):
    query = update.callback_query
    query.edit_message_text(
        'Заказы фрилансера.'
    )

    return ROLE


def tariff_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    tariff = get_tariff(query.data)

    # Здесь будет механизм оплаты

    user_id = update.effective_user
    set_tariff_to_customer(user_id['id'], tariff)

    customer = get_customer(
        telegram_id=user_id['id']
    )
    keyboard = customer_menu_keyboard(customer)

    query.edit_message_text(
        'Оплата прошла успешно.',
        reply_markup=keyboard
    )

    return CUSTOMER


def start_bot():
    token = settings.TG_TOKEN
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ROLE:
                [
                    CallbackQueryHandler(freelancer_menu, pattern='freelancer'),
                    CallbackQueryHandler(customer_menu, pattern='customer'),
                ],
            CUSTOMER:
                [
                    CallbackQueryHandler(subscribe_menu, pattern='choose_tariff'),
                    CallbackQueryHandler(subscribe_menu, pattern='subscribe'),
                    CallbackQueryHandler(create_order, pattern='create_order'),
                    CallbackQueryHandler(show_customer_orders, pattern='customer_orders'),
                    CallbackQueryHandler(main_menu, pattern='back_to_main_menu')
                ],
            TARIFF_PAYMENT:
                [
                    CallbackQueryHandler(tariff_payment, pattern='economy_tariff'),
                    CallbackQueryHandler(tariff_payment, pattern='standart_tariff'),
                    CallbackQueryHandler(tariff_payment, pattern='vip_tariff')
                ],
            FREELANCER:
                [
                    CallbackQueryHandler(choose_order, pattern='choose_order'),
                    CallbackQueryHandler(show_freelancer_orders, pattern='freelancer_orders'),
                    CallbackQueryHandler(main_menu, pattern='back_to_main_menu')
                ],
            NOT_FREELANCER:
                [
                    CallbackQueryHandler(main_menu, pattern='back_to_main_menu')
                ]
        },
        fallbacks=[CommandHandler('rerun', start)],
    )
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()
