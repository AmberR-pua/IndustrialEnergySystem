"""Deterministic hourly fixture generation. Ground truth is evaluation-only."""
import argparse, csv, hashlib, json, math, random
from datetime import datetime, timedelta
from pathlib import Path
DEVICES = [(1,'EL-1001',70,'kWh'), (2,'EL-1002',45,'kWh'),
           (3,'EL-1003',55,'kWh'),(4,'EL-1004',30,'kWh'),
           (5,'EL-1005',12,'kWh'),(6,'WT-2001',3.5,'t')]
RAW_FIELDS = ['device_id','device_code','data_time','value','unit','data_quality','source']
TRUTH_FIELDS = ['device_id','device_code','data_time','anomaly_type','event_id','start_time','end_time','original_value','injected_value','multiplier']
def write_csv(path,fields,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def generate(out,days=365,seed=42,start='2026-01-01',missing_ratio=.01,outlier_ratio=.005,drift_ratio=.003):
    if days<1 or days>3660: raise ValueError('days must be between 1 and 3660')
    ratios=(missing_ratio,outlier_ratio,drift_ratio)
    if any(not math.isfinite(x) or x<0 or x>1 for x in ratios) or sum(ratios)>.25:
        raise ValueError('ratios must be finite, nonnegative, and sum <= 0.25')
    begin=datetime.strptime(start,'%Y-%m-%d');hours=days*24;n=hours*6
    # Round half up; drift is rounded to complete 12-hour events.
    missing_n=int(n*missing_ratio+.5);outlier_n=int(n*outlier_ratio+.5)
    drift_events=int(n*drift_ratio/12+.5)
    rng=random.Random(seed);data={}
    for device_id,code,base,unit in DEVICES:
        normal_rng=random.Random(seed+device_id)
        for h in range(hours):
            t=begin+timedelta(hours=h)
            v=base*(1.6 if 8<=t.hour<18 else .7)
            v*=.2 if t.weekday()>=5 else 1
            v*=1.15 if t.month in (1,2,7,8,12) else 1
            v=round(max(v*normal_rng.gauss(1,.08),0),2)
            data[(device_id,h)]={'device_id':device_id,'device_code':code,'data_time':t.strftime('%Y-%m-%d %H:%M:%S'),'value':f'{v:.2f}','unit':unit,'data_quality':1,'source':'METER'}
    marked={};protected=set();truth=[]
    def mark(key,kind,event,first,last,factor):
        r=data[key];v=float(r['value']);injected='' if kind=='MISSING' else f'{v*factor:.2f}'
        truth.append(dict(device_id=key[0],device_code=r['device_code'],data_time=r['data_time'],
                          anomaly_type=kind,event_id=event,start_time=data[(key[0],first)]['data_time'],
                          end_time=data[(key[0],last)]['data_time'],original_value=r['value'],
                          injected_value=injected,multiplier='' if factor is None else f'{factor:.6f}'))
        marked[key]=(kind,injected)
    # Reserve nonoverlapping contiguous windows before sampling point anomalies.
    candidates=[(d,h) for d,_,_,_ in DEVICES for h in range(hours-12)]
    rng.shuffle(candidates);events=0
    for d,h in candidates:
        keys=[(d,h+j) for j in range(12)]
        if events>=drift_events:break
        buffer=[(d,h+12)]
        if h>0:buffer.append((d,h-1))
        if any(k in marked or k in protected for k in keys+buffer):continue
        protected.update(buffer)
        events+=1
        for j,k in enumerate(keys):mark(k,'DRIFT',f'DRIFT-{events:04d}',h,h+11,1+.3*(j+1)/12)
    if events!=drift_events:raise ValueError('not enough contiguous drift windows')
    remaining=[k for k in sorted(data) if k not in marked and k not in protected]
    selected=rng.sample(remaining,missing_n+outlier_n)
    for i,k in enumerate(selected[:missing_n]):mark(k,'MISSING',f'MISSING-{i+1:04d}',k[1],k[1],None)
    for i,k in enumerate(selected[missing_n:]):
        factor=rng.choice([5,.1]);kind='SPIKE_HIGH' if factor==5 else 'SPIKE_LOW'
        mark(k,kind,f'OUTLIER-{i+1:04d}',k[1],k[1],factor)
    raw=[]
    for k,r in data.items():
        kind,value=marked.get(k,('',None))
        if kind=='MISSING':continue
        if value is not None:r['value']=value
        raw.append(r)
    raw.sort(key=lambda r:(r['data_time'],r['device_id']))
    truth.sort(key=lambda r:(r['data_time'],r['device_id']))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'raw_data.csv',RAW_FIELDS,raw);write_csv(out/'anomaly_truth.csv',TRUTH_FIELDS,truth)
    counts={kind:sum(r['anomaly_type']==kind for r in truth) for kind in ('MISSING','SPIKE_HIGH','SPIKE_LOW','DRIFT')}
    report={'seed':seed,'start':start,'days':days,'devices':6,'expected_slots':n,'raw_rows':len(raw),
            'truth_rows':len(truth),'drift_events':events,'counts':counts,
            'requested_ratios':dict(zip(('missing','outlier','drift'),ratios)),
            'actual_ratios':{'missing':missing_n/n,'outlier':outlier_n/n,'drift':events*12/n,'all':len(truth)/n},
            'ratio_denominator':'expected hourly slots before deleting missing records',
            'sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ('raw_data.csv','anomaly_truth.csv')}}
    (out/'generation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',default=str(Path(__file__).resolve().parents[1]/'data'))
    p.add_argument('--days',type=int,default=365);p.add_argument('--seed',type=int,default=42)
    p.add_argument('--start',default='2026-01-01')
    for name,value in [('missing',.01),('outlier',.005),('drift',.003)]:p.add_argument('--'+name+'-ratio',type=float,default=value)
    a=p.parse_args()
    try:print(json.dumps(generate(a.output,a.days,a.seed,a.start,a.missing_ratio,a.outlier_ratio,a.drift_ratio),ensure_ascii=False,indent=2))
    except ValueError as e:p.error(str(e))
