# -*- coding: utf-8 -*-


"""SQLAlchemy database tables definition"""


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Float, Integer, String


Base = declarative_base()


class GeocodedTable(Base):
    """Geocoded table structure"""
    __tablename__ = 'geocoded'

    ID = Column(Integer, primary_key=True)
    country = Column(String)
    region = Column(String)
    district = Column(String)
    city = Column(String)
    locality = Column(String)
    postcode = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    valid_for = Column(String)

    def __repr__(self):
        """Nice geocoded table row representation"""
        return ('<Geocoded_location(ID={ID}, '
                                   'country={country}, '
                                   'region={region}, '
                                   'district={district}, '
                                   'city={city}, '
                                   'locality={locality}, '
                                   'postcode={postcode}, '
                                   'latitude={latitude}, '
                                   'longitude={longitude}, '
                                   'valid_for={valid_for})>'.format(
                                   ID=self.ID,
                                   country=self.country,
                                   region=self.region,
                                   district=self.district,
                                   city=self.city,
                                   locality=self.locality,
                                   postcode=self.postcode,
                                   latitude=self.latitude,
                                   longitude=self.longitude,
                                   valid_for=self.valid_for))


class UrlsTable(Base):
    """URLs table structure"""
    __tablename__ = 'urls'

    ID = Column(Integer, primary_key=True)
    ad_id = Column(Integer)
    url = Column(String)

    def __repr__(self):
        """Nice URLs table row representation"""
        return ('<URL(ID={ID}, '
                     'ad_id={ad_id}, '
                     'url={url})>'.format(
                     ID=self.ID,
                     ad_id=self.ad_id,
                     url=self.url))
