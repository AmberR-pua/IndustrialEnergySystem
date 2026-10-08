import argparse, csv, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def initialize(path,import_data=False,reset=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if not reset:raise ValueError('database exists; use --reset to explicitly rebuild')
        path.unlink()
    with sqlite3.connect(path) as conn:
        conn.executescript((ROOT/'db/schema.sql').read_text())
        conn.executescript((ROOT/'db/seed.sql').read_text())
        if import_data:
            with (ROOT/'data/raw_data.csv').open(encoding='utf-8',newline='') as f:
                rows=list(csv.DictReader(f))
            conn.executemany('INSERT INTO raw_data(device_id,data_time,value,unit,data_quality,source) VALUES(?,?,?,?,?,?)',
                [(int(r['device_id']),r['data_time'],float(r['value']),r['unit'],int(r['data_quality']),r['source']) for r in rows])
            conn.execute('INSERT INTO collection_log(inserted_count,start_time,end_time,mode) VALUES(?,?,?,?)',
                (len(rows),rows[0]['data_time'] if rows else None,rows[-1]['data_time'] if rows else None,'BOOTSTRAP'))
        return dict(conn.execute("SELECT 'areas',count(*) FROM area UNION ALL SELECT 'devices',count(*) FROM device UNION ALL SELECT 'rawRows',count(*) FROM raw_data"))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--path',default=str(ROOT/'runtime/energy.db'));p.add_argument('--reset',action='store_true');p.add_argument('--import-data',action='store_true');a=p.parse_args()
    try:print(initialize(a.path,a.import_data,a.reset))
    except ValueError as e:p.error(str(e))
