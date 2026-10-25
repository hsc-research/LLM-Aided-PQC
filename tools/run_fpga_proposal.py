#!/usr/bin/env python3
"""Request one review-only Claude proposal with a conservative cost preflight.

Never applies edits, runs EDA, retries a request, or claims hardware improvement.
Budget is estimated from user-supplied prices, not an account-side billing cap.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.prepare_fpga_proposal import require, read_bounded, save, review, sha
from agent.llm_client import create_client
from agent.claude_errors import safe_error


def positive(value):
    try: x=Decimal(str(value))
    except InvalidOperation: raise ValueError('Finite positive pricing/budget required')
    require(x.is_finite() and x>0,'Finite positive pricing/budget required')
    return x


def run(context_path, model, input_price, output_price, budget, max_tokens=4096):
    require(os.environ.get('PQC_ENABLE_LLM')=='1','Paid calls disabled; set PQC_ENABLE_LLM=1 only after approving model, data and estimated budget')
    require(isinstance(model,str) and model and len(model)<160,'Explicit model required')
    ip,op,limit=map(positive,(input_price,output_price,budget))
    require(type(max_tokens) is int and 1<=max_tokens<=8192,'Output limit must be 1..8192 tokens')
    context_path=Path(context_path).resolve();folder=context_path.parent
    context=json.loads(read_bounded(context_path,4*1024*1024))
    require(context.get('status')=='PROMPT_PREPARED_NO_API_CALL','Wrong context')
    require(sha(folder/'prompt.json')==context['prompt_sha256'],'Prompt changed')
    require(all(sha(p)==h for p,h in context['input_sha256'].items()),'Inputs changed; prepare again')
    require(not (folder/'proposal-run.json').exists(),'A request already started here; do not retry an uncertain call')
    prompt=json.loads(read_bounded(folder/'prompt.json',512*1024))
    params={'model':model,'system':prompt['system'],'messages':[{'role':'user','content':json.dumps(prompt['user'],allow_nan=False)}]}
    # Exclusive persistent claim prevents concurrent duplicate charges. Never remove
    # it automatically, including after timeouts or preflight errors.
    try:
        with (folder/'.proposal-request.lock').open('x') as lock:
            lock.write('One proposal request claimed; inspect provider usage before any new request.\n')
    except FileExistsError:
        raise ValueError('A request has already been claimed in this directory') from None
    record={'schema_version':1,'status':'PREFLIGHT_RUNNING','context_sha256':sha(context_path),
            'prompt_sha256':context['prompt_sha256'],'profile_fingerprint':context['profile_fingerprint'],
            'target':'fpga','stage':'proposal_only','model':model,'api_calls_attempted':0,
            'failure_stage':None,'token_count_requests_attempted':0,
            'input_tokens':None,'output_tokens':None,'estimated_max_cost_usd':None,'reported_cost_usd':None,
            'pricing':{'source':'user_declared_USD_per_million_tokens','input':str(ip),'output':str(op)},
            'budget_usd':str(limit),'max_output_tokens':max_tokens,'rtl_changed':False,
            'automatic_acceptance':'BLOCKED','started_at':datetime.now(timezone.utc).isoformat()}
    save(folder/'proposal-run.json',record)
    failure_stage='credential_setup'
    try:
        client=create_client()
        failure_stage='token_count'
        record['token_count_requests_attempted']=1;save(folder/'proposal-run.json',record)
        counted=client.messages.count_tokens(**params).input_tokens
        require(type(counted)is int and counted>=0,'Invalid token-count response')
        failure_stage='budget_check'
        # Counting endpoint estimates may differ from billed message usage.
        reserved=counted+(counted+9)//10+1024
        estimate=(Decimal(reserved)*ip+Decimal(max_tokens)*op)/1000000
        record.update(input_tokens_estimated=counted,estimated_max_cost_usd=str(estimate))
        if estimate>limit:
            record['status']='BLOCKED_BUDGET';save(folder/'proposal-run.json',record);return record
        require(all(sha(p)==h for p,h in context['input_sha256'].items()),'Inputs changed during token preflight')
        failure_stage='generation'
        record.update(status='RUNNING',api_calls_attempted=1);save(folder/'proposal-run.json',record)
        reply=client.messages.create(**params,max_tokens=max_tokens)
        failure_stage='response_review'
        record.update(input_tokens=reply.usage.input_tokens,output_tokens=reply.usage.output_tokens)
        require(type(record['input_tokens'])is int and type(record['output_tokens'])is int,'Missing usage')
        record['reported_cost_usd']=str((Decimal(record['input_tokens'])*ip+Decimal(record['output_tokens'])*op)/1000000)
        record['cost_note']='Computed from returned token usage and supplied prices; provider billing is authoritative.'
        require(reply.stop_reason=='end_turn','Incomplete/tool-directed response; no retry')
        require(reply.content and all(b.type=='text' for b in reply.content),'Only text JSON accepted')
        raw=''.join(b.text for b in reply.content)
        require(len(raw.encode())<=192*1024,'Response too large')
        (folder/'proposal-response.json').write_text(raw, encoding='utf-8')
        record['response_sha256']=sha(folder/'proposal-response.json');save(folder/'proposal-run.json',record)
        verdict=review(context_path,folder/'proposal-response.json',folder/'review.json')
        record['status']='STOP' if verdict['status']=='STOP' else 'PROPOSAL_REVIEW_READY'
    except (Exception, KeyboardInterrupt) as exc:
        record['status']='FAILED_OUTCOME_UNKNOWN' if record['api_calls_attempted'] and record['input_tokens'] is None else 'FAILED'
        # Do not log SDK error text, request headers, environment or credentials.
        record.update(safe_error(exc, failure_stage))
        record['error_note']='No automatic retry; no edit was applied. See docs/CLAUDE_CREDENTIALS.md and preserve this run.'
        save(folder/'proposal-run.json',record)
        raise RuntimeError(record['status']+': '+record['error_type']+'; see proposal-run.json') from None
    finally:
        record['finished_at']=datetime.now(timezone.utc).isoformat();save(folder/'proposal-run.json',record)
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--context',required=True);p.add_argument('--model',required=True);p.add_argument('--input-usd-per-million',required=True);p.add_argument('--output-usd-per-million',required=True);p.add_argument('--budget-usd',required=True);p.add_argument('--max-tokens',type=int,default=4096)
    a=p.parse_args()
    try: print(json.dumps(run(a.context,a.model,a.input_usd_per_million,a.output_usd_per_million,a.budget_usd,a.max_tokens),indent=2));return 0
    except (ValueError,RuntimeError,OSError,ImportError) as exc: print('BLOCKED: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
