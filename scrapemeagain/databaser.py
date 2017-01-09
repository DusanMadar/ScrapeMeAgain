# -*- coding: utf-8 -*-


"""Shared database operations"""


import os
import logging

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_, or_, distinct

from models import UrlsTable, GeocodedTable
from util.addresser import comparable_address
from util.alphanumericker import iterable_to_string
from util.configparser import get_data_directory, get_ungeocoded_coordinate


#:
data_dir = get_data_directory()
ungeocoded_coordinate = get_ungeocoded_coordinate()


class Databaser(object):
    def __init__(self, db_file):
        """Database manipulation class

        :argument db_file: database file name
        :type db_file: str
        :argument db_table: SAQAlchemy table
        :type db_table:

        """
        self.db_file = os.path.join(data_dir, db_file + '.sqlite')
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

    def commit(self):
        """Commit changes"""
        try:
            self.session.commit()
            logging.critical('Changes successfully committed')
        except:
            logging.exception('Failed to commit changes, rolling back ...')
            self.session.rollback()

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
                value = value.decode('utf-8')

            setattr(row, key, value)

        self.session.add(row)

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

    def create_index(self, column_name):
        """Create index for given column

        :argument column_name: column name
        :type column_name: str

        """
        index_name = 'idx_{t}_{c}'.format(t=self.table.__tablename__,
                                          c=column_name)

        # make sure the index is removed before creating new
        sql = 'DROP INDEX IF EXISTS {i}'.format(i=index_name)
        self.engine.execute(sql)

        sql = ('CREATE INDEX {i} ON {t} ({c})'
               .format(i=index_name, t=self.table.__tablename__, c=column_name))
        self.engine.execute(sql)


class AdsDatabaser(Databaser):
    def __init__(self, db_file, db_table):
        super(AdsDatabaser, self).__init__(db_file)

        self.table = self.create_table(db_table)
        self.urls = self.create_table(UrlsTable)

    def update(self, data):
        """Update an ad database record

        :argument data: updated ad data
        :type data: dict

        """
        _filter = self.table.ad_id == data['ad_id']
        query = self.session.query(self.table).filter(_filter)
        query.update(data)

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

        :returns Query object

        """
        return (self.session.query(self.table.district,
                                   self.table.city,
                                   self.table.locality)
                            .filter(self.table.latitude == None,
                                    self.table.city != None)
                            .group_by(self.table.district,
                                      self.table.city,
                                      self.table.locality))  # NOQA

    def update_location_data(self):
        """Update ad location data based on geocoded localizations"""
        transaction_items = 0
        g_dbsr = GeoDatabaser()

        # yeah, I know - it is slow [to loop over like this]
        for addr_cmps in self.to_geocode():
            matched_address = None
            cmprbl_addr = comparable_address(addr_cmps)

            _filter = g_dbsr.table.valid_for.like('%' + cmprbl_addr + '%')
            data = g_dbsr.session.query(g_dbsr.table.country,
                                        g_dbsr.table.region,
                                        g_dbsr.table.district,
                                        g_dbsr.table.city,
                                        g_dbsr.table.locality,
                                        g_dbsr.table.latitude,
                                        g_dbsr.table.longitude,
                                        g_dbsr.table.valid_for
                                        ).filter(_filter)

            addresses_count = data.count()
            if addresses_count == 1:
                matched_address = data.one()
            elif addresses_count > 1:
                for possible_addr in data:
                    if cmprbl_addr in possible_addr.valid_for.split('|'):
                        matched_address = possible_addr
                        break

            if matched_address is None:
                address = iterable_to_string(addr_cmps)
                logging.debug('No coordinates for address: %s' % address)
                continue

            location_data = {'country': matched_address.country,
                             'region': matched_address.region,
                             'district': matched_address.district,
                             'city': matched_address.city,
                             'locality': matched_address.locality,
                             'latitude': matched_address.latitude,
                             'longitude': matched_address.longitude,
                             'location_id': matched_address.ID}

            _filter = and_(self.table.district == addr_cmps[0],
                           self.table.city == addr_cmps[1],
                           self.table.locality == addr_cmps[2])
            query = self.session.query(self.table).filter(_filter)

            query.update(location_data)

            transaction_items += 1
            if transaction_items > 1000:
                transaction_items = 0
                self.commit()

        self.commit()

    def _urls_remove_duplicate(self):
        """Remove duplicate URLs"""
        raw_sql = ('DELETE '
                   'FROM {table} '
                   'WHERE {id} IN (SELECT MAX({id}) '
                                  'FROM {table} '
                                  'GROUP BY {url} '
                                  'HAVING count(*) > 1)'
                    .format(id=self.urls.ID.key,
                            url=self.urls.url.key,
                            table=self.urls.__tablename__))  # NOQA

        self.engine.execute(raw_sql)

    def urls_get_all(self):
        """Get all URLs for scraping ordered from newest to oldest

        :returns list

        """
        self._urls_remove_duplicate()

        order_by = self.urls.ID.desc()
        query = self.session.query(self.urls.url).order_by(order_by)

        return query.all()


class GeoDatabaser(Databaser):
    def __init__(self):
        super(GeoDatabaser, self).__init__(db_file='geocodingcache')

        self.table = self.create_table(GeocodedTable)

    def is_stored(self, addr_cmps, return_location=False):
        """Check if address is already in the database

        :argument addr_cmps: address components
        :type addr_cmps: tuple
        :argument return_location: flag to return location data
        :type return_location: bool

        :returns bool or (Query or None)

        """
        location = None
        is_stored = False

        cmprbl_addr = comparable_address(addr_cmps)

        _filter = self.table.valid_for.like('%' + cmprbl_addr + '%')
        query = self.session.query(self.table).filter(_filter)

        if query:
            for possible_addr in query:
                if cmprbl_addr in possible_addr.valid_for.split('|'):
                    location = possible_addr
                    is_stored = True
                    break

        if return_location:
            return location
        else:
            return is_stored

    def get_incomplete_records(self):
        """Get a list of coordinates for incomplete records, i.e. for records
        where country or region or district is missing

        :returns list

        """
        filter1 = or_(self.table.country == None,
                      self.table.region == None,
                      self.table.district == None)  # NOQA
        filter2 = self.table.latitude != ungeocoded_coordinate

        return (self.session.query(self.table.latitude, self.table.longitude)
                            .filter(filter1, filter2)
                            .all())

    def complete_record(self, data):
        """Add missing data to an incomplete record

        :argument data: updated data
        :type data: dict

        """
        _filter = and_(self.table.latitude == data['latitude'],
                       self.table.longitude == data['longitude'])
        query = self.session.query(self.table).filter(_filter)
        query.update(data)

    def update_record_from_self(self):
        """Update 'country' and 'region' from another record if possible"""
        filter1 = or_(self.table.region == None,
                      self.table.country == None)  # NOQA

        incomplete = (self.session.query(distinct(self.table.district))
                                  .filter(filter1)
                                  .all())

        # probably can be done without looping, but can't figure how
        # http://stackoverflow.com/questions/11790595/sqlite-inner-join-update-
        # using-values-from-another-table/12099738#12099738
        for district in incomplete:
            district = district[0]

            filter2 = and_(self.table.district == district,
                           self.table.region != None,
                           self.table.country != None)  # NOQA

            matched_record = (self.session.query(self.table.region,
                                                 self.table.country)
                                          .filter(filter2)
                                          .first())

            if matched_record is None:
                continue

            data = {'region': matched_record.region,
                    'country': matched_record.country}

            filter3 = and_(filter1,
                           self.table.district == district)

            self.session.query(self.table).filter(filter3).update(data)

        self.commit()
