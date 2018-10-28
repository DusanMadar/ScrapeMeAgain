"""
Common database functionality.
"""


import logging
import os
import socket

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scrapemeagain.config import Config
from scrapemeagain.dockerized.apps.datastore import client as datastore_client
from scrapemeagain.scrapers.basemodel import ItemUrlsTable


class BaseDatabaser:
    def __init__(self, db_name, data_table):
        """
        Database manipulation class.

        :argument db_name: SQLite database file name (without extension)
        :type db_name: str
        :argument data_table: table to store item data in
        :type data_table: SQLAlchemy table
        """
        self.db_name = db_name

        self.item_data_table = data_table
        self.item_urls_table = ItemUrlsTable

        self.transaction_items = 0
        self.transaction_items_max = Config.TRANSACTION_SIZE

        self.engine = self.create_engine()
        self.session = sessionmaker(bind=self.engine)()

    def create_engine(self):
        """
        Create an SQLite database engine.
        """
        # Ensure data dir exists.
        if not os.path.exists(Config.DATA_DIRECTORY):
            os.makedirs(Config.DATA_DIRECTORY)

        db = os.path.join(Config.DATA_DIRECTORY, self.db_name) + ".sqlite"
        if not os.path.exists(db):
            with open(db, "w"):
                pass

        return create_engine("sqlite:///{}".format(db))

    def create_tables(self, create_urls_table=True, create_data_table=True):
        """
        Create tables.
        """
        if create_urls_table:
            self.item_urls_table.__table__.create(self.engine, checkfirst=True)

        if create_data_table:
            self.item_data_table.__table__.create(self.engine, checkfirst=True)

    def commit(self):
        """
        Commit changes.
        """
        try:
            self.session.commit()
            self.transaction_items = 0
            logging.info("Changes successfully committed")
        except Exception as exc:
            logging.error("Failed to commit changes, rolling back ...")
            logging.exception(exc)
            self.session.rollback()

    def manage_transaction(self):
        """
        Manage transaction, i.e. decide when to commit.
        """
        self.transaction_items += 1
        if self.transaction_items > self.transaction_items_max:
            self.commit()

    def _actually_insert(self, data, table):
        """
        Insert data to table.

        :argument data:
        :type data: dict
        :argument table: table reference
        :type table: SQLAlchemy table
        """
        row = table()
        for key, value in data.items():
            setattr(row, key, value)

        self.session.add(row)

    def insert(self, data, table):
        """
        Insert a single data unit and manage the transaction size.
        """
        self._actually_insert(data, table)
        self.manage_transaction()

    def insert_multiple(self, data, table):
        """
        Insert multiple data units.

        :argument data:
        :type data: list of dicts
        :argument table: table reference
        :type table: SQLAlchemy table
        """
        for item in data:
            self.insert(item, table)

    def delete_url(self, url):
        """
        Delete item URL.

        :argument url:
        :type url: str
        """
        self.session.query(self.item_urls_table).filter(
            self.item_urls_table.url == url
        ).delete()

        self.transaction_items += 1

    def _remove_duplicate_item_urls(self):
        """
        Remove duplicate item URLs.
        """
        raw_sql = """
            DELETE
            FROM {table}
            WHERE {id} IN (
                SELECT MAX({id})
                FROM {table}
                GROUP BY {url}
                HAVING COUNT(*) > 1
            )
        """.format(
            id=self.item_urls_table.id.key,
            url=self.item_urls_table.url.key,
            table=self.item_urls_table.__tablename__,
        ).strip()

        self.engine.execute(raw_sql)

    def get_item_urls(self):
        """
        Get item URLs for scraping ordered from newest to oldest.

        :returns query object
        """
        self._remove_duplicate_item_urls()

        return self.session.query(self.item_urls_table.url).order_by(
            self.item_urls_table.id.desc()
        )


class Databaser(BaseDatabaser):
    def __init__(self, db_name, data_table):
        super().__init__(db_name, data_table)
        self.create_tables()


class DataOnlyDatabaser(BaseDatabaser):
    """
    Store item data only.

    Instance of this class will have tables set as follows:
        self.item_data_table = data_table
        self.item_urls_table = None
    """

    def __init__(self, db_name, data_table):
        super().__init__(db_name, data_table)
        self.item_urls_table = None
        self.create_tables(create_urls_table=False)

    def insert(self, data):
        super().insert(data, self.item_data_table)


class UrlsOnlyDatabaser(BaseDatabaser):
    """
    Store item URLs only.

    Instance of this class will have tables set as follows:
        self.item_data_table = None
        self.item_urls_table = ItemUrlsTable
    """

    def __init__(self, db_name):
        super().__init__(db_name, None)
        self.create_tables(create_data_table=False)


class DataStoreDatabaser(DataOnlyDatabaser):
    """
    A data only databaser intended to used as the `datastore` app DB backend.
    """

    def deserialize_data(self, data):
        """
        Update the serialized `data` dict to match the DB schema and return it.
        """
        return data

    def insert(self, data):
        data = self.deserialize_data(data)
        super().insert(data)


class DockerizedDatabaser(UrlsOnlyDatabaser):
    """
    A hybrid Databaser which stores item URLs locally but item data remotely.

    This is the databaser class each dockerized scraped should use/subclass.
    """

    def __init__(self, db_name):
        super().__init__("{0}_{1}".format(db_name, socket.gethostname()))

    def serialize_data(self, data):
        """
        Update the raw `data` dict to be JSON serializable and return it.
        """
        return data

    def insert(self, data, table):
        if table is None:
            # Store item data remotely
            # (`self.item_data_table = None` as we are a `UrlsOnlyDatabaser`).
            data = self.serialize_data(data)
            datastore_client.insert_data(data)
        else:
            # Store item URLs locally.
            super()._actually_insert(data, table)

        self.manage_transaction()

    def commit(self):
        datastore_client.commit()
        super().commit()
