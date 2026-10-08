import argparse,json,traceback
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
from . import service
class Handler(BaseHTTPRequestHandler):
    def response(self,status,data):
        payload=json.dumps(data,ensure_ascii=False).encode();self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    def dispatch(self):
        route=urlsplit(self.path).path
        try:
            if self.command=='GET' and route=='/api/health':data=service.status()
            elif self.command=='GET' and route=='/api/meta':data=service.metadata()
            elif self.command=='GET' and route=='/openapi.json':
                self.response(200,json.loads((service.ROOT/'docs/openapi.json').read_text()));return
            elif self.command=='POST' and route=='/api/raw-data/page':
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=65536:raise ValueError('请求体长度应为 1 至 65536 字节')
                if 'application/json' not in self.headers.get('Content-Type',''):raise ValueError('Content-Type 应为 application/json')
                data=service.raw_page(json.loads(self.rfile.read(size)))
            else:self.response(404,{'code':404,'message':'接口不存在或尚未在第一周实现','data':None});return
            self.response(200,{'code':0,'message':'success','data':data})
        except (ValueError,UnicodeDecodeError) as e:self.response(400,{'code':400,'message':str(e),'data':None})
        except Exception:
            traceback.print_exc();self.response(500,{'code':500,'message':'服务暂不可用，请检查数据库初始化和服务日志','data':None})
    do_GET=dispatch
    do_POST=dispatch
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);a=p.parse_args()
    print(f'Backend: http://127.0.0.1:{a.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
