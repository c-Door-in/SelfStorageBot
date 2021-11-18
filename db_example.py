import datetime

from db_helpers import Warehouses, Boxes, Clients, Storages, Prices, Orders
from db_helpers import get_records, get_records_sql, add_client, add_order



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

''' С прайсом работать через произвольный запрос к view "v_prices":
id	title	period	price	storage_id	storage_title	storage_path
1	4 колеса	месяц	400	2	колёса	сезонные/колёса
2	лыжи за место	месяц	300	3	лыжи	сезонные/лыжи
3	лыжи за место	неделя	100	3	лыжи	сезонные/лыжи
4	велосипед за место	месяц	400	5	велосипед	сезонные/велосипед
5	велосипед за место	неделя	150	5	велосипед	сезонные/велосипед
6	сноуборд за место	месяц	300	4	сноуборд	сезонные/сноуборд
7	сноуборд за место	неделя	100	4	сноуборд	сезонные/сноуборд
8	за 1 кв. метр	месяц	599	6	другое	другое
'''

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
    add_order({'title': 'Заказ важный',
                'order_date': datetime.date(2021, 10, 1),
                'client_id': 2,
                'storage_id': 3,
                'wrh_id': 1,
                'rent_from': datetime.date(2021, 10, 17),
                'rent_to': datetime.date(2021, 12, 17),
                'description': 'Описание'
                })
)
"""
print(
    add_order({'title': 'Заказ важный',
                'order_date': datetime.date(2021, 10, 1),
                'client_id': 2,
                'storage_id': 3,
                'storage_cnt': 4,
                'wrh_id': 1,
                'rent_from': datetime.date(2021, 10, 17),
                'rent_to': datetime.date(2021, 12, 17),
                'description': 'Описание'
                })
)