from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

class Database:
    def __init__(self, url='sqlite:///tree_versioning.db'):
        self.engine = create_engine(url)
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.SessionFactory)
        
    @contextmanager
    def get_session(self):
        """Get a new session."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
            
    def create_all(self, base):
        """Create all tables."""
        base.metadata.create_all(self.engine)

db = Database()