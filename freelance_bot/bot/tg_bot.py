from textwrap import dedent

from telegram import Update, InputFile, LabeledPrice
from telegram.ext import CallbackContext, Updater, ConversationHandler, CommandHandler, CallbackQueryHandler, \
    MessageHandler, Filters, PreCheckoutQueryHandler
from django.conf import settings

from more_itertools import chunked
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from freelance_bot.bot.keyboards import main_menu_keyboard, customer_menu_keyboard, subscribe_keyboard, \
    customer_order_keyboard
from freelance_bot.bot.keyboards import orders_keyboard, available_order_keyboard, freelancer_order_keyboard, customer_orders_keyboard
from freelance_bot.bot.keyboards import back_to_main_menu_keyboard, freelancer_menu_keyboard
from freelance_bot.bot.keyboards import get_document_keyboard
from freelance_bot.bot.db_functions import get_or_create_customer, get_customer, get_tariff, create_order, \
    get_customer_orders, delete_order, set_tariff_to_customer, create_order_without_file, create_message, \
    get_messages_from_order

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
    GET_DOCUMENT,
    WAITING_CUSTOMER_MESSAGE,
    WAITING_FREELANCER_MESSAGE
) = range(12)


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
    query.edit_message_reply_markup(keyboard)
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
    if query:
        query.edit_message_reply_markup(keyboard)
    else:
        update.message.reply_text('Оплата прошла успешно.', reply_markup=keyboard)
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
    context.user_data['title_query'] = query
    query.edit_message_text('Введите название заказа:')

    return CREATE_ORDERS_DESCRIPTION


def get_orders_description(update: Update, context: CallbackContext):
    user_data = context.user_data
    order_title = update.message.text
    if Order.objects.filter(name=order_title).exists():
        update.message.reply_text('Заказ с таким названием уже существует, введите другое название:')
        update.callback_query = context.user_data['title_query']
        get_orders_title(update, context)
    else:
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
    if not update.message.document:
        update.message.reply_text(
            '''
            Неверный формат файла. Приложите документ или выберите "Не прикладывать"
            ''',
            reply_markup=get_document_keyboard()
        )
        return COLLECT_ORDER_DATA

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


def request_customer_orders(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    orders = get_customer_orders(telegram_id)
    orders_per_page = 5
    context.user_data['orders'] = list(chunked(orders, orders_per_page))
    show_customer_orders(update, context)

    return CUSTOMER


def show_customer_orders(update: Update, context: CallbackContext):
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
        if current_orders_index > 0:
            text = 'Вы просмотрели все заказы'
            keyboard = [
                [InlineKeyboardButton("Назад", callback_data='previous')],
                [InlineKeyboardButton("Вернуться в меню", callback_data='customer')]
            ]
            query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            return CUSTOMER
        text = 'Заказов нет'
        keyboard = [
            [InlineKeyboardButton("Вернуться в меню", callback_data='customer')],
        ]
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return CUSTOMER

    orders = context.user_data['current_orders']
    keyboard = customer_orders_keyboard(*orders, current_orders_index=current_orders_index)
    query.message.reply_text(
        text='Ваши заказы:',
        reply_markup=keyboard
    )
    return CUSTOMER


def show_customer_order_description(update: Update, context: CallbackContext):
    query = update.callback_query
    order = Order.objects.get(name=query.data)
    if order.freelancer:
        keyboard = customer_order_keyboard(freelancer=True)
    else:
        keyboard = customer_order_keyboard(freelancer=False)

    text = f'''

Название заказа: {order.name}

Описание заказа: {order.description}

Статус заказа:  {order.get_status_display()}
        '''
    if order.freelancer:
        text += f'''
Исполнитель заказа: {order.freelancer}
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
        context.user_data['viewed_order_title'] = query.data
        context.user_data['freelancer_of_order'] = order.freelancer.telegram_id
        return CUSTOMER
    except ValueError:
        query.message.reply_text(text=text, reply_markup=keyboard)
    except FileNotFoundError:
        query.message.reply_text(text=text, reply_markup=keyboard)


def delete_customer_order(update: Update, context: CallbackContext):
    order_title = context.user_data['viewed_order_title']
    delete_order(order_title)
    update.callback_query.answer('Заказ удален!', show_alert=True)
    return request_customer_orders(update, context)


def request_freelanser_orders(update: Update, context: CallbackContext):
    user_id = update.effective_user['id']
    customer = Customer.objects.get(telegram_id=user_id)
    orders = customer.freelancer_orders.filter(status='work')
    orders_per_page = 5
    context.user_data['orders'] = list(chunked(orders, orders_per_page))
    context.user_data['is_available_orders'] = False
    show_orders(update, context)


def request_available_orders(update: Update, context: CallbackContext):
    orders = Order.objects.filter(status='create')
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

    if query.data == "cancel_order":
        keyboard = freelancer_menu_keyboard()
        query.edit_message_reply_markup(keyboard)
        return CHOOSING_ORDER

    if 0 <= current_orders_index < len(context.user_data['orders']):
        context.user_data['current_orders'] = context.user_data['orders'][current_orders_index]
    else:
        if current_orders_index > 0:
            text = 'Вы просмотрели все заказы'
            keyboard = [
                [InlineKeyboardButton("Назад", callback_data='previous')],
                [InlineKeyboardButton("Вернуться в меню", callback_data='freelancer')]
            ]
            query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            return FREELANCER
        text = 'Заказов нет'
        keyboard = [
            [InlineKeyboardButton("Вернуться в меню", callback_data='freelancer')],
        ]
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return FREELANCER

    orders = context.user_data['current_orders']
    keyboard = orders_keyboard(*orders, current_orders_index=current_orders_index)
    query.message.reply_text(
        text='Ваши заказы для выполнения:',
        reply_markup=keyboard
    )
    return FREELANCER


def show_freelancer_order_description(update: Update, context: CallbackContext):
    query = update.callback_query
    order = Order.objects.get(name=query.data)
    keyboard = available_order_keyboard() if \
        context.user_data['is_available_orders'] else freelancer_order_keyboard()

    text = f'''
Название заказа: {order.name}

Описание заказа: {order.description}

Статус заказа:  {Order.OrderStatus(order.status).label}
            '''
    if order.freelancer:
        text += f'''
Заказчик: {order.customer}
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
        context.user_data['viewed_order_title'] = query.data
        context.user_data['customer_of_order'] = order.customer.telegram_id
        return FREELANCER
    except ValueError:
        query.message.reply_text(text=text, reply_markup=keyboard)
    except FileNotFoundError:
        query.message.reply_text(text=text, reply_markup=keyboard)


def customer_chat(update: Update, context: CallbackContext):
    query = update.callback_query
    order = Order.objects.get(name=context.user_data['viewed_order_title'])
    
    order_messages = get_messages_from_order(order)

    if order_messages:
        prev_messages = 'Предыдущие сообщения: \n' 

        for number, message in enumerate(order_messages):
            prev_message = dedent(
                f"""\
                Сообщение №{number+1}
                От: {message.message_from.nickname}
                К: {message.message_to.nickname}
                
                {message.message}

                """
            )

            prev_messages += prev_message

        prev_messages += 'Вы можете написать исполнителю ещё сообщение,\n'
        prev_messages += 'либо ввести quit для возврата в главное меню:'
    else:
        prev_messages = dedent(
            f"""\
            Предыдущих сообщений нет. 

            Напишите сообщение исполнителю, либо введите quit для
            возврата в главное меню:
            """
        )

    query.message.reply_text(
        text=prev_messages,
    )

    return WAITING_CUSTOMER_MESSAGE


def get_customer_message(update: Update, context: CallbackContext):
    user_data = context.user_data
    message = update.message.text
    order = Order.objects.get(name=context.user_data['viewed_order_title'])
    customer_id = update.effective_user.id
    freelancer_id = context.user_data['freelancer_of_order']

    if message != 'quit':
        create_message(
            order,
            customer_id,
            freelancer_id,
            message
        )

        message_to_freelancer = dedent(
            f"""\
            У вас новое сообщение от заказчика в заказе
            '{order.name}'. Перейдите в чат этого заказа, чтобы его прочитать.
            """
        )

        context.bot.send_message(
            text=message_to_freelancer,
            chat_id=freelancer_id,
        )

        text = dedent(
            f"""\
            Ваше сообщение отправлено исполнителю!

            Вы можете написать исполнителю ещё сообщение,
            либо ввести quit для возврата в главное меню:
            """
        )

        update.message.reply_text(text)

        return WAITING_CUSTOMER_MESSAGE
    else:
        customer = get_customer(
            telegram_id=customer_id
        )
        keyboard = customer_menu_keyboard(customer)

        update.message.reply_text(
            "Выберите действие:",
            reply_markup=keyboard
        )

        return CUSTOMER


def freelancer_chat(update: Update, context: CallbackContext):
    query = update.callback_query
    order = Order.objects.get(name=context.user_data['viewed_order_title'])
    
    order_messages = get_messages_from_order(order)

    if order_messages:
        prev_messages = 'Предыдущие сообщения: \n' 

        for number, message in enumerate(order_messages):
            prev_message = dedent(
                f"""\
                Сообщение №{number+1}
                От: {message.message_from.nickname}
                К: {message.message_to.nickname}
                
                {message.message}

                """
            )

            prev_messages += prev_message

        prev_messages += 'Вы можете написать заказчику ещё сообщение,\n'
        prev_messages += 'либо ввести quit для возврата в главное меню:'
    else:
        prev_messages = dedent(
            f"""\
            Предыдущих сообщений нет. 

            Напишите сообщение заказчику, либо введите quit для
            возврата в главное меню:
            """
        )

    query.message.reply_text(
        text=prev_messages,
    )

    return WAITING_FREELANCER_MESSAGE


def get_freelancer_message(update: Update, context: CallbackContext):
    user_data = context.user_data
    message = update.message.text
    order = Order.objects.get(name=context.user_data['viewed_order_title'])
    freelancer_id = update.effective_user.id
    customer_id = context.user_data['customer_of_order']

    if message != 'quit':
        create_message(
            order,
            freelancer_id,
            customer_id,
            message
        )

        message_to_customer = dedent(
            f"""\
            У вас новое сообщение от исполнителя заказа
            '{order.name}'. Перейдите в чат этого заказа, чтобы его прочитать.
            """
        )

        context.bot.send_message(
            text=message_to_customer,
            chat_id=customer_id,
        )

        text = dedent(
            f"""\
            Ваше сообщение отправлено заказчику!

            Вы можете написать заказчику ещё сообщение,
            либо ввести quit для возврата в главное меню:
            """
        )

        update.message.reply_text(text)

        return WAITING_FREELANCER_MESSAGE
    else:
        keyboard = freelancer_menu_keyboard()

        update.message.reply_text(
            "Выберите действие:",
            reply_markup=keyboard
        )

        return FREELANCER


def tariff_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    tariff = get_tariff(query.data)
    context.user_data['tariff'] = tariff
    chat_id = update.callback_query.message.chat.id
    title = "Оплата тарифа"
    description = "Оплата тарифа заказчиком"
    payload = "Custom-Payload"
    provider_token = settings.PAYMENT_PROVIDER_TOKEN
    currency = "rub"
    prices = [LabeledPrice("Сумма заказа", tariff.price * 100)]

    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )

    return CUSTOMER


def precheckout_callback(update: Update, context: CallbackContext):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        query.answer(ok=True)

        tariff = context.user_data['tariff']
        set_tariff_to_customer(context.user_data['telegram_id'], tariff)

    return CUSTOMER


def save_freelancer_order(update: Update, context: CallbackContext):
    user_id = update.effective_user['id']
    freelancer = Customer.objects.get(telegram_id=user_id)
    order = Order.objects.get(name=context.user_data['viewed_order_title'])
    order.status = 'work'
    order.freelancer = freelancer
    order.save()

    message_to_customer = dedent(
        f"""\
        Ваш заказ '{order.name}' взят в работу.

        Теперь вы можете общаться с исполнителем.
        Для этого нажмите кноаку "Чат" в меню заказа.
        """
    )

    context.bot.send_message(
        text=message_to_customer,
        chat_id=order.customer.telegram_id,
    )

    return freelancer_menu(update, context)


def cancel_freelancer_order(update: Update, context: CallbackContext):
    order = Order.objects.get(name=context.user_data['viewed_order_title'])
    order.status = 'create'
    order.freelancer = None
    order.save()

    message_to_customer = f"Исполнитель отказался от заказа '{order.name}'."

    context.bot.send_message(
        text=message_to_customer,
        chat_id=order.customer.telegram_id,
    )

    return request_freelanser_orders(update, context)


def complete_freelancer_order(update: Update, context: CallbackContext):
    order = Order.objects.get(name=context.user_data['viewed_order_title'])
    order.status = 'closed'
    order.save()

    message_to_customer = f"Испонитель завершил заказ '{order.name}'."

    context.bot.send_message(
        text=message_to_customer,
        chat_id=order.customer.telegram_id,
    )

    return request_freelanser_orders(update, context)


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
                    CallbackQueryHandler(request_customer_orders, pattern='customer_orders'),
                    CallbackQueryHandler(main_menu, pattern='back_to_main_menu'),
                    CallbackQueryHandler(customer_menu, pattern='customer'),
                    CallbackQueryHandler(show_customer_orders, pattern='next'),
                    CallbackQueryHandler(show_customer_orders, pattern='previous'),
                    CallbackQueryHandler(show_customer_orders, pattern='back'),
                    PreCheckoutQueryHandler(precheckout_callback, pass_update_queue=True),
                    MessageHandler(Filters.successful_payment, customer_menu),
                    CallbackQueryHandler(delete_customer_order, pattern='delete_order'),
                    CallbackQueryHandler(customer_chat, pattern='chat'),
                    CallbackQueryHandler(show_customer_order_description, pattern=None),
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
                    CallbackQueryHandler(save_freelancer_order, pattern='take_order'),
                    CallbackQueryHandler(show_orders, pattern='previous'),
                    CallbackQueryHandler(show_orders, pattern='back'),
                    CallbackQueryHandler(cancel_freelancer_order, pattern='cancel_order'),
                    CallbackQueryHandler(complete_freelancer_order, pattern='complete_order'),
                    CallbackQueryHandler(freelancer_chat, pattern='chat'),
                    CallbackQueryHandler(show_freelancer_order_description, pattern=None)
                ],
            NOT_FREELANCER:
                [CallbackQueryHandler(main_menu, pattern='back_to_main_menu')],
            GET_DOCUMENT:
                [
                    MessageHandler(Filters.all, collect_order_data)
                ],
            WAITING_CUSTOMER_MESSAGE:
                [
                    MessageHandler(Filters.text, get_customer_message)
                ],
            WAITING_FREELANCER_MESSAGE:
                [
                    MessageHandler(Filters.text, get_freelancer_message)
                ]
        },
        fallbacks=[
            CommandHandler('rerun', start),
            CommandHandler('start', start)
        ]
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    updater.start_polling()
    updater.idle()
