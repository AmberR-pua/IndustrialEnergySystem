"""Start services on fresh temporary database and ephemeral ports; always cleanup."""
import importlib.util,json,os,socket,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
def port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def call(url,body=None):
    req=Request(url,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    try:
        with urlopen(req,timeout=5) as r:return r.status,r.read(),r.headers.get('Content-Type','')
    except HTTPError as e:return e.code,e.read(),e.headers.get('Content-Type','')
def main():
    checks=[];processes=[]
    def check(name,cond):
        if not cond:raise AssertionError(name)
        checks.append(name)
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp);database=path/'energy.db'
        subprocess.run([sys.executable,'db/init_db.py','--path',str(database),'--import-data'],cwd=ROOT,check=True,capture_output=True)
        env=os.environ.copy();env['ENERGY_DB_PATH']=str(database)
        ports=[]
        while len(ports)<3:
            n=port()
            if n not in ports:ports.append(n)
        bp,fp,ap=ports;backend=f'http://127.0.0.1:{bp}';front=f'http://127.0.0.1:{fp}';algo=f'http://127.0.0.1:{ap}'
        logfile=(path/'services.log').open('w')
        try:
            for args in [['-m','backend.controller','--port',str(bp)],['frontend/server.py','--port',str(fp),'--backend',backend],['algo-service/server.py','--port',str(ap)]]:
                processes.append(subprocess.Popen([sys.executable,*args],cwd=ROOT,env=env,stdout=logfile,stderr=logfile))
            for url in [backend+'/api/health',front+'/',algo+'/health']:
                deadline=time.monotonic()+15
                while True:
                    try:
                        if call(url)[0]==200:break
                    except (URLError,TimeoutError):pass
                    if time.monotonic()>deadline:raise AssertionError('service startup timeout')
                    time.sleep(.05)
            s,b,m=call(front+'/');check('独立前端 HTML 可访问',s==200 and '园区能耗'.encode() in b and 'text/html' in m)
            check('本地 JS/CSS 无 CDN 依赖',all(call(front+'/'+asset)[0]==200 for asset in ['app.js','style.css','api.js','api.html']))
            s,b,_=call(front+'/api/health');j=json.loads(b);check('前端代理连接真实后端/数据库',s==200 and j['code']==0 and j['data']['tables']['raw_data']>0)
            s,b,_=call(front+'/api/meta');check('元信息真实含6块器具',s==200 and len(json.loads(b)['data']['devices'])==6)
            s,b,_=call(front+'/api/raw-data/page',{'areaId':2,'pageNum':1,'pageSize':20});j=json.loads(b);check('POST筛选分页全链路',s==200 and len(j['data']['list'])==20 and {r['deviceId'] for r in j['data']['list']}<={1,2})
            s,b,_=call(front+'/api/raw-data/page',{'pageSize':0});check('HTTP参数错误400与统一包络',s==400 and json.loads(b)['code']==400)
            s,b,_=call(front+'/api/raw-data/page',{'startTime':'2030-01-01 00:00:00'});check('HTTP无数据200与空列表',s==200 and json.loads(b)['data']['list']==[])
            s,b,_=call(front+'/openapi.json');check('OpenAPI契约通过本地代理访问',s==200 and json.loads(b)['openapi']=='3.0.3')
            s,b,_=call(backend+'/api/predict',{});check('未实现预测不伪造成功',s==404 and json.loads(b)['data'] is None)
            s,b,_=call(algo+'/health');check('独立算法空壳明确未就绪',s==200 and json.loads(b)['data']['modelReady'] is False)
            processes[0].terminate();processes[0].wait(timeout=5)
            s,b,_=call(front+'/api/health');check('后端退出时代理502与可读错误',s==502 and json.loads(b)['code']==502)
        except Exception:
            logfile.flush();print((path/'services.log').read_text(),file=sys.stderr);raise
        finally:
            for p in processes:
                if p.poll() is None:p.terminate()
            for p in processes:
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.wait()
            logfile.close()
    return {'result':'PASS','checkCount':len(checks),'checks':checks}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
