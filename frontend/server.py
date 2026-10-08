"""Local frontend server with same-origin API proxy; no node or CDN required."""
import argparse,json
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen
class Handler(SimpleHTTPRequestHandler):
    backend='http://127.0.0.1:8000'
    def proxy(self):
        n=int(self.headers.get('Content-Length','0'))
        if not 0<=n<=65536:
            self.send_error(413);return
        payload=self.rfile.read(n) if n else None
        req=Request(self.backend+self.path,data=payload,method=self.command,headers={'Content-Type':self.headers.get('Content-Type','application/json')})
        try:
            with urlopen(req,timeout=10) as r:self.relay(r.status,r.read(),r.headers.get('Content-Type','application/json'))
        except HTTPError as e:self.relay(e.code,e.read(),'application/json')
        except (URLError,TimeoutError):self.relay(502,json.dumps({'code':502,'message':'后端连接失败，请启动后端服务','data':None},ensure_ascii=False).encode(),'application/json; charset=utf-8')
    def relay(self,status,payload,mime):
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    def do_GET(self):
        if self.path.startswith('/api/') or self.path.startswith('/openapi.json'):self.proxy()
        else:super().do_GET()
    def do_POST(self):
        if self.path.startswith('/api/'):self.proxy()
        else:self.send_error(404)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=5173);p.add_argument('--backend',default='http://127.0.0.1:8000');a=p.parse_args();Handler.backend=a.backend
    print(f'Frontend: http://127.0.0.1:{a.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',a.port),partial(Handler,directory=str(Path(__file__).parent))).serve_forever()
