#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WGS-84 latitude and longitude to a 2D Spatialite geometry (Point) column"""


import os
import sys
import sqlite3
import argparse


def sql2spatial(database, table, latitude, longitude, extension, geometry,
                synchronous=False, rename=False):
    """Add a geometry (Point) column in WGS-84 and all Spatialite required stuff

    :argument database: path to SQLite database to be spatially enabled
    :type database: str
    :argument table: name of the table containing latitude and longitude data
    :type table: str
    :argument latitude: name of the column containing latitude data
    :type latitude: str
    :argument longitude: name of the column containing longitude data
    :type longitude: str
    :argument extension: path to the SQLite spatial extension
    :type extension: str
    :argument geometry: name of the new geometry column
    :type geometry: str
    :argument synchronous: flag to use FULL synchronous pragma
    :type synchronous: bool
    :argument rename: flag to change file extension to 'spatialite'
    :type rename: bool

    """
    if not os.path.exists(database):
        print 'File "%s" does not exists' % database
        sys.exit()
    else:
        db_engine = sqlite3.connect(database)
        print 'Working with database "%s"' % database

    try:
        db_engine.enable_load_extension(True)
        db_engine.load_extension(extension)
        print 'Using spatial extension "%s"' % extension
    except:
        print 'Failed to load spatial extension "%s"' % extension
        raise

    with db_engine:
        cursor = db_engine.cursor()

        # turn off disk synchronization - the process is very slow otherwise
        if not synchronous:
            cursor.execute('PRAGMA synchronous=0;')
            print 'Disk synchronization mode is set to "OFF"'
        else:
            cursor.execute('PRAGMA synchronous=2;')
            print 'Disk synchronization mode is set to "FULL"'

        # create everything required by SpatiaLite
        init_spatial = cursor.execute('SELECT InitSpatialMetadata();')
        init_spatial_status = int(init_spatial.fetchone()[0])
        if init_spatial_status == 0:
            print 'Failed to spatially initialize database'
            sys.exit()
        else:
            print 'Database spatially initialized'

        # add a 2D geometry (Point) column
        add_geometry_sql = ('Select AddGeometryColumn ("{table}", "{column}", '
                            '4326, "POINT", 2);'.format(table=table,
                                                        column=geometry))
        add_geometry = cursor.execute(add_geometry_sql)
        add_geometry_status = add_geometry.fetchone()[0]
        if add_geometry_status == 0:
            print 'Failed to add geometry (Point) column'
            sys.exit()
        else:
            print 'Added geometry (Point) column "%s"' % geometry

        # set point values (latitude and longitude)
        try:
            make_point_sql = ('UPDATE {table} SET '
                              'Geometry=MakePoint({longitude}, {latitude}, '
                              '4326);'.format(table=table,
                                              latitude=latitude,
                                              longitude=longitude))
            cursor.execute(make_point_sql)
            print 'Updated values for geometry (Point) column "%s"' % geometry
        except Exception as exc:
            print 'Failed to update values for geometry (Point) column'
            print exc
            sys.exit()

    if rename:
        try:
            file_name, _ = os.path.splitext(database)
            os.rename(database, file_name + '.spatialite')
            print 'Database file extension updated'
        except Exception as exc:
            print 'Failed to update database file extension'
            print exc
            sys.exit()

    print 'DONE!'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # default values
    default_geometry_column = 'geometry'
    default_latitude_column = 'latitude'
    default_longitude_column = 'longitude'
    default_extension = '/usr/local/lib/mod_spatialite.so'

    # database, table
    parser.add_argument('-d', '--database', required=True,
                        help='Path to SQLite database to be spatially enabled')
    parser.add_argument('-t', '--table', required=True,
                        help='Name of the table with latitude and longitude')

    # column options
    parser.add_argument('-l', '--latitude', default=default_latitude_column,
                        help='Name of the column containing latitude data, '
                             'defaults to "%s"' % default_latitude_column)
    parser.add_argument('-n', '--longitude', default=default_longitude_column,
                        help='Name of the column containing longitude data, '
                             'defaults to "%s"' % default_longitude_column)

    # spatial options
    parser.add_argument('-g', '--geometry', default=default_geometry_column,
                        help='Name of the new geometry column, defaults '
                             'to "%s"' % default_geometry_column)
    parser.add_argument('-e', '--extension', default=default_extension,
                        help='Path to the SQLite spatial extension, defaults '
                             'to "%s"' % default_extension)

    # SQLite option
    parser.add_argument('-s', '--synchronous', action='store_true',
                        default=False,
                        help='Flag to use FULL synchronous pragma')

    parser.add_argument('-r', '--rename', action='store_false',
                        default=True,
                        help='Flag not to change extension to `spatialite`')

    args = parser.parse_args()
    sql2spatial(database=args.database, table=args.table,
                latitude=args.latitude, longitude=args.longitude,
                extension=args.extension, geometry=args.geometry,
                synchronous=args.synchronous, rename=args.rename)
