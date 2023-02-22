from telegram import Update
from telegram.ext import CallbackContext, Updater, ConversationHandler, CommandHandler, CallbackQueryHandler
from django.conf import settings

import os
from dotenv import load_dotenv

from freelance_bot.bot.keyboards import main_menu_keyboard, customer_menu_keyboard, subscribe_keyboard

ROLE, CUSTOMER = range(2)


def start(update: Update, context: CallbackContext):
    keyboard = main_menu_keyboard()
    update.message.reply_text(
        'Здравствуйте! Вас приветствует бот поддержки PHP. '
        'Вы Заказчик или Фрилансер?',
        reply_markup=keyboard
    )
    return ROLE


def customer_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = customer_menu_keyboard()
    query.edit_message_reply_markup(keyboard)
    return CUSTOMER


def subscribe_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = subscribe_keyboard()
    query.edit_message_reply_markup(keyboard)
    return ROLE


def start_bot():
    token = settings.TG_TOKEN
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ROLE:
                [
                    # CallbackQueryHandler(freelancer_menu, pattern='freelancer'),
                    CallbackQueryHandler(customer_menu, pattern='customer'),
                ],
            CUSTOMER:
                [
                    CallbackQueryHandler(subscribe_menu, pattern='choose_tariff'),
                    CallbackQueryHandler(subscribe_menu, pattern='subscribe')
                ]
        },
        fallbacks=[CommandHandler('rerun', start)],
    )
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()
