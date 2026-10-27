"""Offline contract, authentication and JSON-RPC tests, without backend/network."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/choms-memory'))
sys.path.insert(0,str(ROOT/'tools/choms-skills/skills/choms-memory-governance/scripts'))
import contract


def payload(**changes):
    value={'scope':'project','project_id':'choms-memory-e2e-unit','summary':'Synthetic violet satellite decision',
           'source_kind':'user_explicit','source_reference':'fixture:unit','topic':'synthetic','importance':'high'}
    value.update(changes)
    return value


class ContractTests(unittest.TestCase):
    def test_exact_tools(self):
        self.assertEqual([t['name'] for t in contract.TOOLS],list(contract.OPERATIONS))
        self.assertEqual(len(contract.TOOLS),8)
    def test_all_scopes(self):
        for scope in ('global','personal','project'):
            p=payload(scope=scope,project_id='synthetic' if scope=='project' else None)
            self.assertEqual(contract.record_input(p,explicit=True)['scope'],scope)
    def test_explicit_active(self):
        self.assertEqual(contract.record_input(payload(),explicit=True)['state'],'active')
    def test_inferred_candidate(self):
        r=contract.record_input(payload(source_kind='agent_inferred'),explicit=False)
        self.assertEqual(r['state'],'candidate')
    def test_duplicate_normalization(self):
        a=contract.record_input(payload(summary='Synthetic violet satellite'),explicit=True)
        b=contract.record_input(payload(summary='synthetic  VIOLET satellite!'),explicit=True)
        self.assertEqual(a['content_hash'],b['content_hash'])
    def test_no_real_memory(self):
        with self.assertRaises(contract.Fault):contract.record_input(payload(source_reference='user:real'),explicit=True)
    def test_secret(self):
        value='pass'+'word='+''.join(chr(65+i%20) for i in range(30))
        with self.assertRaises(contract.Fault):contract.record_input(payload(summary=value),explicit=True)
    def test_poisoned_sources(self):
        for source in ('web','repository','tool'):
            with self.assertRaises(contract.Fault):contract.record_input(payload(source_kind=source),explicit=True)
    def test_ambiguous_consent(self):
        with self.assertRaises(contract.Fault):contract.record_input(payload(source_kind='agent_inferred'),explicit=True)
    def test_project_required(self):
        with self.assertRaises(contract.Fault):contract.partition({'scope':'project'})
    def test_global_project_rejected(self):
        with self.assertRaises(contract.Fault):contract.partition({'scope':'global','project_id':'synthetic'})
    def test_extra_fields(self):
        with self.assertRaises(contract.Fault):contract.arguments('health',{'command':'synthetic'})
    def test_boolean_type(self):
        with self.assertRaises(contract.Fault):contract.arguments('search',{'scope':'global','query':'synthetic','include_low':'false'})
    def test_missing_cas(self):
        with self.assertRaises(contract.Fault):contract.arguments('remember',{'request_id':str(uuid.uuid4()),'id':str(uuid.uuid4()),'explicit':True})
    def test_bad_uuid(self):
        with self.assertRaises(contract.Fault):contract.identifier('../outside')
    def test_budget(self):
        rows=[contract.record_input(payload(summary='Synthetic '+str(i)),explicit=True) for i in range(10)]
        result=contract.bounded(rows,{'limit':2,'budget_chars':2400})
        self.assertLessEqual(len(result['records']),2);self.assertLessEqual(result['characters'],2400)
    def test_invalid_budget(self):
        with self.assertRaises(contract.Fault):contract.bounded([],{'budget_chars':100000})
    def test_checkpoint(self):
        self.assertEqual(contract.record_input(payload(),explicit=True,checkpoint=True)['type'],'checkpoint')


class RpcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        previous=sys.modules.get('backend');sys.modules['backend']=types.SimpleNamespace(Backend=object)
        spec=importlib.util.spec_from_file_location('choms_rpc_test',ROOT/'tools/choms-memory/server.py')
        cls.server=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.server)
        if previous is None:del sys.modules['backend']
        else:sys.modules['backend']=previous
    def test_handshake(self):
        r=self.server.rpc({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18'}})
        self.assertEqual(r['result']['protocolVersion'],'2025-06-18')
    def test_tools(self):
        self.assertEqual(len(self.server.rpc({'jsonrpc':'2.0','id':2,'method':'tools/list'})['result']['tools']),8)
    def test_notification(self):
        self.assertIsNone(self.server.rpc({'jsonrpc':'2.0','method':'notifications/initialized'}))
    def test_auth_fail_closed(self):
        self.server.TOKENS={'codex':'a'*40,'hermes':'b'*40}
        self.assertFalse(self.server.authenticated(''))
        self.assertFalse(self.server.authenticated('Bearer '+'x'*40))
        self.assertTrue(self.server.authenticated('Bearer '+'a'*40))
    def test_backend_error_is_sanitized(self):
        class Fake:
            def call(self,*args):raise RuntimeError('synthetic private content must not leak')
        self.server.BACKEND=Fake()
        r=self.server.rpc({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'health','arguments':{}}})
        self.assertNotIn('private',json.dumps(r));self.assertTrue(r['result']['isError'])
    def test_structured_cas_error(self):
        class Fake:
            def call(self,*args):raise contract.Fault('cas_conflict')
        self.server.BACKEND=Fake()
        r=self.server.rpc({'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'supersede','arguments':{}}})
        self.assertEqual(r['result']['structuredContent']['error']['code'],'cas_conflict')

class ClientFramingTests(unittest.TestCase):
    def test_hermes_error_wrapper(self):
        sys.path.insert(0,str(ROOT/'scripts/memory'))
        from memory_mcp_e2e import unwrap
        expected={'ok':False,'error':{'code':'cas_conflict','retryable':False}}
        self.assertEqual(unwrap({'error':json.dumps(expected)}),expected)
    def test_hermes_success_wrapper(self):
        from memory_mcp_e2e import unwrap
        expected={'ok':True,'data':{'status':'ready'}}
        self.assertEqual(unwrap({'content':[{'type':'text','text':json.dumps(expected)}]}),expected)
    def test_invalid_framing_rejected(self):
        from memory_mcp_e2e import unwrap
        with self.assertRaises(RuntimeError):unwrap({'unexpected':True})
    def test_backend_down_is_explicit(self):
        class Offline:
            def call(self,*args):raise contract.Fault('backend_unavailable',retryable=True)
        RpcTests.setUpClass()
        server=RpcTests.server;server.BACKEND=Offline()
        result=server.rpc({'jsonrpc':'2.0','id':9,'method':'tools/call','params':{'name':'health','arguments':{}}})
        self.assertTrue(result['result']['isError'])
        self.assertEqual(result['result']['structuredContent']['error']['code'],'backend_unavailable')

if __name__=='__main__':unittest.main()
