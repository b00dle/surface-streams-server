﻿"""ImageFile model"""
from database.base import TableBase
from sqlalchemy import Column, String, DateTime, Integer
import datetime


class Client(TableBase):
    """ImageFile database object"""

    __tablename__ = 'client'

    id = Column(Integer, primary_key=True)

    uuid = Column(String(128), unique=True, nullable=False)

    name = Column(String(256), nullable=False)

    created_datetime = Column(DateTime, nullable=False, default=datetime.datetime.now())

    ip = Column(String(64), nullable=False)

    video_src_port = Column(Integer, default=-1)

    video_sink_port = Column(Integer, default=-1)

    video_protocol = Column(String(128))

    tuio_sink_port = Column(Integer, default=-1)

    mixing_mode = Column(String(32), default="other", nullable=False)
  
    def __repr__(self):
        return "<Client id=%s uuid=%s name=%s created_datetime=%s ip=%s video_src_port=%s video_sink_port=%s video_protocol=%s tuio_sink_port=%s mixing_mode=%s>" % (
            self.id, self.uuid, self.name, str(self.created_datetime), self.ip, str(self.video_src_port), str(self.video_sink_port), self.video_protocol, str(self.tuio_sink_port), self.mixing_mode)
