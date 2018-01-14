"""Common database functionality."""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Config
from .scrapers.basemodel import ItemUrlsTable


class Databaser(object):
    def __init__(self, db_file, db_table):
        """Database manipulation class.

        :argument db_file: SQLite database file path
        :type db_file: str

        """
        # Ensure data dir exists.
        if not os.path.exists(Config.DATA_DIRECTORY):
            os.makedirs(Config.DATA_DIRECTORY)

        self.db_file = os.path.join(Config.DATA_DIRECTORY, db_file) + '.sqlite'
        if not os.path.exists(self.db_file):
            with open(self.db_file, 'w'):
                pass

        self.engine = create_engine('sqlite:///{}'.format(self.db_file))

        session_maker = sessionmaker(bind=self.engine)
        self.session = session_maker()

        self.item_urls_table = ItemUrlsTable
        self.item_data_table = db_table

        self.create_tables()

        self.transaction_items = 0
        self.transaction_items_max = Config.TRANSACTION_SIZE

    def create_tables(self):
        """Create tables."""
        self.item_urls_table.__table__.create(self.engine, checkfirst=True)
        self.item_data_table.__table__.create(self.engine, checkfirst=True)

    def commit(self):
        """Commit changes."""
        try:
            self.session.commit()
            self.transaction_items = 0
            logging.info('Changes successfully committed')
        except Exception as exc:
            logging.error('Failed to commit changes, rolling back ...')
            logging.exception(exc)
            self.session.rollback()

    def insert(self, data, table):
        """Insert.

        :argument data:
        :type data: dict
        :argument table: table reference
        :type table: SQLAlchemy table

        """
        row = table()
        for key, value in data.items():
            setattr(row, key, value)

        self.session.add(row)

        self.transaction_items += 1
        if self.transaction_items > self.transaction_items_max:
            self.databaser.commit()

    def insert_multiple(self, data, table):
        """Insert multiple.

        :argument data:
        :type data: list of dicts
        :argument table: table reference
        :type table: SQLAlchemy table

        """
        for item in data:
            self.insert(item, table)

    def delete_url(self, url):
        """Delete url.

        :argument url:
        :type url: str
        :argument table: table reference
        :type table: SQLAlchemy table

        """
        self.session.query(
            self.item_urls_table
        ).filter(
            self.item_urls_table.url == url
        ).delete()

        self.transaction_items += 1

    def _remove_duplicate_item_urls(self):
        """Remove duplicate item URLs."""
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
            table=self.item_urls_table.__tablename__
        ).strip()

        self.engine.execute(raw_sql)

    def get_item_urls(self):
        """Get item URLs for scraping ordered from newest to oldest.

        :returns query object
        """
        self._remove_duplicate_item_urls()

        return self.session.query(
            self.item_urls_table.url
        ).order_by(
            self.item_urls_table.id.desc()
        )
