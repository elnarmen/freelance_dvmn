from telegram import Update, InputFile, LabeledPrice
from telegram.ext import CallbackContext, Updater, ConversationHandler, CommandHandler, CallbackQueryHandler, \
    MessageHandler, Filters
from django.conf import settings

import os
from dotenv import load_dotenv
from more_itertools import chunked

from freelance_bot.bot.keyboards import main_menu_keyboard, customer_menu_keyboard, subscribe_keyboard
from freelance_bot.bot.keyboards import orders_keyboard, available_order_keyboard, freelancer_order_keyboard
from freelance_bot.bot.keyboards import back_to_main_menu_keyboard, freelancer_menu_keyboard
from freelance_bot.bot.keyboards import get_document_keyboard
from freelance_bot.bot.db_functions import get_or_create_customer, get_customer, get_tariff, create_order
from freelance_bot.bot.db_functions import set_tariff_to_customer, create_order_without_file

from freelance_bot.models import Customer, Order

(
    ROLE,
    CUSTOMER,
    TARIFF_PAYMENT,
    CREATE_ORDERS_DESCRIPTION,
    GET_ORDER_FILE,
    COLLECT_ORDER_DATA,
    FREELANCER,
    NOT_FREELANCER,
    CHOOSING_ORDER,
    GET_DOCUMENT
) = range(10)


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

    context.user_data['telegram_id'] = user_id['id']

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

    context.user_data['telegram_id'] = user_id['id']

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


def get_orders_title(update: Update, context: CallbackContext):
    query = update.callback_query
    query.edit_message_text('Введите название заказа:')

    return CREATE_ORDERS_DESCRIPTION


def get_orders_description(update: Update, context: CallbackContext):
    user_data = context.user_data
    order_title = update.message.text
    user_data['order_title'] = order_title

    update.message.reply_text('Введите описание заказа:')

    return GET_ORDER_FILE


def get_document(update: Update, context: CallbackContext):
    user_data = context.user_data
    order_description = update.message.text
    user_data['order_description'] = order_description

    keyboard = get_document_keyboard()
    update.message.reply_text(
        'Если необходимо, приложите файл:',
        reply_markup=keyboard
    )

    return COLLECT_ORDER_DATA


def get_order_file(update: Update, context: CallbackContext):
    query = update.callback_query
    query.edit_message_text(
        'Приложите файл:',
    )

    return GET_DOCUMENT


def collect_order_data(update: Update, context: CallbackContext):
    if update.message.document:
        customer_id = update.effective_user.id
        order_title = context.user_data['order_title']
        order_description = context.user_data['order_description']
        file = context.bot.get_file(update.message.document)
        telegram_file_id = file.file_id

        create_order(order_title, order_description, telegram_file_id, customer_id)

        customer = get_customer(
            telegram_id=customer_id
        )
        keyboard = customer_menu_keyboard(customer)
        
        update.message.reply_text(
            'Ваш заказ создан!',
            reply_markup=keyboard
        )

        return CUSTOMER


def collect_order_data_without_file(update: Update, context: CallbackContext):
    query = update.callback_query
    customer_id = update.effective_user.id
    order_title = context.user_data['order_title']
    order_description = context.user_data['order_description']

    create_order_without_file(
        order_title,
        order_description,
        customer_id
    )

    customer = get_customer(
        telegram_id=customer_id
    )
    keyboard = customer_menu_keyboard(customer)
    
    query.edit_message_text(
        'Ваш заказ создан!',
        reply_markup=keyboard
    )

    return CUSTOMER


def show_customer_orders(update: Update, context: CallbackContext):
    query = update.callback_query
    query.edit_message_text(
        'Заказы заказчика.'
    )

    return ROLE


def request_freelanser_orders(update: Update, context: CallbackContext):
    user_id = update.effective_user
    customer = Customer.objects.get(telegram_id=user_id['id'])
    orders = customer.freelancer_orders.all()
    orders_per_page = 5
    context.user_data['orders'] = list(chunked(orders, orders_per_page))
    context.user_data['is_available_orders'] = False
    show_orders(update, context)


def request_available_orders(update: Update, context: CallbackContext):
    orders = Order.objects.filter(status=Order.CREATE)
    orders_per_page = 5
    context.user_data['orders'] = list(chunked(orders, orders_per_page))
    context.user_data['is_available_orders'] = True
    show_orders(update, context)


def show_orders(update: Update, context: CallbackContext):
    query = update.callback_query
    current_orders_index = context.user_data.get('current_orders_index', 0)
    if query.data == 'previous' and current_orders_index > 0:
        current_orders_index -= 1
        context.user_data['current_orders_index'] = current_orders_index

    if query.data == 'next':
        current_orders_index += 1
        context.user_data['current_orders_index'] = current_orders_index

    if 0 <= current_orders_index < len(context.user_data['orders']):
        context.user_data['current_orders'] = context.user_data['orders'][current_orders_index]
    else:
        text = 'Заказов нет'
        keyboard = freelancer_menu_keyboard()
        query.edit_message_text(text, reply_markup=keyboard)
        return CHOOSING_ORDER

    orders = context.user_data['current_orders']
    keyboard = orders_keyboard(*orders)
    query.message.reply_text(
        text='Ваши заказы для выполнения:',
        reply_markup=keyboard
    )
    return FREELANCER


def show_order_description(update: Update, context: CallbackContext):
    query = update.callback_query
    order = Order.objects.get(name=query.data)
    keyboard = available_order_keyboard() if context.user_data['is_available_orders'] \
        else freelancer_order_keyboard()

    text = f'''
{order.name}
    
{order.description}    
    '''
    try:
        if order.telegram_file_id:
            query.message.reply_document(
                document=order.telegram_file_id,
                caption=text,
                reply_markup=keyboard
            )
        else:
            query.message.reply_text(
                text=text,
                reply_markup=keyboard
            )

        return FREELANCER
    except ValueError: 
        query.message.reply_text(text=text, reply_markup=keyboard)
    except FileNotFoundError:
        query.message.reply_text(text=text, reply_markup=keyboard)


def tariff_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    tariff = get_tariff(query.data)

    # chat_id = update.callback_query.message.chat.id
    # title = "Оплата тарифа"
    # description = "Оплата тарифа заказчиком"
    # payload = "Custom-Payload"
    # provider_token = settings.PAYMENT_PROVIDER_TOKEN
    # currency = "rub"
    # prices = [LabeledPrice("Сумма заказа", tariff.price * 100)]

    # context.bot.send_invoice(
    #     chat_id, title, description, payload, provider_token, currency, prices
    # )

    set_tariff_to_customer(context.user_data['telegram_id'], tariff)

    customer = get_customer(
        telegram_id=context.user_data['telegram_id']
    )
    keyboard = customer_menu_keyboard(customer)

    query.edit_message_text(
        'Оплата прошла успешно.',
        reply_markup=keyboard
    )

    return CUSTOMER

def precheckout_callback(update: Update, context: CallbackContext):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        query.answer(ok=True)


def save_freelancer_order():
    pass

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
                    CallbackQueryHandler(get_orders_title, pattern='create_order'),
                    CallbackQueryHandler(show_customer_orders, pattern='customer_orders'),
                    CallbackQueryHandler(main_menu, pattern='back_to_main_menu')
                ],
            TARIFF_PAYMENT:
                [
                    CallbackQueryHandler(tariff_payment, pattern='economy_tariff'),
                    CallbackQueryHandler(tariff_payment, pattern='standart_tariff'),
                    CallbackQueryHandler(tariff_payment, pattern='vip_tariff')
                ],
            CREATE_ORDERS_DESCRIPTION:
                [
                    MessageHandler(Filters.text, get_orders_description)
                ],
            GET_ORDER_FILE:
                [
                    MessageHandler(Filters.text, get_document)
                ],
            COLLECT_ORDER_DATA:
                [   
                    CallbackQueryHandler(get_order_file, pattern='attach_file'),
                    CallbackQueryHandler(
                        collect_order_data_without_file,
                        pattern='not_attach_file'
                    )
                ],
            FREELANCER:
                [
                    CallbackQueryHandler(request_available_orders, pattern='choose_order'),
                    CallbackQueryHandler(request_freelanser_orders, pattern='freelancer_orders'),
                    CallbackQueryHandler(main_menu, pattern='back_to_main_menu'),
                    CallbackQueryHandler(show_orders, pattern='next'),
                    CallbackQueryHandler(freelancer_menu, pattern='freelancer'),
                    CallbackQueryHandler(freelancer_menu, pattern='take_order'),
                    CallbackQueryHandler(show_orders, pattern='previous'),
                    CallbackQueryHandler(show_orders, pattern='back'),
                    CallbackQueryHandler(show_order_description, pattern=None)
                ],
            NOT_FREELANCER:
                [
                    CallbackQueryHandler(main_menu, pattern='back_to_main_menu')
                ],
            GET_DOCUMENT:
                [
                    MessageHandler(Filters.document, collect_order_data)
                ],
        },
        fallbacks=[CommandHandler('rerun', start)],
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

