const $=id=>document.getElementById(id);
let page=1,total=0,current={};
async function request(url,method='GET',body){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);
 try{const r=await fetch(url,{method,signal:controller.signal,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const j=await r.json();if(!r.ok||j.code!==0)throw Error(j.message||'请求失败');return j.data;}finally{clearTimeout(timer);}
}
function notice(msg,error=false){$('notice').textContent=msg;$('notice').classList.toggle('error',error);}
function options(id,rows,label){const s=$(id);while(s.options.length>1)s.remove(1);rows.forEach(r=>{const o=document.createElement('option');o.value=r.id;o.textContent=label(r);s.append(o);});}
async function init(){
 notice('加载中…');$('refresh').disabled=true;
 try{const [status,meta]=await Promise.all([request('/api/health'),request('/api/meta')]);$('devices').textContent=status.tables.device;$('rows').textContent=status.tables.raw_data.toLocaleString();const g=status.generation;$('rate').textContent=g?(g.actual_ratios.all*100).toFixed(3)+'%':'未生成';$('days').textContent=g?g.days+' 天':'未生成';$('range').textContent=status.dataRange.startTime?status.dataRange.startTime+' — '+status.dataRange.endTime:'数据库暂无原始数据，请导入 CSV';options('area',meta.areas,r=>r.name);options('device',meta.devices,r=>r.code+' '+r.name);await load();}catch(e){notice('加载失败：'+e.message+'。可点击刷新重试。',true);}finally{$('refresh').disabled=false;}
}
async function load(){
 notice('加载中…');$('prev').disabled=$('next').disabled=true;
 try{const r=await request('/api/raw-data/page','POST',{...current,pageNum:page,pageSize:20});total=r.total;$('table').replaceChildren();
 if(!r.list.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.textContent='该筛选条件下暂无数据';tr.append(td);$('table').append(tr);}
 r.list.forEach(row=>{const tr=document.createElement('tr');[row.deviceCode,row.dataTime,row.value.toFixed(2),row.unit,{1:'正常上报',2:'异常上报',3:'缺失标记'}[row.dataQuality]].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td);});$('table').append(tr);});$('count').textContent=`共 ${total.toLocaleString()} 条 · 第 ${page} / ${Math.max(1,Math.ceil(total/20))} 页`;$('prev').disabled=page<=1;$('next').disabled=page*20>=total;notice(r.total?'后端联通正常 · 数据已加载':'暂无数据，可调整筛选条件');
 }catch(e){$('table').replaceChildren();$('count').textContent='加载失败';notice('查询失败：'+e.message+'。可再次点击查询。',true);}
}
$('filters').addEventListener('submit',e=>{e.preventDefault();current={};if($('area').value)current.areaId=Number($('area').value);if($('device').value)current.deviceId=Number($('device').value);if($('energy').value)current.energyType=$('energy').value;if($('date').value){current.startTime=$('date').value+' 00:00:00';current.endTime=$('date').value+' 23:59:59';}page=1;load();});
$('prev').onclick=()=>{page--;load();};$('next').onclick=()=>{page++;load();};$('refresh').onclick=init;
current={startTime:'2026-01-01 00:00:00',endTime:'2026-01-01 23:59:59'};init();
