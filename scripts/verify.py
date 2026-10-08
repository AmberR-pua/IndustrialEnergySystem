"""Meaningful fixture, relational integrity and service checks; no dependencies."""
import csv,hashlib,importlib.util,json,platform,random,sqlite3,sys,tempfile
from datetime import datetime,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
gen=load_module('generate_data',ROOT/'db/generate_data.py');init=load_module('init_db',ROOT/'db/init_db.py')
def read(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def verify():
    results=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        results.append(name)
    report=json.loads((ROOT/'data/generation_report.json').read_text());raw=read(ROOT/'data/raw_data.csv');truth=read(ROOT/'data/anomaly_truth.csv')
    key=lambda r:(int(r['device_id']),r['data_time'])
    rd={key(r):r for r in raw};td={key(r):r for r in truth};start=datetime.strptime(report['start'],'%Y-%m-%d')
    full={(d,(start+timedelta(hours=h)).strftime('%Y-%m-%d %H:%M:%S')) for d in range(1,7) for h in range(report['days']*24)}
    missing={k for k,r in td.items() if r['anomaly_type']=='MISSING'}
    check('完整网格与删除缺失一一对应',set(rd)==full-missing)
    check('原始键唯一、异常标签互斥',len(rd)==len(raw) and len(td)==len(truth) and set(td)<=full)
    check('原始文件全局按时间和器具排序',raw==sorted(raw,key=lambda r:(r['data_time'],int(r['device_id']))))
    check('计数报告一致',len(raw)==report['raw_rows'] and len(truth)==report['truth_rows'] and len(full)==report['expected_slots'])
    check('各类计数与报告一致',all(sum(r['anomaly_type']==k for r in truth)==v for k,v in report['counts'].items()))
    check('质量标签未泄漏 truth',all(r['data_quality']=='1' and r['source']=='METER' for r in raw))
    # Reconstruct every normal baseline independently, then apply truth transformations.
    baseline={}
    for d,code,base,unit in gen.DEVICES:
        rng=random.Random(report['seed']+d)
        for h in range(report['days']*24):
            t=start+timedelta(hours=h);v=base*(1.6 if 8<=t.hour<18 else .7)*(.2 if t.weekday()>=5 else 1)*(1.15 if t.month in (1,2,7,8,12) else 1)
            baseline[(d,t.strftime('%Y-%m-%d %H:%M:%S'))]=round(max(v*rng.gauss(1,.08),0),2)
    check('异常原值符合任务书负荷/周期/噪声公式',all(float(r['original_value'])==baseline[k] for k,r in td.items()))
    check('非异常记录与基线逐点相同',all(float(r['value'])==baseline[k] for k,r in rd.items() if k not in td))
    check('突变按 ×5 或 ×0.1 注入且 CSV 与真值一致',all(float(r['multiplier'])==(5 if r['anomaly_type']=='SPIKE_HIGH' else .1) and float(r['injected_value'])==round(baseline[k]*float(r['multiplier']),2) and r['injected_value']==rd[k]['value'] for k,r in td.items() if r['anomaly_type'].startswith('SPIKE')))
    events={}
    for k,r in td.items():
        if r['anomaly_type']=='DRIFT':events.setdefault(r['event_id'],[]).append(r)
    valid=True
    for event in events.values():
        event.sort(key=lambda r:r['data_time']);t=datetime.strptime(event[0]['data_time'],'%Y-%m-%d %H:%M:%S')
        valid &= len(event)==12 and len({r['device_id'] for r in event})==1
        for j,r in enumerate(event):
            valid &= r['data_time']==(t+timedelta(hours=j)).strftime('%Y-%m-%d %H:%M:%S') and r['start_time']==event[0]['data_time'] and r['end_time']==event[-1]['data_time'] and abs(float(r['multiplier'])-(1+.3*(j+1)/12))<1e-6 and float(rd[key(r)]['value'])==round(baseline[key(r)]*(1+.3*(j+1)/12),2)
    check('漂移为完整12小时、逐步升到1.3且窗口不重叠',valid and len(events)==report['drift_events'])
    recovery=True
    for event in events.values():
        last=max(event,key=lambda r:r['data_time'])
        t=datetime.strptime(last['data_time'],'%Y-%m-%d %H:%M:%S')+timedelta(hours=1)
        k=(int(last['device_id']),t.strftime('%Y-%m-%d %H:%M:%S'))
        recovery &= k in rd and k not in td and float(rd[k]['value'])==baseline[k]
    check('每个漂移事件下一小时真实恢复基线',recovery)
    check('异常比例使用完整网格分母',abs(report['actual_ratios']['all']-len(truth)/len(full))<1e-12)
    check('CSV SHA-256 与生成报告一致',all(hashlib.sha256((ROOT/'data'/name).read_bytes()).hexdigest()==digest for name,digest in report['sha256'].items()))
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);rr=report['requested_ratios'];rerun=gen.generate(tmp/'data',report['days'],report['seed'],report['start'],rr['missing'],rr['outlier'],rr['drift'])
        check('同参数同种子 CSV 字节完全一致',rerun['sha256']==report['sha256'])
        zero=gen.generate(tmp/'zero',1,42,'2026-01-01',0,0,0)
        check('零异常比例与小数据集可运行',zero['raw_rows']==144 and zero['truth_rows']==0)
        leap=gen.generate(tmp/'leap',366,42,'2028-01-01',0,0,0)
        check('闰年366天完整覆盖',leap['expected_slots']==52704 and read(tmp/'leap/raw_data.csv')[-1]['data_time']=='2028-12-31 23:00:00')
        rejects=0
        for kwargs in [{'days':0},{'missing_ratio':-.1},{'drift_ratio':float('nan')},{'outlier_ratio':.5}]:
            try:gen.generate(tmp/'bad',**kwargs)
            except ValueError:rejects+=1
        check('非法天数/负比例/NaN/超范围拒绝',rejects==4)
        database=tmp/'test.db';counts=init.initialize(database,True)
        check('种子区域/器具/全年导入完成',counts=={'areas':5,'devices':6,'rawRows':len(raw)})
        with sqlite3.connect(database) as c:
            c.execute('PRAGMA foreign_keys=ON');checks=0
            for sql,args in [('INSERT INTO raw_data(device_id,data_time,value,unit,data_quality,source) VALUES(?,?,?,?,?,?)',(1,'2026-01-01 00:00:00',-1,'kWh',1,'METER')),('INSERT INTO raw_data(device_id,data_time,value,unit,data_quality,source) VALUES(?,?,?,?,?,?)',(99,'2026-01-01 00:00:00',1,'kWh',1,'METER')),('INSERT INTO raw_data(device_id,data_time,value,unit,data_quality,source) VALUES(?,?,?,?,?,?)',(1,'2026-01-01 00:30:00',1,'kWh',1,'METER'))]:
                try:c.execute(sql,args)
                except sqlite3.IntegrityError:checks+=1
            r=raw[0]
            try:c.execute('INSERT INTO raw_data(device_id,data_time,value,unit,data_quality,source) VALUES(?,?,?,?,?,?)',(int(r['device_id']),r['data_time'],float(r['value']),r['unit'],1,'METER'))
            except sqlite3.IntegrityError:checks+=1
            check('外键、非负、小时边界、重复唯一约束',checks==4)
            check('后续三类表已建但为空',all(c.execute('SELECT count(*) FROM '+t).fetchone()[0]==0 for t in ['summary','alert','forecast_result']))
        try:init.initialize(database)
        except ValueError:check('数据库默认拒绝覆盖',True)
        else:raise AssertionError('database overwrite')
        from backend import mapper,service
        old=mapper.DB_PATH;mapper.DB_PATH=database
        try:
            region=service.raw_page({'areaId':2,'pageSize':200})
            expected=sum(int(r['device_id']) in [1,2] for r in raw)
            check('区域筛选包含子产线，且不混入其他车间',region['total']==expected and {r['deviceId'] for r in region['list']}<={1,2})
            a=service.raw_page({'pageNum':1,'pageSize':20});b=service.raw_page({'pageNum':2,'pageSize':20})
            check('稳定分页、页间无重复',len(a['list'])==20 and len(b['list'])==20 and not ({r['id'] for r in a['list']}&{r['id'] for r in b['list']}))
            check('无数据条件返回空列表',service.raw_page({'startTime':'2030-01-01 00:00:00'})['total']==0)
            water=service.raw_page({'energyType':'WATER','pageSize':200})
            check('能源过滤单位正确',all(r['unit']=='t' and r['deviceId']==6 for r in water['list']))
            rejects=0
            for p in [{'pageSize':201},{'pageNum':True},{'deviceId':'1'},{'startTime':'2026-99-01 00:00:00'},{'startTime':'2026-02-01 00:00:00','endTime':'2026-01-01 00:00:00'},{'areaId':999},{'energyType':'GAS'},{'unexpected':1}]:
                try:service.raw_page(p)
                except ValueError:rejects+=1
            check('筛选分页参数与时间范围校验',rejects==8)
        finally:mapper.DB_PATH=old
    return {'result':'PASS','python':platform.python_version(),'checkCount':len(results),'checks':results,'data':report}
if __name__=='__main__':
    result=verify();print(json.dumps(result,ensure_ascii=False,indent=2))
