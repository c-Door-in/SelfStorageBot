import datetime
import logging
import os

from environs import Env
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    Filters,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
)

from db_helpers import Warehouses, Boxes, Clients, Storages, Prices, Orders
from db_helpers import get_records, add_client, add_order, add_t_order, generate_qr


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


def main_menu(update, context, reply_text='Вы в главном меню'):
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
        ['Лыжи', 'Сноуборд', 'Велосипед', 'Колеса'],
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
    stuff = context.user_data['stuff']
    reply_text = (
        f'Показывается стоимость для {stuff} '
        f'количеством {update.message.text}.'
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
    reply_text = (
        f'Показывается стоимость для {update.message.text} '
        f'квадратных метров в месяц.'
    )
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
    stuff = context.user_data['stuff']
    stuff_number = context.user_data['stuff_number']
    period = context.user_data['period']
    warehouse_title = context.user_data['warehouse_title']
    if context.user_data['stuff'] == 'Другое':
        reply_text = (
            f'Вы бронируете {stuff_number} квадратных метров '
            f'на складе {warehouse_title} на срок {period}.\n'
            f'Стоимость ...'
        )
    else:
        reply_text = (
            f'Вы бронируете место под {stuff} в количестве {stuff_number} шт. '
            f'на складе "{warehouse_title}" на срок - {period}.\n'
            f'Стоимость ...'
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
    reply_text = 'К оплате ...'
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


def complete(update, context):
    user = update.message.from_user
    logger.info("User %s's birth_date is '%s'", user.first_name, update.message.text)
    
    # TODO Подбить заказ и отправить в базу. context.user_data
    # собрать context.user_data по соответствию типам    
    context_data = {
    'user_id': 706609141,
    'current_warehouse': 'Склад Юг',
    'current_season_stuff': 'Лыжи',
    'current_season_stuff_number': 3,
    'fio': 'Петров',
    'phone': '9899898989',
    'pass_id': '5555555555',
    'birth_date': datetime.date(1995, 10, 25)
    }
    order_id = add_t_order(context_data)

    # TODO update.message.reply_photo() Выложить QR-код
    img = generate_qr({'order_id': order_id, 'fio': context_data['fio']})
    qr_name = os.path.join(os.getcwd(), 'qr', f'qr_{order_id}.png') 
    img.save(qr_name)
    update.message.reply_photo(open(qr_name, 'rb'))
    # TODO Задать переменные для периода start_date, finish_date
    reply_text = (
        'Спасибо за бронирование, оплата принята.\n'
        'Вот ваш электронный ключ для доступа к вашему личному складу. '
        'Вы сможете попасть на склад в любое время в период с по'
    )
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
    env = Env()
    env.read_env()

    DEBUG = env.bool('DEBUG', False)

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
                MessageHandler(Filters.regex('^Лыжи|Сноуборд|Велосипед|Колеса$'), check_season_stuff),
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
                MessageHandler(Filters.regex('^([1-9]|10)$'), storage_period),
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
                    Filters.regex('^(0?[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])(\.(20)?\d{2})?$'),
                    payment,
                ),
            ],
            PAYMENT: [
                MessageHandler(Filters.regex('^Главное меню$'), main_menu),
                MessageHandler(Filters.regex('^Назад$'), personal_passport),
                MessageHandler(Filters.regex('^Оплатить$'), complete),
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

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
