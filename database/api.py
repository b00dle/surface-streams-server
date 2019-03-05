import database.base
from sqlalchemy.orm import sessionmaker
from database.models import tables

Session = sessionmaker()


class Api(object):
    def __init__(self, bind):
        self._db = None
        self.bind = bind

    def open(self):
        """ creates a session for database transaction if none is active. """
        self._db = Session(bind=self.bind)

    def close(self):
        """ closes the current database session if open. """
        self._db.expunge_all()
        self._db.close()
        self._db = None

    def commit(self):
        return self._db.commit()

    def _clear(self):
        """ clears all tables """
        for table in reversed(database.base.TableBase.metadata.sorted_tables):
            self._db.execute(table.delete())

    def insert(self, obj):
        """ adds a database object to the current session. """
        self._db.add(obj)
    
    def insert_all(self, obj_list):
        """ adds a list of database objects to the current session. """
        self._db.add_all(obj_list)

    def expunge(self, obj):
        """ removes a database object from the current session. """
        self._db.expunge(obj)

    def expunge_all(self, obj_list):
        """ removes a list of database objects from the current session. """
        for item in obj_list:
            self._db.expunge(item)

    def delete(self, obj):
        """ Helper function to encapsulate delete operations.
            Performs automatic commit (see commit()).
            Performs automatic expunge if commit unsuccessful (see expunge()).
            Returns success of operation. """
        self._db.delete(obj)

    def query(self,*args):
        """ universal function for querying the database connection. """
        return self._db.query(*args)
    
    def select(self, table, filter):
        """ helper function for performing simple select operations. """
        return self.query(table).filter(filter)

    def select_all(self, table):
        """ helper function for performing select operations with no filter. """
        return self.query(table).all()


class ClientApi(Api):
    def __init__(self, bind):
        super().__init__(bind)

    def add_client(self, uuid, name, ip, video_src_port=-1, video_sink_port=-1, video_protocol="jpeg", tuio_sink_port=-1, mixing_mode="other"):
        c = tables.Client(
            uuid=uuid, name=name, ip=ip,
            video_src_port=video_src_port,
            video_sink_port=video_sink_port,
            video_protocol=video_protocol,
            tuio_sink_port=tuio_sink_port,
            mixing_mode=mixing_mode
        )
        self.insert(c)
        return c

    def get_client(self, uuid):
        return self.select(tables.Client, tables.Client.uuid == uuid).first()

    def get_clients(self):
        return self.select_all(tables.Client)

    def remove_client(self, uuid):
        c = self.get_client(uuid)
        if c is None:
            return False
        self.delete(c)
        return True

    def remove_clients(self, uuids=[]):
        for uuid in uuids:
            if not self.remove_client(uuid):
                return False
        return True


class ImageApi(Api):
    def __init__(self, bind):
        super().__init__(bind)

    def add_image_file(self, uuid, name):
        i = tables.ImageFile(uuid=uuid, name=name)
        self.insert(i)
        return i

    def get_image_file(self, uuid):
        return self.select(tables.ImageFile, tables.ImageFile.uuid == uuid).first()

    def get_image_files(self):
        return self.select_all(tables.ImageFile)

    def remove_image_file(self, uuid):
        i = self.get_image_file(uuid)
        if i is None:
            return False
        self.delete(i)
        return True

    def remove_image_files(self, uuids=[]):
        for uuid in uuids:
            if not self.remove_image_file(uuid):
                return False
        return True
