import json,time,pathlib,httpx,sys
root=pathlib.Path(__file__).resolve().parent
models=json.loads((root/'kilo-models.json').read_text(encoding='utf-8-sig'))['data']
free={m['id'] for m in models if m.get('isFree') is True}
model=sys.argv[1] if len(sys.argv)>1 else 'inclusionai/ling-3.1-flash'
assert model in free
start=time.monotonic()
try:
    with httpx.Client(timeout=120,follow_redirects=False) as c:
        r=c.post('https://api.kilo.ai/api/gateway/chat/completions',headers={'User-Agent':'PA-Agent-Fallback-Verification','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':'Synthetic connectivity test only. Return only JSON with keys status (value ok) and sum (value 7).'}],'stream':False,'max_tokens':512,'reasoning':{'enabled':False}})
        result={'model':model,'http_status':r.status_code,'elapsed_s':time.monotonic()-start,'body':r.text}
except Exception as e:
    result={'model':model,'elapsed_s':time.monotonic()-start,'error':str(e)}
(root/('independent-probe-'+str(time.time_ns())+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
