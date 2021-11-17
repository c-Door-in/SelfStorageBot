import datetime
from db_helpers import Warehouses, Boxes, Clients, Storages, Prices, Orders
from db_helpers import get_records, add_client, add_order


# Таблица, фильтр (опционально). Возвращает список строк, строка словарь
filter = {'title': 'Склад Юг'}
for row in get_records(Warehouses, filter):
    print(row.id, row.title, row.__dict__)

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