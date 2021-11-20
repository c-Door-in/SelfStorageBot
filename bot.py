import datetime
import logging
import os

from environs import Env
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    LabeledPrice,
    ShippingOption,
    Update,
)
from telegram.ext import (
    Updater,
    Filters,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    CallbackContext,
    ShippingQueryHandler,
)

from db_helpers import (
    Warehouses,
    get_records,
    get_records_sql,
    add_t_order,
    generate_qr,
    make_dates,
    calc_payment,
    last_orders
)

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
logger = logging.getLogger(__name__)


STORES, WHAT_TO_STORE, SEASON_STUFF, CHECK_SEASON_STUFF, OTHER_STUFF, STORAGE_PERIOD, SUMMARY_STUFF = range(7)

PERSONAL_FIO, PERSONAL_PHONENUMBER, PERSONAL_PASSPORT, PERSONAL_BIRTHDATE = range(7, 11)

PAYMENT, COMPLETE = range(11, 13)


def start(update, context):
    # user = get_user(update.message.from_user.id)
    user = update.message.from_user
    context.user_data['user_id'] = user.id
    logger.info("User %s with id %s starts the bot", user.first_name, user.id)
    # if user:
    #     reply_text = 'Приветствую! Вы в главном меню.'
    #     main_menu(update, context, reply_text)
    # else:
    reply_text = (
        'Привет! Я помогу вам арендовать личную ячейку '
        'для хранения вещей. Давайте посмотрим адреса складов, '
        'чтобы выбрать ближайший!'
    )
    main_menu(update, context, reply_text)
    return STORES


def main_menu(update, context, reply_text='Выберите склад'):
    reply_keyboard = [[]]
    for warehouse in get_records(Warehouses):
        reply_keyboard[0].append(warehouse.title)
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
        ),
    )
    return STORES


def check_store(update, context):
    user = update.message.from_user
    logger.info("User %s chooses %s as warehouse", user.first_name, update.message.text)
    for warehouse in get_records(Warehouses):
        if warehouse.title == update.message.text:
            context.user_data['warehouse_title'] = update.message.text
            context.user_data['warehouse_id'] = warehouse.id
            what_to_store(update, context)
            return WHAT_TO_STORE
    reply_text = 'Такого склада нет'
    main_menu(update, context, reply_text)
    # return STORES


def what_to_store(update, context):
    if context.user_data.get('other_stuff'):
        del context.user_data['other_stuff']
    reply_text = 'Что хотите хранить?'
    reply_keyboard = [
        ['Cезонные вещи', 'Другое'],
        ['Назад', 'Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
        ),
    )
    return WHAT_TO_STORE


def season_stuff(update, context):
    user = update.message.from_user
    logger.info("User %s chooses season stuff", user.first_name)
    reply_text = 'Уточните'
    reply_keyboard = [
        ['Лыжи', 'Сноуборд', 'Велосипед', 'Колёса'],
        ['Назад', 'Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
        ),
    )
    return SEASON_STUFF


def check_season_stuff(update, context):
    if update.message.text != 'Назад':
        context.user_data['stuff'] = update.message.text
        user = update.message.from_user
        logger.info("User %s chooses %s to store", user.first_name, update.message.text)
    reply_text = 'Укажите количество'
    reply_keyboard = [
        ['Назад', 'Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
        ),
    )
    return CHECK_SEASON_STUFF


def confirm_season_stuff(update, context):
    user = update.message.from_user
    logger.info("User %s chooses %s things to store", user.first_name, update.message.text)
    context.user_data['stuff_number'] = update.message.text
    stuff_number = int(update.message.text)
    stuff = context.user_data['stuff']
    reply_text = (
        f'Стоимость для {stuff} '
        f'количеством {update.message.text} составит:\n'
    )
    for row in get_records_sql(f'SELECT title, period, price FROM v_prices WHERE storage_title = "{stuff}"'):
        reply_text += (
            f'цена "{row["title"]}" '
            f'на период "{row["period"]}" '
            f'{row["price"]}р., {stuff_number} места {row["price"]*stuff_number}р.\n'
        )
    update.message.reply_text(reply_text)
    storage_period(update, context)
    return STORAGE_PERIOD


def other_stuff(update, context):
    if update.message.text != 'Назад':
        context.user_data['stuff'] = 'Другое'
        user = update.message.from_user
        logger.info("User %s chooses some stuff to store", user.first_name)
    reply_text = (
        'Условия хранения... '
        '1 кв.м. - 599 руб. Каждый дополнительный - 150 руб. '
        'Укажите площадь от 1 до 10 квадратных метров.'
    )
    reply_keyboard = [
        ['1', '2', '3', '4', '5'],
        ['6', '7', '8', '9', '10'],
        ['Назад', 'Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
        ),
    )
    return OTHER_STUFF


def confirm_other_stuff(update, context):
    user = update.message.from_user
    logger.info("User %s chooses %s square meters to store", user.first_name, update.message.text)
    context.user_data['stuff_number'] = update.message.text
    stuff = context.user_data['stuff']
    stuff_number = int(update.message.text)
    reply_text = (
        f'Стоимость для "{stuff}"" '
        f'{update.message.text} кв.м. составит:\n'
    )
    for row in get_records_sql(f'SELECT title, period, price FROM v_prices WHERE storage_title = "{stuff}"'):
        reply_text += (
            f'цена "{row["title"]}" '
            f'на период "{row["period"]}" '
            f'{row["price"]}р., {stuff_number} кв.м. {row["price"]*stuff_number}р.\n'
        )
    '''
    reply_text = (
        f'Показывается стоимость для {update.message.text} '
        f'квадратных метров в месяц.'
    )
    '''
    update.message.reply_text(reply_text)
    storage_period(update, context)
    return STORAGE_PERIOD


def storage_period(update, context):
    reply_text = 'Выберите период хранения'
    reply_keyboard = [
        ['1 месяц', '2 месяца', '3 месяца'],
        ['4 месяца', '5 месяцев', '6 месяцев'],
        ['Назад', 'Главное меню'],
    ]
    if context.user_data['stuff'] in ['Лыжи', 'Сноуборд', 'Велосипед']:
        reply_keyboard.insert(0, ['1 неделя', '2 недели', '3 недели'])
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
        ),
    )
    return STORAGE_PERIOD


def summary_stuff(update, context):
    if update.message.text != 'Назад':
        user = update.message.from_user
        logger.info("User %s chooses %s as storage period", user.first_name, update.message.text)
        context.user_data['period'] = update.message.text
    rent_from, rent_to = make_dates(context.user_data['period'])
    context.user_data['rent_from'] = rent_from
    context.user_data['rent_to'] = rent_to
    stuff = context.user_data['stuff']
    stuff_number = context.user_data['stuff_number']
    period = context.user_data['period']
    order_sum = calc_payment(period, stuff, int(stuff_number))
    context.user_data['order_sum'] = order_sum
    warehouse_title = context.user_data['warehouse_title']
    if context.user_data['stuff'] == 'Другое':
        reply_text = (
            f'Вы бронируете {stuff_number} квадратных метров '
            f'на складе {warehouse_title} на срок {period}\n'
            f'с {rent_from.strftime("%d.%m.%Y")} по {rent_to.strftime("%d.%m.%Y")}\n'
            f'Стоимость составит {order_sum} р.'
        )
    else:
        reply_text = (
            f'Вы бронируете место под {stuff} в количестве {stuff_number} шт. '
            f'на складе "{warehouse_title}" на срок - {period}\n'
            f'с {rent_from.strftime("%d.%m.%Y")} по {rent_to.strftime("%d.%m.%Y")}\n'
            f'Стоимость составит {order_sum} р.'
        )
    reply_keyboard = [
        ['Забронировать'],
        ['Назад', 'Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
        ),
    )
    return SUMMARY_STUFF


def personal_fio(update, context):
    if update.message.text != 'Назад':
        user = update.message.from_user
        logger.info("User %s has confirmed an order", user.first_name)
    reply_text = 'Введите ФИО.'
    reply_keyboard = [
        ['Назад', 'Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            input_field_placeholder='Иванов Иван Иванович',
        ),
    )
    return PERSONAL_FIO


def personal_phonenumber(update, context):
    if update.message.text != 'Назад':
        user = update.message.from_user
        logger.info("User %s's full name is '%s'", user.first_name, update.message.text)
        context.user_data['fio'] = update.message.text
    reply_text = 'Введите номер телефона.'
    reply_keyboard = [
        ['Назад', 'Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            input_field_placeholder='987 654 3210',
        ),
    )
    return PERSONAL_PHONENUMBER


def personal_passport(update, context):
    if update.message.text != 'Назад':
        user = update.message.from_user
        logger.info("User %s's phone is '%s'", user.first_name, update.message.text)
        context.user_data['phone'] = update.message.text
    reply_text = 'Введите серию и номер паспорта.'
    reply_keyboard = [
        ['Назад', 'Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            input_field_placeholder='1234 567890',
        ),
    )
    return PERSONAL_PASSPORT


def personal_birthdate(update, context):
    if update.message.text != 'Назад':
        user = update.message.from_user
        logger.info("User %s's pass_id is '%s'", user.first_name, update.message.text)
        context.user_data['pass_id'] = update.message.text
    reply_text = 'Введите дату рождения.'
    reply_keyboard = [
        ['Назад', 'Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            input_field_placeholder='дд.мм.гггг',
        ),
    )
    return PERSONAL_BIRTHDATE


def payment(update, context):
    if update.message.text != 'Назад':
        user = update.message.from_user
        logger.info("User %s's birth_date is '%s'", user.first_name, update.message.text)
        context.user_data['birth_date'] = update.message.text
    order_sum = context.user_data['order_sum']
    reply_text = f'К оплате {order_sum} р.'
    reply_keyboard = [
        ['Оплатить'],
        ['Назад', 'Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
        ),
    )
    return PAYMENT


def start_without_shipping_callback(update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id
    title = "Payment Example"
    description = "Оплата заказа номер"
    payload = "Custom-Payload"
    provider_token = SBER_TEST_TOKEN
    currency = "RUB"
    price = int(context.user_data['order_sum'])
    prices = [LabeledPrice("Test", price * 100)]

    logger.info("User %s's starts payment callback", user.first_name)

    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )
    return PAYMENT


def precheckout_callback(update, context):
    query = update.pre_checkout_query
    logger.info("Payload %s - precheckout_callback", query.invoice_payload)
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)
    return PAYMENT


def complete(update, context):
    user = update.message.from_user
    logger.info("User %s made a payment for %s rubles", user.first_name, context.user_data['order_sum'])
    birth_date = context.user_data['birth_date'].split('.')
    context_data = {
    'order_date': datetime.datetime.now(),
    'order_sum': context.user_data['order_sum'],
    'user_id': user.id,
    'warehouse_id': context.user_data['warehouse_id'],
    'warehouse_title': context.user_data['warehouse_title'],
    'stuff': context.user_data['stuff'],
    'stuff_number': context.user_data['stuff_number'],
    'fio': context.user_data['fio'],
    'phone': context.user_data['phone'],
    'pass_id': context.user_data['pass_id'],
    'birth_date': datetime.date(int(birth_date[2]), int(birth_date[1]), int(birth_date[0])),
    'rent_from': context.user_data['rent_from'],
    'rent_to': context.user_data['rent_to']
    }
    order_id = add_t_order(context_data)
    context.user_data['order_id'] = order_id
    img = generate_qr({'order_id': order_id, 'fio': context_data['fio']})
    folder = os.path.join(os.getcwd(), "qr")
    os.makedirs(folder, exist_ok=True)
    qr_name = os.path.join(folder, f'qr_{order_id}.png')
    img.save(qr_name)
    update.message.reply_photo(open(qr_name, 'rb'))
    rent_from = context.user_data['rent_from'].strftime('%d.%m.%Y')
    rent_to = context.user_data['rent_to'].strftime('%d.%m.%Y')

    reply_text = (
        'Спасибо за бронирование, оплата принята.\n'
        f'Номер Вашего заказа #{order_id}. \n'
        'Вот ваш электронный ключ для доступа к вашему личному складу. '
        'Вы сможете попасть на склад в любое время в '
        f'период с {rent_from} по {rent_to}\n'
        'Ваши предыдущие 3 заказа:\n'
    )
    reply_text += last_orders(user.id)
    reply_keyboard = [
        ['Главное меню'],
    ]
    update.message.reply_text(
        reply_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
        ),
    )
    return ConversationHandler.END


def incorrect_input(update, context):
    update.message.reply_text(
        'Я вас не понимаю \U0001F61F\n\n'
        'Пожалуйста, воспользуйтесь кнопками в нижнем меню.\n'
        'Если они у вас не отображаются, просто нажмите на эту\n'
        'кнопку в поле ввода:'
    )
    with open('pointer.jpeg', 'rb') as pointer_file:
        update.message.reply_photo(pointer_file)


def exit(update, _):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Всего доброго!',
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main():
    TG_BOT_TOKEN = env('TG_BOT_TOKEN_WORK') if DEBUG else env('TG_BOT_TOKEN')

    updater = Updater(token=TG_BOT_TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            STORES: [
                MessageHandler(Filters.text, check_store),
            ],
            WHAT_TO_STORE: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), start),
                MessageHandler(Filters.regex('^Cезонные вещи$'), season_stuff),
                MessageHandler(Filters.regex('^Другое$'), other_stuff),
                MessageHandler(Filters.text, incorrect_input),
            ],
            SEASON_STUFF: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), what_to_store),
                MessageHandler(Filters.regex('^Лыжи|Сноуборд|Велосипед|Колёса$'), check_season_stuff),
                MessageHandler(Filters.text, incorrect_input),
            ],
            CHECK_SEASON_STUFF: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), season_stuff),
                MessageHandler(Filters.regex('^\d{1,3}$'), confirm_season_stuff),
            ],
            OTHER_STUFF: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), what_to_store),
                MessageHandler(Filters.regex('^([1-9]|10)$'), confirm_other_stuff),
            ],
            STORAGE_PERIOD: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), what_to_store),
                MessageHandler(Filters.regex('^(1\s(месяц|неделя))|([2-6]\s(месяц(а|(ев)))|(недел[иь]))$'), summary_stuff),
                MessageHandler(Filters.text, incorrect_input),
            ],
            SUMMARY_STUFF: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), storage_period),
                MessageHandler(Filters.regex('^Забронировать$'), personal_fio),
                MessageHandler(Filters.text, incorrect_input),
            ],
            PERSONAL_FIO: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), summary_stuff),
                MessageHandler(Filters.text, personal_phonenumber),
            ],
            PERSONAL_PHONENUMBER: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), personal_fio),
                MessageHandler(Filters.text, personal_passport),
            ],
            PERSONAL_PASSPORT: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), personal_phonenumber),
                MessageHandler(Filters.text, personal_birthdate),
            ],
            PERSONAL_BIRTHDATE: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), personal_passport),
                MessageHandler(
                    Filters.regex('^(0?[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])(\.((19)|(20))?\d{2})?$'),
                    payment,
                ),
            ],
            PAYMENT: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), personal_passport),
                MessageHandler(Filters.regex('^Оплатить$'), start_without_shipping_callback),
                # MessageHandler(Filters.regex('^Оплатить$'), complete),
                PreCheckoutQueryHandler(precheckout_callback),
                MessageHandler(Filters.successful_payment, complete),
                MessageHandler(Filters.text, incorrect_input),
            ],
            COMPLETE: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), personal_passport),
                MessageHandler(Filters.text, exit),
            ],
        },
        fallbacks=[CommandHandler('exit', exit)],
        name="my_conversation",
        allow_reentry=True
    )

    dispatcher.add_handler(conv_handler)

    # dispatcher.add_handler(CommandHandler("noshipping", start_without_shipping_callback))

    # Pre-checkout handler to final check
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    # # Success! Notify your user!
    # dispatcher.add_handler(MessageHandler(Filters.successful_payment, complete))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    env = Env()
    env.read_env()

    DEBUG = env.bool('DEBUG', False)

    SBER_TEST_TOKEN = env('SBER_TEST_TOKEN_WORK') if DEBUG else env('SBER_TEST_TOKEN')
    main()
