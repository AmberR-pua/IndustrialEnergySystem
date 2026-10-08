import argparse,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--backend-port',type=int,default=8000);p.add_argument('--frontend-port',type=int,default=5173);p.add_argument('--algo-port',type=int,default=8001);a=p.parse_args()
    if not (ROOT/'runtime/energy.db').exists():p.error('先执行 python3 db/generate_data.py 和 python3 db/init_db.py --import-data')
    children=[]
    try:
        for command in [['-m','backend.controller','--port',str(a.backend_port)],['frontend/server.py','--port',str(a.frontend_port),'--backend',f'http://127.0.0.1:{a.backend_port}'],['algo-service/server.py','--port',str(a.algo_port)]]:
            children.append(subprocess.Popen([sys.executable,*command],cwd=ROOT))
        print(f'打开 http://127.0.0.1:{a.frontend_port}，Ctrl+C 关闭全部服务',flush=True)
        while all(c.poll() is None for c in children):time.sleep(.3)
        raise RuntimeError('服务异常退出，请检查端口是否已被占用')
    except KeyboardInterrupt:pass
    finally:
        for c in children:
            if c.poll() is None:c.terminate()
        for c in children:
            try:c.wait(timeout=5)
            except subprocess.TimeoutExpired:c.kill();c.wait()
if __name__=='__main__':main()
