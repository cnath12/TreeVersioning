from setuptools import setup, find_packages

setup(
    name="tree_versioning",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "SQLAlchemy>=1.4.41",
        "alembic>=1.9.1",
        "pytest>=7.3.1",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.9",
)