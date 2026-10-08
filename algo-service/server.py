"""Week-one independent algorithm service skeleton. No fake model metrics."""
import argparse,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status=200 if self.path=='/health' else 404
        data={'code':0,'message':'success','data':{'service':'algo-service','stage':'week1','modelReady':False,'plannedModel':'LightGBM','trainingImplemented':False}} if status==200 else {'code':404,'message':'算法训练与预测安排在第三周','data':None}
        body=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8001);a=p.parse_args()
    print(f'Algorithm: http://127.0.0.1:{a.port}/health',flush=True);ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
