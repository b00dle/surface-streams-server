"""ImageFile model"""
from database.base import TableBase
from sqlalchemy import Column, String, DateTime
import datetime


class ImageFile(TableBase):
    """ImageFile database object"""

    __tablename__ = 'image_file'

    uuid = Column(String(128), primary_key=True)

    name = Column(String(256), nullable=False)

    created_datetime = Column(DateTime, nullable=False, default=datetime.datetime.now())

    mimetype = Column(String(64))

    filename = Column(String(512))
  
    def __repr__(self):
        return "<ImageFile uuid=%s name=%s created_datetime=%s mimetype=%s filename=%s>" % (
            self.uuid, self.name, str(self.created_datetime), self.mimetype, self.filename)
