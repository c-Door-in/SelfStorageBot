import datetime

from sqlalchemy.engine import base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

Base = automap_base()

engine = create_engine(r"sqlite:///SelfStorage.db")

Base.prepare(engine, reflect=True)

Warehouses = Base.classes.warehouses
Boxes = Base.classes.boxes
Clients = Base.classes.clients
Storages = Base.classes.storages
Prices = Base.classes.prices
Orders = Base.classes.orders

session = Session(engine)

def get_records(table, filter={}):
    if filter:
        return session.query(table).filter_by(**filter).all()
    return session.query(table).all()


def get_records_sql(sql):
    recordset = session.execute(sql)
    return([row._asdict() for row in recordset])


def add_client(context_data):
    new_client = Clients(
                    title = context_data['title'],
                    fio = context_data['fio'],
                    phone = context_data['phone'],
                    pass_id = context_data['pass_id'],
                    birth_date = context_data['birth_date'],
                    description = context_data['description'],
                )
    session.add(new_client)
    session.commit()
    return new_client.id


def add_order(context_data):
    new_order = Orders(
                    title = context_data['title'],
                    client_id = context_data['client_id'],
                    storage_id = context_data['storage_id'],
                    box_id = context_data['box_id'],
                    rent_from = context_data['rent_from'],
                    rent_to = context_data['rent_to'],
                    description = context_data['description'],
                )
    session.add(new_order)
    session.commit()
    return new_order.id
