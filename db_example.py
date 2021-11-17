import datetime
from db_helpers import Warehouses, Boxes, Clients, Storages, Prices, Orders
from db_helpers import get_records, get_records_sql, add_client, add_order


# Таблица, фильтр (опционально). Возвращает список строк, строка словарь
filter = {'title': 'Склад Юг'}
for row in get_records(Warehouses, filter):
    print(row.id, row.title, row.__dict__)

# Весь клиенты
for row in get_records(Clients):
    print(row.id, row.title, row.__dict__)

# Произвольный запрос на выборку
title = 'сноуборд за место'
period = 'неделя'
print(get_records_sql(f"SELECT * FROM v_prices WHERE title = '{title}' AND period = '{period}'"))

""" С прайсом работать через произвольный запрос к view "v_prices":
id	title	period	price	storage_id	storage_title	storage_path
1	4 колеса	месяц	400	2	колёса	сезонные/колёса
2	лыжи за место	месяц	300	3	лыжи	сезонные/лыжи
3	лыжи за место	неделя	100	3	лыжи	сезонные/лыжи
4	велосипед за место	месяц	400	5	велосипед	сезонные/велосипед
5	велосипед за место	неделя	150	5	велосипед	сезонные/велосипед
6	сноуборд за место	месяц	300	4	сноуборд	сезонные/сноуборд
7	сноуборд за место	неделя	100	4	сноуборд	сезонные/сноуборд
8	за 1 кв. метр	месяц	599	6	другое	другое
"""

# Произвольный запрос на выборку
print(get_records_sql('SELECT * FROM v_prices'))

title = 'сноуборд за место'
period = 'неделя'
print(get_records_sql(f"SELECT * FROM v_prices WHERE title = '{title}' AND period = '{period}'"))


"""
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
                'client_id': 2,
                'storage_id': 3,
                'box_id': 12,
                'rent_from': datetime.date(2021, 10, 17),
                'rent_to': datetime.date(2021, 12, 17),
                'description': 'Описание'
                })
)
"""