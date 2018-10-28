"""SQLAlchemy common database tables definition."""


from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ItemUrlsTable(Base):
    """Item URLs table structure."""

    __tablename__ = "item_urls"

    id = Column(Integer, primary_key=True)
    url = Column(String)

    def __repr__(self):
        """Nice ItemUrlsTable row representation."""
        return "<Item URL (id={id}, url={url})>".format(
            id=self.id, url=self.url
        )
