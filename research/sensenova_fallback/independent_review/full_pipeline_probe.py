"""Independent verification: production prompts, validator, orchestrator and writer.
Only primary transport is fault-injected; free upstream is real. No live trading.
"""
from pathlib import Path
import sys,json,time,logging
from unittest.mock import patch
PROJECT=Path(r'D:\cl\PA_Agent')
sys.path.insert(0,str(PROJECT))
from pa_agent.config.settings import Settings
from pa_agent.ai.deepseek_client import DeepSeekClient
from pa_agent.ai.prompt_assembler import PromptAssembler
from pa_agent.ai.json_validator import JsonValidator
from pa_agent.ai.router import route_strategy_files
from pa_agent.orchestrator.two_stage import TwoStageOrchestrator
from pa_agent.records.pending_writer import PendingWriter
from pa_agent.records.experience_reader import ExperienceReader
from pa_agent.util.threading import CancelToken
from tests.integration.conftest import make_frame
ROOT=Path(__file__).resolve().parent
OUT=ROOT/('full-pipeline-'+time.strftime('%Y%m%d-%H%M%S'))
OUT.mkdir(parents=True)
logging.basicConfig(level=logging.INFO,handlers=[logging.FileHandler(OUT/'run.log',encoding='utf-8'),logging.StreamHandler()])
settings=Settings()
settings.provider.base_url='https://token.sensenova.cn/v1'
settings.provider.api_key='synthetic-primary-key-not-real'
exp=ExperienceReader(OUT/'empty-experience')
client=DeepSeekClient(settings.provider)
# The genuine primary model cannot be deliberately rate-limited; inject its failure.
def primary_failure(*args,**kwargs):
    raise ConnectionError('Injected primary network failure; free upstream remains real')
client.stream_chat=primary_failure
orchestrator=TwoStageOrchestrator(client,PromptAssembler(PROJECT/'prompt_engineering',exp,prompt_settings=settings.prompt),route_strategy_files,JsonValidator(settings.validation),PendingWriter(OUT/'records'),exp,settings)
frame=make_frame()
if '--trend' in sys.argv:
    from pa_agent.data.base import KlineBar, KlineFrame, IndicatorBundle
    n=60
    bars=tuple(KlineBar(seq=i+1,ts_open=1791586800000-i*3600000,
        open=2000+(n-1-i)*2,high=2002+(n-1-i)*2,low=1999.8+(n-1-i)*2,
        close=2001.8+(n-1-i)*2,volume=100,closed=True) for i in range(n))
    frame=KlineFrame('SYNTHETIC_XAUUSD','1h',bars,
        IndicatorBundle(tuple(b.close-15 for b in bars),tuple(2.2 for b in bars)),1791590400000)
events=[]
start=time.monotonic()
try:
    record=orchestrator.submit(frame,CancelToken(),lambda e:events.append(e.name))
    data=record.model_dump(mode='json')
    (OUT/'record.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'ok':record.exception is None and record.stage1_diagnosis is not None and record.stage2_decision is not None,'stage2_model_called':record.stage2_response is not None,'events':events,'exception':record.exception,'elapsed_s':time.monotonic()-start,'note':'Production prompts/validation/record writer, synthetic fixture bars, injected primary failure, real free upstream'}
except Exception as e:
    logging.exception('Full pipeline failed')
    summary={'ok':False,'events':events,'error':str(e),'elapsed_s':time.monotonic()-start}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2)); print('OUT='+str(OUT))
sys.exit(0 if summary['ok'] else 1)
