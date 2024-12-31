# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from tree_versioning.models import Base, Tree

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="session")
def SessionFactory(engine):
    """Create a session factory."""
    return sessionmaker(bind=engine)

@pytest.fixture
def session(SessionFactory):
    """Create a new database session for a test."""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

@pytest.fixture
def sample_tree(session):
    """Create a sample tree for testing."""
    tree = Tree(name="test_tree")
    session.add(tree)
    session.commit()
    return tree