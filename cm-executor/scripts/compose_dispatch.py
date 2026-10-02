#!/usr/bin/env python3
"""Compose child instructions + role + dispatch; never launches agents or grants authority.

CLI validates a canonical imported-plan packet. A real adapter may apply the same recipe
to a separately authorized amended graph after validating the amendment.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cm_injection_handoff',BASE/'scripts/handoff.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
v=h.v
ROLES=json.loads((BASE/'assets/roles.json').read_text(encoding='utf-8'))['roles']

def closure(name):
    result={}
    def add(n):
        if n in result:return
        result[n]=v.SCHEMA['$defs'][n]
        def walk(x):
            if isinstance(x,dict):
                if '$ref' in x and x['$ref'].startswith('#/$defs/'):add(x['$ref'].split('/')[-1])
                for item in x.values():walk(item)
            elif isinstance(x,list):
                for item in x:walk(item)
        walk(result[n])
    add(name)
    return {'$schema':v.SCHEMA['$schema'],'$defs':result,'$ref':'#/$defs/'+name}

def compose(dispatch,plan_root=None,live=False):
    errors=v.validate_document(dispatch,live)+h.contract_errors()
    if dispatch.get('kind')!='dispatch':errors.append('Expected dispatch document')
    if plan_root is not None:
        errors+=h.validate_handoff(Path(plan_root),live)
        if not errors:
            m=h.load(Path(plan_root)/'HANDOFF.json');g=h.load(Path(plan_root)/m['graph_path'])
            packet=next((t for t in g['tasks'] if t['task_id']==dispatch['packet']['task_id']),None)
            if packet is None or v.canonical_hash(packet)!=dispatch['packet_sha256']:errors.append('Dispatch packet is not the canonical admitted-plan packet; an authorized amendment is required')
    if errors:raise ValueError('\n'.join(errors))
    role=dispatch['recipient']['role'];path=BASE/f'references/roles/{role}.md'
    common=(BASE/'references/COMMON-WORKER.md').read_text(encoding='utf-8').strip()
    role_text=path.read_text(encoding='utf-8').strip()
    return {'instructions':common+'\n\n---\n\n'+role_text,
            'task_data':dispatch,
            'response_contract':closure('result'),
            'protocol_contract':{k:closure(k) for k in ['artifact','evidence','change_request']},
            'provenance':{'profile':'cm-two-skill/1.0','role':role,'role_sha256':h.digest(path),'common_sha256':h.digest(BASE/'references/COMMON-WORKER.md'),'packet_sha256':dispatch['packet_sha256'],'contract_sha256':h.contract_digest()}}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dispatch',type=Path);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--live',action='store_true');a=p.parse_args(argv)
    try:
        payload=compose(h.load(a.dispatch),a.plan,a.live)
        with a.output.open('x',encoding='utf-8') as f:json.dump(payload,f,indent=2,ensure_ascii=False);f.write('\n')
        print(f'Composed {a.output}; no agent was launched and no authority was authenticated.');return 0
    except (OSError,ValueError,KeyError,TypeError) as e:print('FAIL: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
