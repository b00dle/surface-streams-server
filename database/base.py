from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from database.config import dev
from datetime import datetime

##
#  sqlalchemy database instance created based on uri
##

engine = create_engine(dev.SQLALCHEMY_DATABASE_DEBUG_URI, echo=dev.SQLALCHEMY_ECHO)


##
# Declarative base extension
# to make each derived class dict serializable.
##

class _TableExt(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def as_dict(self):
        """ Returns all object properties as dictionary. """
        dict = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        for key in dict:
            if isinstance(dict[key], datetime):
                dict[key] = dict[key].isoformat()
        return dict

    def from_dict(self, d):
        """ Sets the objects attributes from python dict.
            Returns success of operation. """
        if not isinstance(d, dict):
            print("Failure: parameter has to be a dictionary.")
            return False
        for key in d:
            if hasattr(self, key):
                setattr(self, key, d[key])
            else:
                print("Failure:", type(self), " does not have '", key, "' attribute.")
                print(" > Skipping dict argument...")
        return True

##
# Base class for all table objects
##


TableBase = declarative_base(cls=_TableExt)


##
# Functions for creating and dropping the database
##
def create_database():
    """ Creates the database from scratch. """
    global TableBase
    global engine
    TableBase.metadata.create_all(engine)


def drop_database():
    """ Drops all database contents.
        ALL DATABASE TABLES/INDEXES AND DATA WILL BE LOST!"""
    global TableBase
    global engine
    TableBase.metadata.drop_all(engine)


def recreate_database():
    """ drops database and creates it from scratch.
        ALL DATA WILL BE LOST! """
    drop_database()
    create_database()