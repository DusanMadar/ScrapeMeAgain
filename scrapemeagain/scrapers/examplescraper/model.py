from sqlalchemy import Column, Integer, String

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ExampleDataTable(Base):
    __tablename__ = 'example_item_data'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    h1 = Column(String)
