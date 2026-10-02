#!/usr/bin/env python3
"""CM cross-chat handoff validator/packer. No execution, authentication, or scheduling.

Python 3.10+ and jsonschema>=4.18,<5. Run --help for commands.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any
import zipfile
from jsonschema import Draft202012Validator, FormatChecker
BASE=Path(__file__).resolve().parents[1]
_spec=importlib.util.spec_from_file_location('cm_worker_validator_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:10],BASE/'scripts/validate.py')
v=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(v)
SCHEMA=v.parse_json((BASE/'assets/handoff.schema.json').read_text(encoding='utf-8'))
KINDS={'plan-handoff':'handoff','plan-receipt':'receipt','replan-request':'replan'}
LOCK_FILES=['assets/handoff.schema.json','assets/protocol.schema.json','assets/roles.json','references/HANDOFF.md','references/PROTOCOL.md','scripts/handoff.py','scripts/validate.py']

def digest(path: Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def contract_files()->dict[str,str]:return {name:digest(BASE/name) for name in LOCK_FILES}
def contract_digest()->str:return v.canonical_hash(contract_files())
def contract_errors()->list[str]:
    try:
        lock=v.parse_json((BASE/'assets/contract-lock.json').read_text(encoding='utf-8'))
        return [] if lock=={'profile':'cm-two-skill/1.0','files':contract_files(),'sha256':contract_digest()} else ['Installed contract-lock does not match contract files']
    except (OSError,ValueError) as e:return [f'Cannot verify installed contract-lock: {e}']

def safe_path(root: Path,name: str)->Path:
    """Require portable relative paths; reject symlinks even when staying in root."""
    p=PurePosixPath(name)
    if not name or '\\' in name or ':' in name or p.is_absolute() or any(x in {'','..','.'} for x in name.split('/')):
        raise ValueError(f'Unsafe bundle path: {name}')
    at=root
    for part in p.parts:
        at=at/part
        if at.is_symlink():raise ValueError(f'Symlink path forbidden: {name}')
    if not at.resolve().is_relative_to(root.resolve()):raise ValueError(f'Path escapes bundle: {name}')
    return at

def load(path: Path)->Any:return v.parse_json(path.read_text(encoding='utf-8'))
def syntax(doc: Any)->list[str]:
    if not isinstance(doc,dict) or doc.get('kind') not in KINDS:return ['Unknown CM handoff document kind']
    schema={'$schema':SCHEMA['$schema'],'$defs':SCHEMA['$defs'],'$ref':'#/$defs/'+KINDS[doc['kind']]}
    return [f"{'/'.join(map(str,e.absolute_path)) or '$'}: {e.message}" for e in Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(doc)]

def validate_control(doc: Any,live: bool=False)->list[str]:
    errors=syntax(doc)
    if errors:return errors
    errors+=contract_errors()
    if doc['contract_sha256']!=contract_digest():errors.append('Handoff contract fingerprint mismatch')
    if live and doc['example']:errors.append('Synthetic example is forbidden in live intake')
    if doc['kind']=='plan-receipt':
        if doc['status']!='rejected':
            if not doc['authorization_ref']:errors.append('Accepted receipt needs actual host authorization reference')
            if not doc['ledger_location']:errors.append('Accepted receipt needs ledger location')
            if doc['execution_mode']=='unavailable':errors.append('Accepted receipt cannot have unavailable execution mode')
        if doc['status']=='accepted' and (doc['blocked_tasks'] or doc['issues']):errors.append('Accepted receipt with blockers must use accepted-with-blockers')
        if doc['status']!='accepted' and not doc['issues']:errors.append('Blocked/rejected receipt needs structured issues')
    return errors

def _source_key(source: dict)->str:return v.canonical_hash(source)
def graph_gate_errors(g: dict,policy: dict,completion: dict)->list[str]:
    """Evidence-expanded edges include root gates, not only produced-code gates."""
    errors=[];tasks={t['task_id']:t for t in g['tasks']};gates={x['gate_id']:x for x in policy['gates']}
    producers={};edges={t:set() for t in tasks}
    for t in tasks.values():
        inputs={p['name']:p for p in t['prerequisites']}
        for c in t['checks']:
            if not c['required']:continue
            side,name=c['subject'].split(':',1)
            source=inputs[name]['source'] if side=='input' else {'producer_task':t['task_id'],'output_name':name}
            producers.setdefault((_source_key(source),c['check_id']),[]).append((t['task_id'],t['role']))
    def checks(source,gateid):
        gate=gates.get(gateid)
        if not gate:
            errors.append(f'Unknown completion/prerequisite gate: {gateid}');return []
        found=[]
        for check in gate['required_checks']:
            pp=[tid for tid,role in producers.get((_source_key(source),check['check_id']),[]) if role in check['allowed_roles']]
            if len(pp)!=1:errors.append(f'Missing or ambiguous gate producer: {gateid}/{check["check_id"]}')
            found.extend(pp)
        return found
    for t in tasks.values():
        for p in t['prerequisites']:
            source=p['source']
            if 'producer_task' in source:edges[t['task_id']].add(source['producer_task'])
            for gate in p['required_gates']:edges[t['task_id']].update(checks(source,gate))
    subject=completion['product_subject'];product=tasks.get(subject['producer_task'])
    output=next((x for x in product['outputs'] if x['name']==subject['output_name']),None) if product else None
    if not output:errors.append('Unknown product completion producer/output')
    for gateid in completion['required_gates']:
        checks(subject,gateid)
        if output and gateid in gates and gates[gateid]['subject_type']!=output['artifact_type']:errors.append('Completion gate subject type mismatch')
    active=set();seen=set()
    def visit(n):
        if n in active:errors.append('Evidence-expanded dependency cycle (including root gate checks)');return
        if n in seen:return
        active.add(n)
        for x in edges.get(n,()):visit(x)
        active.remove(n);seen.add(n)
    for n in edges:visit(n)
    return errors

def validate_handoff(root: Path,live: bool=False)->list[str]:
    root=Path(root)
    try:
        manifest=safe_path(root,'HANDOFF.json');d=load(manifest)
        errors=validate_control(d,live)
        if errors:return errors
        if d['kind']!='plan-handoff':return ['HANDOFF.json must be a plan-handoff']
        names=[x['path'] for x in d['files']]
        if len(names)!=len({x.casefold() for x in names}):errors.append('Duplicate or case-colliding bundle paths')
        if any(x.casefold()=='handoff.json' for x in names):errors.append('Manifest cannot hash itself')
        checked={}
        for f in d['files']:
            try:
                p=safe_path(root,f['path'])
                if not p.is_file():errors.append(f'Bundle file missing: {f["path"]}');continue
                if digest(p)!=f['sha256']:errors.append(f'Bundle file hash mismatch: {f["path"]}');continue
                checked[f['path']]=p
            except (ValueError,OSError) as e:errors.append(str(e))
        for p in root.rglob('*'):
            if p.is_symlink():errors.append(f'Symlink forbidden: {p.relative_to(root)}')
            if p.is_file() and p!=manifest and p.relative_to(root).as_posix() not in names:errors.append(f'Unlisted payload: {p.relative_to(root)}')
        required=[d[k] for k in ['summary_path','requirements_path','graph_path','policy_path']]+[d['environment']['setup_path'],d['environment']['verification_path']]+[r['path'] for r in d['root_artifacts']]
        for name in required:
            safe_path(root,name)
            if name not in checked:errors.append(f'Referenced path is missing or unverified: {name}')
        if errors:return errors
        for name,p in checked.items():
            if p.suffix.lower()=='.json':
                doc=load(p)
                if isinstance(doc,dict) and doc.get('protocol')=='cdag/1.0' and doc.get('kind') in {'dispatch','result','attestation','evidence','event'}:
                    errors.append(f'Planner bundle must not import runtime state: {name}')
        g=load(checked[d['graph_path']]);policy=load(checked[d['policy_path']])
        structural=v.validate_document(g,live)+v.validate_document(policy,live)
        if structural:return errors+structural
        if g['kind']!='graph' or policy['kind']!='policy':return errors+['Graph/policy path contains wrong document kind']
        if g['project_id']!=d['project_id'] or policy['project_id']!=d['project_id']:errors.append('Handoff/graph/policy project mismatch')
        for t in g['tasks']:
            if live and t.get('example'):errors.append('Synthetic packet forbidden in live intake')
        errors+=v.validate_graph(g,policy)
        roots={r['artifact_id']:r for r in d['root_artifacts']}
        if len(roots)!=len(d['root_artifacts']):errors.append('Duplicate root artifact IDs')
        if len({r['path'] for r in roots.values()})!=len(roots):errors.append('Duplicate root artifact payload paths')
        if {(r['artifact_id'],r['sha256']) for r in d['root_artifacts']}!={(r['artifact_id'],r['sha256']) for r in g['external_artifacts']}:errors.append('Graph external roots do not match bundled root artifacts')
        for r in roots.values():
            if digest(checked[r['path']])!=r['sha256']:errors.append(f'Root artifact hash mismatch: {r["artifact_id"]}')
        gates={gate['gate_id']:gate for gate in policy['gates']}
        for task in g['tasks']:
            for pre in task['prerequisites']:
                if 'artifact' not in pre['source']:continue
                r=roots.get(pre['source']['artifact']['artifact_id'])
                if not r:continue
                typ=r['artifact_type']
                if pre['class']=='contract' and typ!='contract':errors.append('Contract prerequisite root type is incompatible')
                if pre['class']=='implementation' and typ not in {'source','build','baseline','test-suite'}:errors.append('Implementation prerequisite root type is incompatible')
                if task['baseline_input']==pre['name'] and typ not in {'baseline','source'}:errors.append('Baseline prerequisite root type is incompatible')
                for gid in pre['required_gates']:
                    if gid in gates and gates[gid]['subject_type']!=typ:errors.append('Gate prerequisite root type is incompatible')
        pref=g['acceptance_policy'];pr=roots.get(pref['artifact_id'])
        if not pr or pr['path']!=d['policy_path'] or pr['sha256']!=pref['sha256'] or pr['artifact_type']!='policy':errors.append('Graph policy pin does not match policy root')
        if not any(r['path']==d['requirements_path'] and r['artifact_type']=='requirements' for r in roots.values()):errors.append('Requirements snapshot must be a root artifact')
        if d['baseline']['mode']=='git' and d['baseline']['commit'] is None:errors.append('Git baseline requires an exact commit')
        if d['baseline']['mode']=='new-repository' and d['baseline']['commit'] is not None:errors.append('New-repository baseline commit must be null')
        if d['baseline']['repository_hint'].startswith(('/','~')) or re_drive(d['baseline']['repository_hint']):errors.append('Repository hint must be portable, not an absolute planner path')
        tids={t['task_id'] for t in g['tasks']}
        for a in d['assumptions']:
            if not set(a['affected_tasks'])<=tids:errors.append('Assumption references unknown affected task')
            if a['resolution']=='requires-decision':
                if d['status']!='partial':errors.append('Unresolved assumptions require partial status')
                if not a['affected_tasks']:errors.append('Unresolved assumption requires affected tasks')
        if d['revision']==1 and d['parent'] is not None:errors.append('Initial revision must not have a parent')
        if d['revision']>1 and (d['parent'] is None or d['parent']['plan_id']!=d['plan_id'] or d['parent']['revision']!=d['revision']-1):errors.append('Revision parent must identify the preceding revision of this plan')
        if not errors:errors+=graph_gate_errors(g,policy,d['completion'])
        return errors
    except (OSError,ValueError,KeyError,TypeError,RecursionError) as e:
        return [f'Cannot validate handoff: {e}']

def re_drive(s: str)->bool:return len(s)>1 and s[1]==':'
def seal(root: Path)->list[str]:
    """Explicit authoring operation. Refresh listed bytes, not approval or execution."""
    root=Path(root);d=load(root/'HANDOFF.json');files=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise ValueError(f'Symlink forbidden: {p}')
        if p.is_file() and p.name!='HANDOFF.json':
            rel=p.relative_to(root).as_posix();safe_path(root,rel);files.append({'path':rel,'sha256':digest(p)})
    d['files']=files;d['contract_sha256']=contract_digest()
    (root/'HANDOFF.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return validate_handoff(root)

def main(argv=None)->int:
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='cmd',required=True)
    for name in ['validate','seal','pack']:
        s=sub.add_parser(name);s.add_argument('path',type=Path);s.add_argument('--live',action='store_true')
        if name=='pack':s.add_argument('--output',type=Path,required=True)
    sub.add_parser('fingerprint');a=ap.parse_args(argv)
    try:
        if a.cmd=='fingerprint':
            errors=contract_errors()
            if errors:raise ValueError('; '.join(errors))
            print(contract_digest());return 0
        if a.cmd=='seal':errors=seal(a.path)
        elif a.path.is_dir():errors=validate_handoff(a.path,a.live)
        elif a.cmd=='validate' and a.path.name!='HANDOFF.json':errors=validate_control(load(a.path),a.live)
        else:errors=validate_handoff(a.path.parent,a.live)
        if a.live and a.cmd=='seal':errors+=validate_handoff(a.path,True)
        if errors:raise ValueError('\n'.join(errors))
        if a.cmd=='pack':
            if not a.path.is_dir():raise ValueError('pack requires a bundle directory')
            d=load(a.path/'HANDOFF.json')
            if a.output.resolve().is_relative_to(a.path.resolve()):raise ValueError('Output ZIP must be outside the immutable bundle')
            with zipfile.ZipFile(a.output,'x',zipfile.ZIP_DEFLATED) as z:
                for name in ['HANDOFF.json']+[f['path'] for f in d['files']]:z.write(safe_path(a.path,name),name)
            print(f'Packaged: {a.output}')
        manifest=(a.path/'HANDOFF.json') if a.path.is_dir() else a.path
        print(f'PASS: static CM handoff validation; sha256={digest(manifest)}')
        print('No execution, repository verification, trust authentication, or product acceptance was performed.')
        return 0
    except (OSError,ValueError,KeyError,TypeError) as e:
        print('FAIL: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
