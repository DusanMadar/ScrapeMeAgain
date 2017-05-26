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

    def create_tables(self):
        """Create tables."""
        self.item_urls_table.__table__.create(self.engine, checkfirst=True)
        self.item_data_table.__table__.create(self.engine, checkfirst=True)

    def commit(self):
        """Commit changes."""
        try:
            self.session.commit()
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

        print(row)
        self.session.add(row)

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
