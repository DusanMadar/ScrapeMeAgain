#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Shared database operations"""


import os

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, event

from util.configparser import get_data_directory


#:
data_dir = get_data_directory()


@event.listens_for(Engine, "connect")
def _synchronous_pragma_on_connect(engine, _):
    """Do not wait till the data are stored to disk on each commit"""
    engine.execute('pragma synchronous=OFF')


class Databaser(object):
    def __init__(self, db_file):
        """Database manipulation class

        :argument db_file:
        :type db_file:
        :argument db_table: SAQAlchemy table
        :type db_table:

        """
        self.db_file = os.path.join(data_dir, db_file)
        if not os.path.exists(self.db_file):
            with open(self.db_file, 'w'):
                pass

        self.engine = create_engine('sqlite:///%s' % self.db_file)

        session_maker = sessionmaker(bind=self.engine)
        self.session = session_maker()

        # main databaser table - should be overridden in __init__
        self.table = None

    def create_table(self, db_table):
        """Create table"""
        db_table.__table__.create(self.engine, checkfirst=True)
        return db_table

    def insert(self, data, table=None):
        """Insert

        :argument data: collected data
        :type data: dict
        :argument table:
        :type table:

        """
        if table is None:
            table = self.table

        row = table()
        for key, value in data.items():
            if isinstance(value, str):
                value = unicode(value)

            setattr(row, key, value)

        self.session.add(row)
        self.session.commit()

    def insert_multiple(self, data, table=None):
        """Insert multiple

        :argument data: collected data
        :type data: list of dicts
        :argument table:
        :type table:

        """
        if table is None:
            table = self.table

        for index, item in enumerate(data):
            row = table()
            for key, value in item.items():
                setattr(row, key, value)

            data[index] = row

        self.session.add_all(data)
        self.session.commit()

    def delete(self, id_, table=None):
        """Delete

        :argument id_: ID to look for
        :type id_: int
        :argument table:
        :type table:

        """
        if table is None:
            table = self.table

        query = self.session.query(table).filter(table.ad_id == id_)
        query.delete()
        self.session.commit()


class AdsDatabaser(Databaser):
    def __init__(self, db_file, db_table):
        super(AdsDatabaser, self).__init__(db_file)

        self.table = self.create_table(db_table)

    def update(self, data):
        """Update an ad database record

        :argument data: updated ad data
        :type data: dict

        """
        _filter = self.table.ad_id == data['ad_id']
        query = self.session.query(self.table).filter(_filter)
        query.update(data)
        self.session.commit()

    def is_stored(self, ad_id):
        """Check if ad is already in the database

        :argument ad_id: ad page ID
        :type ad_id: int

        :returns bool

        """
        _filter = self.table.ad_id == ad_id
        query = self.session.query(self.table).filter(_filter)

        return self.session.query(query.exists()).scalar()

    def get_timestamp(self, ad_id):
        """Get stored ad time-stamp

        :argument ad_id: ad page ID
        :type ad_id: int

        :returns datetime instance

        """
        _filter = self.table.ad_id == ad_id
        query = self.session.query(self.table.last_update).filter(_filter)

        return query.scalar()

    def to_geocode(self):
        """Select records for geocoding (i.e. those without coordinates)

        :returns list

        """
        return [row for row in
                self.session.query(self.table.district,
                                   self.table.city,
                                   self.table.locality)
                            .filter(self.table.lat == None,
                                    self.table.city != None)  # NOQA
                            .group_by(self.table.district,
                                      self.table.city,
                                      self.table.locality)]
