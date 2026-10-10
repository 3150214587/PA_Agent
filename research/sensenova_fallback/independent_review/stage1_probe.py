from pathlib import Path
import sys,time,json,httpx
PROJECT=Path(r'D:\cl\PA_Agent'); sys.path.insert(0,str(PROJECT))
from pa_agent.ai.prompt_assembler import PromptAssembler
from pa_agent.ai.json_validator import JsonValidator,Ok
from tests.integration.conftest import make_frame
out=Path(__file__).resolve().parent/('stage1-'+time.strftime('%Y%m%d-%H%M%S')); out.mkdir()
frame=make_frame(); messages=PromptAssembler(PROJECT/'prompt_engineering').build_stage1(frame)
body={'model':sys.argv[1] if len(sys.argv)>1 else 'inclusionai/ling-3.1-flash','messages':messages,'stream':False,'max_tokens':16384,'reasoning':{'enabled':False}}
(out/'request.json').write_text(json.dumps(body,ensure_ascii=False,indent=2),encoding='utf-8')
start=time.monotonic()
try:
    with httpx.Client(timeout=180,follow_redirects=False) as c:
        r=c.post('https://api.kilo.ai/api/gateway/chat/completions',headers={'User-Agent':'PA-Agent-Verification'},json=body)
    (out/'response.txt').write_text(r.text,encoding='utf-8')
    r.raise_for_status(); p=r.json(); content=p['choices'][0]['message'].get('content') or ''
    result=JsonValidator().validate('stage1',content,kline_frame=frame)
    summary={'ok':isinstance(result,Ok),'http_status':r.status_code,'elapsed_s':time.monotonic()-start,'finish_reason':p['choices'][0].get('finish_reason'),'content_chars':len(content),'validation':str(result)}
except Exception as e: summary={'ok':False,'error':str(e),'elapsed_s':time.monotonic()-start}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2)); print(out)
