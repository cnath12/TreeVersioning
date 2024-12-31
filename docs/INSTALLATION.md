# Installation Guide

## Prerequisites
- Python 3.9+
- SQLite 
- pip

## Steps
1. Clone the repository:
```bash
git clone <repository-url>
cd tree_versioning
```
2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Initialize database:
```bash
alembic upgrade head
```
## Testing Installation
```bash
pytest tests/
```