import datetime
import os 
from db_helpers import Warehouses, Boxes, Clients, Storages, Prices, Orders
from db_helpers import get_records, get_records_sql, add_client, add_order, generate_qr, add_t_order

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
# print(add_t_order(context_data))

""" Таблица, фильтр (опционально). Возвращает список строк, строка словарь
filter = {'title': 'Склад Юг'}
for row in get_records(Warehouses, filter):
    print(row.id, row.title, row.__dict__)

# Все клиенты
for row in get_records(Clients):
    print(row.id, row.title, row.__dict__)

# Произвольный запрос на выборку
title = 'сноуборд за место'
period = 'неделя'
print(get_records_sql(f"SELECT * FROM v_prices WHERE title = '{title}' AND period = '{period}'"))

# Произвольный запрос на выборку
print(get_records_sql('SELECT * FROM v_prices'))

title = 'сноуборд за место'
period = 'неделя'
print(get_records_sql(f"SELECT * FROM v_prices WHERE title = '{title}' AND period = '{period}'"))

# Генерация qr кода
context_data = {'order_id': 1,
 'order_date': '01.11.2021',
 'order_title': 'Аренда для велосипеда',
 'rent_from': '10.11.2021',
 'rent_to': '10.12.2021',
 'client_fio': 'Иванов Пётр Сидорович'
 }
img = generate_qr(context_data)
img.save(f'qr_{context_data["order_id"]}.png')

# Добавление нового клиента, возвращает id
print(
    add_client({'title': 'Клиент 5',
                'fio': 'Фамилия',
                'phone': '+71234567890',
                'pass_id': '0123456789',
                'birth_date': datetime.date(1995, 10, 25),
                'description': 'Описание'
                })
)

# Добавление нового заказа, возвращает id
print(
    add_order({'title': 'Заказ, 2 велосипеда северный склад',
                'order_date': datetime.date(2021, 9, 15),
                'client_id': 1,
                'price_id': 4,
                'storage_cnt': 2,
                'wrh_id': 4,
                'rent_from': datetime.date(2021, 9, 15),
                'rent_to': datetime.date(2021, 12, 15),
                'description': 'Описание'
                })
)

"""
img = generate_qr({'order_id': 22, 'fio': 'fio'})
img.save(os.path.join(os.getcwd(), "qr", f'qr_{22}.png'))