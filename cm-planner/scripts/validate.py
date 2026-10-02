#!/usr/bin/env python3
"""Static CDAG document/bundle validator; NOT a scheduler or authorization engine.

Requires jsonschema >=4.18,<5. Uses local schemas only; never retrieves references.
Run: python scripts/validate.py DOCUMENT_OR_DIRECTORY
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit('Install the validation dependencies from requirements.txt in an isolated environment.') from exc

BASE = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((BASE/'assets/protocol.schema.json').read_text(encoding='utf-8'))
ROLES = json.loads((BASE/'assets/roles.json').read_text(encoding='utf-8'))['roles']
KINDS = {k.replace('_','-'): k for k in ('packet','dispatch','result','artifact','evidence','attestation','policy','graph','change_request','event')}
Doc = dict[str, Any]

def parse_json(text: str) -> Any:
    """Reject duplicate keys and non-finite constants before schema validation."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError(f'Duplicate JSON key: {key}')
            result[key]=value
        return result
    def constant(value):
        raise ValueError(f'Non-finite JSON number is forbidden: {value}')
    return json.loads(text,object_pairs_hook=pairs,parse_constant=constant)

def canonical_hash(value: Any) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

def ref_key(value: Doc) -> tuple[str,str]:
    return value['artifact_id'],value['sha256']

def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z','+00:00'))

def duplicates(values: list[Any]) -> bool:
    return len(values)!=len(set(values))

def same_context(a: Doc,b: Doc) -> bool:
    aa={k:v for k,v in a.items() if k!='inputs'};bb={k:v for k,v in b.items() if k!='inputs'}
    return aa==bb and {ref_key(x) for x in a['inputs']}=={ref_key(x) for x in b['inputs']}

def syntax_errors(doc: Any) -> list[str]:
    if not isinstance(doc,dict): return ['Document must be a JSON object']
    kind=doc.get('kind')
    if not isinstance(kind,str) or kind not in KINDS:return [f'Unknown document kind: {kind!r}']
    schema={'$schema':SCHEMA['$schema'],'$defs':SCHEMA['$defs'],'$ref':'#/$defs/'+KINDS[kind]}
    v=Draft202012Validator(schema,format_checker=FormatChecker())
    return [f"{'/'.join(map(str,e.absolute_path)) or '$'}: {e.message}" for e in sorted(v.iter_errors(doc),key=lambda e:str(list(e.absolute_path)))]

def packet_errors(p: Doc) -> list[str]:
    errors=[]; role=ROLES[p['role']]
    if p['delegation']!=role['delegation']:errors.append('delegation does not agree with role registry')
    if not set(p['requested_capabilities'])<=set(role['capabilities']):errors.append('requested capabilities exceed role authority')
    for field,key in [('prerequisites','name'),('outputs','name'),('checks','check_id')]:
        if duplicates([x[key] for x in p[field]]):errors.append(f'duplicate {field} names')
    names={x['name'] for x in p['prerequisites']};outs={x['name'] for x in p['outputs']}
    if p['baseline_input'] is not None and p['baseline_input'] not in names:errors.append('baseline_input not found in prerequisites')
    if p['role'] in {'implementer','integrator'} and p['baseline_input'] is None:errors.append('source-writing role requires baseline_input')
    w=p['workspace_policy']
    if w['mode'] in {'read-only','none'} and w['write_paths']:errors.append('read-only/none workspace cannot declare source write_paths')
    if p['role'] in {'reviewer','verifier','diagnostician'} and w['mode']=='isolated-write':errors.append('checker/diagnostician requires read-only inspected source')
    if w['mode']=='isolated-write' and 'edit_workspace' not in p['requested_capabilities']:errors.append('isolated-write requires edit_workspace capability')
    for out in p['outputs']:
        if out['artifact_type'] not in role['outputs']:errors.append(f"role cannot produce named artifact type {out['artifact_type']}")
    for c in p['checks']:
        prefix,sep,name=c['subject'].partition(':')
        if not sep or prefix not in {'input','output'} or name not in (names if prefix=='input' else outs):errors.append(f"invalid check subject: {c['subject']}")
        if c['method'] in {'test','build','integration'}:
            if c['command'] is None:errors.append('command check requires command')
            if 'run_commands' not in p['requested_capabilities']:errors.append('command check requires run_commands capability')
    return errors

def dispatch_errors(d: Doc) -> list[str]:
    p=d['packet'];errors=packet_errors(p)
    if d['project_id']!=p['project_id']:errors.append('dispatch project differs from packet')
    if d['packet_sha256']!=canonical_hash(p):errors.append('packet_sha256 does not match authoritative packet')
    if d['recipient']['role']!=p['role']:errors.append('recipient role differs from packet role')
    if d['recipient']['skill']!=ROLES[p['role']]['skill']:errors.append('recipient skill differs from role registry')
    grants=set(d['grant']['capabilities'])
    if not grants<=set(p['requested_capabilities']) or not grants<=set(ROLES[p['role']]['capabilities']):errors.append('grant exceeds requested or role capabilities')
    if dt(d['lease']['expires_at'])<=dt(d['issued_at']):errors.append('lease expires before dispatch was issued')
    bindings={i['name']:i for i in d['inputs']}
    if len(bindings)!=len(d['inputs']) or set(bindings)!={x['name'] for x in p['prerequisites']}:errors.append('resolved input names must exactly match prerequisites')
    for x in p['prerequisites']:
        b=bindings.get(x['name'])
        if b is None:continue
        if 'artifact' in x['source'] and x['source']['artifact']!=b['artifact']:errors.append(f"pinned input mismatch: {x['name']}")
        if x['required_gates'] and not b['attestations']:errors.append(f"missing attestation references: {x['name']}")
    base=bindings.get(p['baseline_input']) if p['baseline_input'] else None
    if d['workspace']['baseline']!=(base['artifact'] if base else None):errors.append('workspace baseline does not match baseline input')
    return errors

def validate_document(doc: Any,live: bool=False) -> list[str]:
    errors=syntax_errors(doc)
    if errors:return errors
    kind=doc['kind']
    if live and (doc.get('example',False) or (kind=='dispatch' and doc['packet'].get('example',False))):errors.append('synthetic example is forbidden in live validation')
    if kind=='packet':errors+=packet_errors(doc)
    elif kind=='dispatch':errors+=dispatch_errors(doc)
    elif kind=='result':
        if dt(doc['finished_at'])<dt(doc['started_at']):errors.append('result finished before it started')
        if doc['status']!='completed' and not doc['issues']:errors.append('non-completed result requires a structured issue')
        if duplicates([x['name'] for x in doc['outputs']]):errors.append('duplicate output names')
    elif kind=='evidence':
        if duplicates([ref_key(r) for r in doc['context']['inputs']]):errors.append('duplicate evidence context input')
        if doc['method'] in {'test','build','integration'}:
            if doc['command'] is None:errors.append('command evidence requires command')
            if doc['exit_code'] is None and doc['verdict']!='inconclusive':errors.append('command evidence requires exit_code')
            if doc['verdict']=='pass' and doc['exit_code']!=0:errors.append('passing command requires exit_code zero')
    elif kind=='policy':
        if duplicates([g['gate_id'] for g in doc['gates']]):errors.append('duplicate policy gate')
        for g in doc['gates']:
            if duplicates([c['check_id'] for c in g['required_checks']]):errors.append('duplicate required check in gate')
    return errors

def validate_result(d: Doc,r: Doc,artifacts: dict[str,Doc]|None=None,evidence: dict[str,Doc]|None=None,current_fence: int|None=None) -> list[str]:
    errors=validate_document(d)+validate_document(r)
    if errors:return errors
    p=d['packet']
    expected={
        'project_id':d['project_id'],'dispatch_id':d['dispatch_id'],'attempt_id':d['attempt_id'],
        'task_id':p['task_id'],'packet_revision':p['packet_revision'],'packet_sha256':d['packet_sha256'],
        'lease_id':d['lease']['lease_id'],'fence':d['lease']['fence'],
        'agent_id':d['recipient']['agent_id'],'role':d['recipient']['role']}
    for k,v in expected.items():
        if r[k]!=v:errors.append(f'result {k} does not match dispatch')
    if current_fence is not None and r['fence']!=current_fence:errors.append('stale result fence')
    if dt(r['started_at'])<dt(d['issued_at']):errors.append('result started before dispatch')
    outs={o['name']:o for o in p['outputs']};actual={o['name']:o['artifact'] for o in r['outputs']}
    if not set(actual)<=set(outs):errors.append('undeclared output in result')
    if r['status']=='completed':
        for name,o in outs.items():
            if o['required'] and name not in actual:errors.append(f'missing required output: {name}')
    if artifacts is not None:
        for name,reference in actual.items():
            m=artifacts.get(reference['artifact_id'])
            if m is None:errors.append('unknown output artifact');continue
            if m['sha256']!=reference['sha256']:errors.append('output artifact hash mismatch')
            if name in outs and m['artifact_type']!=outs[name]['artifact_type']:errors.append('output artifact type mismatch')
            if m['producer']!={'task_id':p['task_id'],'attempt_id':d['attempt_id'],'dispatch_id':d['dispatch_id']}:errors.append('output provenance mismatch')
            if r['agent_id'] not in m['authors']:errors.append('output author mismatch')
    if evidence is not None:
        checks={c['check_id']:c for c in p['checks']};seen=set();bindings={i['name']:i['artifact'] for i in d['inputs']}
        for reference in r['evidence']:
            e=evidence.get(reference['artifact_id'])
            if e is None:errors.append('unknown evidence artifact');continue
            seen.add(e['check_id'])
            if e['dispatch_id']!=d['dispatch_id'] or e['attempt_id']!=d['attempt_id'] or e['issuer']!={'agent_id':r['agent_id'],'role':r['role']}:errors.append('evidence origin differs from result')
            c=checks.get(e['check_id'])
            if c is None:errors.append('undeclared check in evidence');continue
            prefix,_,name=c['subject'].partition(':');subject=(bindings if prefix=='input' else actual).get(name)
            if subject!=e['subject']:errors.append('check evidence subject differs from packet')
            if c['method']!=e['method']:errors.append('evidence method differs from packet')
            if e['context']['policy']!=p['acceptance_policy']:errors.append('evidence policy differs from packet')
            if e['context']['baseline']!=d['workspace']['baseline']:errors.append('evidence baseline differs from dispatch')
            if not {ref_key(x) for x in e['context']['inputs']}<={ref_key(x['artifact']) for x in d['inputs']}:errors.append('evidence context includes undeclared inputs')
            if e['method'] in {'test','build','integration'} and e['command']!=c['command']:errors.append('evidence command differs from packet')
            if r['status']=='completed' and r['role'] not in {'reviewer','verifier'} and c['required'] and e['verdict']!='pass':errors.append('required local check did not pass')
        if r['status']=='completed':
            for c in checks.values():
                if c['required'] and c['check_id'] not in seen:errors.append(f"missing required check evidence: {c['check_id']}")
    return errors

def validate_graph(g: Doc,policy: Doc|None=None) -> list[str]:
    errors=validate_document(g)
    if errors:return errors
    tasks={p['task_id']:p for p in g['tasks']};reqs=set(g['requirement_ids']);roots={ref_key(a) for a in g['external_artifacts']}
    if len(tasks)!=len(g['tasks']):errors.append('duplicate graph task ID')
    gates={x['gate_id']:x for x in policy['gates']} if policy else None
    edges={t:set() for t in tasks}
    for p in g['tasks']:
        errors += [p['task_id']+': '+e for e in packet_errors(p)]
        if p['project_id']!=g['project_id'] or p['graph_revision']!=g['graph_revision']:errors.append('task project/graph revision mismatch')
        if p['acceptance_policy']!=g['acceptance_policy']:errors.append('task acceptance policy mismatch')
        if not set(p['requirement_ids'])<=reqs:errors.append('unknown requirement in task')
        for x in p['prerequisites']:
            source=x['source'];otype=None
            if 'artifact' in source:
                if ref_key(source['artifact']) not in roots:errors.append('unregistered external artifact')
            else:
                producer=tasks.get(source['producer_task'])
                if producer is None:errors.append(f"unknown producer: {source['producer_task']}");continue
                edges[p['task_id']].add(source['producer_task'])
                found=next((o for o in producer['outputs'] if o['name']==source['output_name']),None)
                if found is None:errors.append('unknown output of producer');continue
                otype=found['artifact_type']
                if x['class']=='contract' and otype!='contract':errors.append('contract prerequisite has non-contract producer')
                if x['class']=='implementation' and otype not in {'source','build','baseline','test-suite','integration-manifest','release-manifest'}:errors.append('implementation prerequisite has incompatible producer')
            if gates is not None:
                for gate in x['required_gates']:
                    if gate not in gates:errors.append(f'unknown gate: {gate}')
                    elif otype is not None and gates[gate]['subject_type']!=otype:errors.append('gate subject type incompatible with producer')
    # Gates add real proof dependencies even when the candidate itself already exists.
    # This protocol version requires one canonical checking task per required gate check.
    def source_key(source):
        if 'artifact' in source:return ('artifact',*ref_key(source['artifact']))
        return ('output',source['producer_task'],source['output_name'])
    check_producers={}
    for candidate in g['tasks']:
        inputs={x['name']:x['source'] for x in candidate['prerequisites']}
        for check in candidate['checks']:
            prefix,sep,name=check['subject'].partition(':')
            source=inputs.get(name) if prefix=='input' else {'producer_task':candidate['task_id'],'output_name':name}
            if not sep or source is None:continue
            key=(source_key(source),check['check_id'])
            check_producers.setdefault(key,[]).append((candidate['task_id'],candidate['role']))
    if gates is not None:
        for consumer in g['tasks']:
            for prerequisite in consumer['prerequisites']:
                source=prerequisite['source']
                if 'artifact' in source:continue # Root evidence is supplied/authenticated externally.
                for gate_id in prerequisite['required_gates']:
                    gate=gates.get(gate_id)
                    if gate is None:continue
                    for check in gate['required_checks']:
                        candidates=[task for task,role in check_producers.get((source_key(source),check['check_id']),[]) if role in check['allowed_roles']]
                        if not candidates:errors.append(f"missing gate producer: {gate_id}/{check['check_id']}")
                        elif len(candidates)>1:errors.append(f"ambiguous gate producer: {gate_id}/{check['check_id']}")
                        else:edges[consumer['task_id']].add(candidates[0])
    active=set();done=set()
    def visit(task):
        if task in active:errors.append('dependency cycle detected');return
        if task in done:return
        active.add(task)
        for parent in edges[task]:visit(parent)
        active.remove(task);done.add(task)
    for task in tasks:visit(task)
    covered=[c['requirement_id'] for c in g['coverage']]
    if set(covered)!=reqs or duplicates(covered):errors.append('requirements coverage is incomplete or duplicated')
    for c in g['coverage']:
        for name in c['implementation_tasks']+c['acceptance_tasks']:
            if name not in tasks:errors.append('coverage references unknown task')
            elif c['requirement_id'] not in tasks[name]['requirement_ids']:errors.append('coverage task does not declare requirement')
    if not set(g['release_tasks'])<=set(tasks):errors.append('unknown release task')
    return errors

def validate_attestation(a: Doc,evidence: dict[str,Doc],artifacts: dict[str,Doc],policy: Doc) -> list[str]:
    errors=validate_document(a)+validate_document(policy)
    if errors:return errors
    gate=next((g for g in policy['gates'] if g['gate_id']==a['gate_id']),None)
    if gate is None:return ['unknown gate in attestation']
    subject=artifacts.get(a['subject']['artifact_id'])
    if subject is None:return ['unknown attestation subject']
    if subject['sha256']!=a['subject']['sha256']:errors.append('attestation subject hash mismatch')
    if subject['artifact_type']!=gate['subject_type']:errors.append('attestation subject type mismatch')
    seen={}
    for reference in a['evidence']:
        e=evidence.get(reference['artifact_id'])
        if e is None:errors.append('unknown attestation evidence');continue
        if e['subject']!=a['subject']:errors.append('attestation evidence subject mismatch')
        if not same_context(e['context'],a['context']):errors.append('attestation evidence context mismatch')
        if e['verdict']!='pass':errors.append('attestation evidence is not pass')
        seen.setdefault(e['check_id'],[]).append(e)
    for required in gate['required_checks']:
        items=seen.get(required['check_id'],[])
        if not items:errors.append('missing required gate check');continue
        for e in items:
            if e['issuer']['role'] not in required['allowed_roles']:errors.append('gate check issuer role not allowed')
            if required['independent'] and e['issuer']['agent_id'] in subject['authors']:errors.append('independent check performed by subject author')
    return errors

def walk_refs(value: Any):
    if isinstance(value,dict):
        if set(value)=={'artifact_id','sha256'}:yield value
        else:
            for child in value.values():yield from walk_refs(child)
    elif isinstance(value,list):
        for child in value:yield from walk_refs(child)

def validate_artifact_payload(artifact: Doc,root: Path) -> list[str]:
    uri=artifact['uri']
    if '://' in uri:return [] # External artifacts require host retrieval/authentication.
    path=(root/uri).resolve()
    if not path.is_relative_to(root.resolve()):return ['artifact path escapes bundle root']
    if not path.is_file():return [f'artifact payload is missing: {uri}']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=artifact['sha256']:return [f'artifact payload hash mismatch: {uri}']
    return []

def load_bundle(root: Path) -> dict[str,Any]:
    root=Path(root);docs={}
    for path in sorted(root.rglob('*.json')):
        doc=parse_json(path.read_text(encoding='utf-8'))
        if isinstance(doc,dict) and 'kind' in doc:docs[str(path.relative_to(root))]=doc
    artifacts={d['artifact_id']:d for d in docs.values() if d.get('kind')=='artifact'}
    by_uri={str((root/m['uri']).resolve()):aid for aid,m in artifacts.items() if '://' not in m['uri']}
    evidence={by_uri[str((root/p).resolve())]:d for p,d in docs.items() if d['kind']=='evidence' and str((root/p).resolve()) in by_uri}
    attestations={by_uri[str((root/p).resolve())]:d for p,d in docs.items() if d['kind']=='attestation' and str((root/p).resolve()) in by_uri}
    return {'docs':docs,'artifacts':artifacts,'evidence':evidence,'attestations':attestations}

def validate_bundle(root: Path,live: bool=False) -> list[str]:
    root=Path(root)
    try:b=load_bundle(root)
    except (OSError,ValueError,KeyError) as exc:return [f'Cannot load bundle: {exc}']
    errors=[];docs=b['docs'];arts=b['artifacts']
    if not docs:return ['No protocol documents found']
    for path,doc in docs.items():
        errors += [path+': '+e for e in validate_document(doc,live)]
    if errors:return errors # Do not interpret structurally invalid input.
    if len(arts)!=sum(d['kind']=='artifact' for d in docs.values()):errors.append('duplicate artifact IDs')
    for aid,a in arts.items():errors += [aid+': '+e for e in validate_artifact_payload(a,root)]
    for path,doc in docs.items():
        for r in walk_refs(doc):
            a=arts.get(r['artifact_id'])
            if a is None or a['sha256']!=r['sha256']:errors.append(f"{path}: unresolved artifact reference {r['artifact_id']}")
    dispatches={d['dispatch_id']:d for d in docs.values() if d['kind']=='dispatch'}
    policies={str((root/m['uri']).resolve()):aid for aid,m in arts.items() if m['artifact_type']=='policy' and '://' not in m['uri']}
    policy_docs={policies[str((root/p).resolve())]:d for p,d in docs.items() if d['kind']=='policy' and str((root/p).resolve()) in policies}
    for path,doc in docs.items():
        local=[]
        if doc['kind']=='result':
            dispatch=dispatches.get(doc['dispatch_id'])
            if dispatch is None:local.append('result has no dispatch in bundle')
            else:local += validate_result(dispatch,doc,arts,b['evidence'])
        elif doc['kind']=='graph':local += validate_graph(doc,policy_docs.get(doc['acceptance_policy']['artifact_id']))
        elif doc['kind']=='attestation':
            policy=policy_docs.get(doc['context']['policy']['artifact_id'])
            if policy is None:local.append('attestation policy is not available')
            else:local += validate_attestation(doc,b['evidence'],arts,policy)
        elif doc['kind']=='dispatch':
            for p in doc['packet']['prerequisites']:
                binding=next(x for x in doc['inputs'] if x['name']==p['name'])
                claims=[b['attestations'].get(r['artifact_id']) for r in binding['attestations']]
                for gate in p['required_gates']:
                    if not any(a and a['gate_id']==gate and a['subject']==binding['artifact'] and a['context']['policy']==doc['packet']['acceptance_policy'] for a in claims):local.append(f"input {p['name']} lacks matching attestation for {gate}")
        errors += [path+': '+e for e in local]
    return errors

def main(argv: list[str]|None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path',type=Path,help='One JSON protocol document, or a self-contained example bundle directory')
    parser.add_argument('--live',action='store_true',help='Reject synthetic examples; does not authenticate or execute anything')
    args=parser.parse_args(argv)
    try:
        if args.path.is_dir():errors=validate_bundle(args.path,args.live)
        else:errors=validate_document(parse_json(args.path.read_text(encoding='utf-8')),args.live)
    except (OSError,ValueError) as exc:errors=[str(exc)]
    if errors:
        print('\n'.join(errors),file=sys.stderr);print(f'FAIL: {len(errors)} static validation issue(s)',file=sys.stderr);return 1
    print('PASS: static protocol validation. No live authority, scheduling, or product correctness was tested.');return 0

if __name__=='__main__':raise SystemExit(main())
