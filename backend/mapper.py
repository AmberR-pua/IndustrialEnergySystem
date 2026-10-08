import os,sqlite3
from contextlib import contextmanager
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB_PATH=Path(os.environ.get('ENERGY_DB_PATH',str(ROOT/'runtime/energy.db')))
@contextmanager
def connection():
    if not DB_PATH.exists():raise RuntimeError('数据库未初始化，请先执行 db/init_db.py')
    conn=sqlite3.connect(DB_PATH,timeout=10);conn.row_factory=sqlite3.Row;conn.execute('PRAGMA foreign_keys=ON')
    try:yield conn
    finally:conn.close()
def rows(sql,args=()):
    with connection() as conn:return [dict(r) for r in conn.execute(sql,args)]
