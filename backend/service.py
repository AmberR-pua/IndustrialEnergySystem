import json
from datetime import datetime
from . import mapper
ROOT=mapper.ROOT
def metadata():
    return {'areas':mapper.rows('SELECT * FROM area ORDER BY id'),
            'devices':mapper.rows('SELECT * FROM device ORDER BY id'),
            'energyTypes':mapper.rows('SELECT * FROM energy_type ORDER BY code')}
def status():
    with mapper.connection() as c:
        counts={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['area','device','raw_data','summary','alert','forecast_result']}
        span=dict(c.execute('SELECT min(data_time) startTime,max(data_time) endTime FROM raw_data').fetchone())
    report_path=ROOT/'data/generation_report.json'
    return {'service':'backend','stage':'week1','tables':counts,'dataRange':span,
            'generation':json.loads(report_path.read_text()) if report_path.exists() else None}
def integer(p,key,default=None,minimum=1,maximum=2147483647):
    v=p.get(key,default)
    if isinstance(v,bool) or not isinstance(v,int) or not minimum<=v<=maximum:raise ValueError(f'{key} 必须是 {minimum} 至 {maximum} 的整数')
    return v
def raw_page(p):
    if not isinstance(p,dict):raise ValueError('请求体必须是对象')
    allowed={'areaId','deviceId','energyType','startTime','endTime','dataQuality','pageNum','pageSize'}
    if set(p)-allowed:raise ValueError('未知字段: '+','.join(sorted(set(p)-allowed)))
    page=integer(p,'pageNum',1);size=integer(p,'pageSize',20,maximum=200)
    where=[];args=[]
    if p.get('areaId') is not None:
        aid=integer(p,'areaId')
        if not mapper.rows('SELECT id FROM area WHERE id=?',(aid,)):raise ValueError('areaId 不存在')
        ids=mapper.rows('WITH RECURSIVE subtree(id) AS (SELECT id FROM area WHERE id=? UNION ALL SELECT a.id FROM area a JOIN subtree s ON a.parent_id=s.id) SELECT id FROM subtree',(aid,))
        where.append('d.area_id IN ('+','.join('?' for _ in ids)+')');args.extend(r['id'] for r in ids)
    if p.get('deviceId') is not None:
        where.append('r.device_id=?');args.append(integer(p,'deviceId'))
    if p.get('energyType') is not None:
        if p['energyType'] not in ['ELECTRIC','WATER']:raise ValueError('energyType 必须为 ELECTRIC 或 WATER')
        where.append('d.energy_type=?');args.append(p['energyType'])
    if p.get('dataQuality') is not None:where.append('r.data_quality=?');args.append(integer(p,'dataQuality',maximum=3))
    times={}
    for field,op in [('startTime','>='),('endTime','<=')]:
        if p.get(field) is not None:
            v=p[field]
            if not isinstance(v,str):raise ValueError(field+' 必须是时间字符串')
            try:
                t=datetime.strptime(v,'%Y-%m-%d %H:%M:%S')
                if t.strftime('%Y-%m-%d %H:%M:%S')!=v:raise ValueError()
            except ValueError:raise ValueError(field+' 格式应为 YYYY-MM-DD HH:mm:ss')
            times[field]=v;where.append('r.data_time '+op+' ?');args.append(v)
    if len(times)==2 and times['startTime']>times['endTime']:raise ValueError('开始时间不能晚于结束时间')
    condition=(' WHERE '+' AND '.join(where)) if where else ''
    base=' FROM raw_data r JOIN device d ON r.device_id=d.id'+condition
    with mapper.connection() as c:
        total=c.execute('SELECT count(*)'+base,args).fetchone()[0]
        result=c.execute('SELECT r.id,r.device_id deviceId,d.code deviceCode,d.name deviceName,d.energy_type energyType,r.data_time dataTime,r.value,r.unit,r.data_quality dataQuality,r.source'+base+' ORDER BY r.data_time,r.device_id LIMIT ? OFFSET ?',args+[size,(page-1)*size])
        return {'total':total,'pageNum':page,'pageSize':size,'list':[dict(r) for r in result]}
