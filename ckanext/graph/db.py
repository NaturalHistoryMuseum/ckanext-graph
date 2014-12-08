from pylons import config
from sqlalchemy import create_engine

_read_engine = None

def _get_engine():
    """Return an SQL Alchemy engine to be used by this extention."""
    global _read_engine

    if _read_engine is None:
        _read_engine = create_engine(config['ckan.datastore.read_url'])
    return _read_engine
