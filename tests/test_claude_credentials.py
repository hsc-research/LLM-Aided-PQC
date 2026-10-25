"""Offline credential security fixtures: dummy secrets, no network or real keys."""
import contextlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
import warnings

from agent import claude_credentials as c
from agent import llm_client as l

KEY = 'dummy-only-api-key-never-valid'
WORKSPACE = 'wrkspc_fixture-only'
PASSWORD = 'long unique test passphrase only'


@unittest.skipUnless(importlib.util.find_spec('cryptography'), 'Install llm extra for vault tests')
class VaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.root)}, clear=True)
        self.env.start(); self.addCleanup(self.env.stop)
        c._CACHE = None
        self.addCleanup(setattr, c, '_CACHE', None)
        self.file = self.root / c.APP / c.FILENAME

    def setup_vault(self):
        with patch.object(c, 'hidden_input', side_effect=[KEY, WORKSPACE, PASSWORD, PASSWORD]):
            c.setup()

    def test_roundtrip_encrypted_permissions_and_cache(self):
        self.setup_vault()
        raw=self.file.read_bytes()
        for secret in (KEY, WORKSPACE, PASSWORD): self.assertNotIn(secret.encode(),raw)
        self.assertEqual(stat.S_IMODE(self.file.stat().st_mode),0o600)
        self.assertEqual(stat.S_IMODE(self.file.parent.stat().st_mode),0o700)
        with patch.object(c,'hidden_input',return_value=PASSWORD) as prompt:
            value=c.load_credentials(); self.assertEqual(c.load_credentials(),value)
        prompt.assert_called_once()
        self.assertEqual(value.api_key,KEY);self.assertEqual(value.workspace_id,WORKSPACE)
        self.assertNotIn(KEY,repr(value));self.assertNotIn(WORKSPACE,repr(value))
        self.assertNotIn('ANTHROPIC_API_KEY',os.environ)

    def test_cache_cannot_silently_unlock_a_forked_process(self):
        self.setup_vault()
        with patch.object(c,'hidden_input',return_value=PASSWORD):c.load_credentials()
        child_pid=os.getpid()+1
        with patch.object(c.os,'getpid',return_value=child_pid),patch.object(c,'hidden_input',return_value=PASSWORD) as prompt:
            self.assertEqual(c.load_credentials().api_key,KEY)
            prompt.assert_called_once()

    def test_weak_passphrase_never_installs_vault(self):
        with patch.object(c,'hidden_input',side_effect=[KEY,WORKSPACE,'short']):
            with self.assertRaises(c.CredentialError):c.setup()
        self.assertFalse(self.file.exists())

    def test_wrong_file_owner_is_rejected_after_open(self):
        self.setup_vault()
        with c.private_directory() as fd:
            original=self.file.stat()
            fake=NS(st_mode=original.st_mode,st_uid=os.getuid()+1,st_nlink=1,st_size=original.st_size)
            with patch.object(c.os,'fstat',return_value=fake):
                with self.assertRaises(c.CredentialError):c._read(fd)

    def test_wrong_password_and_tampered_ciphertext_fail(self):
        self.setup_vault()
        with patch.object(c,'hidden_input',return_value='incorrect password'):
            with self.assertRaisesRegex(c.CredentialError,'Cannot unlock'):c.load_credentials()
        self.assertIsNone(c._CACHE)
        value=json.loads(self.file.read_text());value['token']=value['token'][:-8]+'AAAAAAAA'
        self.file.write_text(json.dumps(value))
        with patch.object(c,'hidden_input',return_value=PASSWORD):
            with self.assertRaisesRegex(c.CredentialError,'Cannot unlock'):c.load_credentials()

    def test_reject_malformed_and_unbounded_kdf(self):
        for data in (b'[]',b'{',b'null',b'{"version":1,"kdf":"scrypt-n999999999999"}',b'{"version":2}'):
            with self.subTest(data=data),patch.object(c,'_fernet',side_effect=AssertionError('KDF must not run')):
                with self.assertRaises(c.CredentialError):c._decrypt(data,PASSWORD)

    def test_setup_no_overwrite_and_failed_replace_preserves_bytes(self):
        self.setup_vault();old=self.file.read_bytes()
        with patch.object(c,'hidden_input',side_effect=AssertionError('must not prompt')):
            with self.assertRaisesRegex(c.CredentialError,'already exists'):c.setup()
        with patch.object(c,'hidden_input',side_effect=[PASSWORD,KEY,WORKSPACE,PASSWORD,'mismatch']):
            with self.assertRaisesRegex(c.CredentialError,'do not match'):c.setup(replace=True)
        self.assertEqual(self.file.read_bytes(),old)

    def test_replace_success_and_atomic_failure(self):
        self.setup_vault();old=self.file.read_bytes()
        prompts=[PASSWORD,KEY+'-new',WORKSPACE,PASSWORD,PASSWORD]
        with patch.object(c,'hidden_input',side_effect=prompts),patch.object(c.os,'replace',side_effect=OSError('fixture')):
            with self.assertRaises(c.CredentialError):c.setup(replace=True)
        self.assertEqual(self.file.read_bytes(),old)
        self.assertEqual(list(self.file.parent.iterdir()),[self.file])
        with patch.object(c,'hidden_input',side_effect=prompts):c.setup(replace=True)
        with patch.object(c,'hidden_input',return_value=PASSWORD):self.assertEqual(c.load_credentials().api_key,KEY+'-new')

    def test_reject_insecure_file_and_directory_permissions(self):
        self.setup_vault()
        for path,mode in ((self.file,0o644),(self.file.parent,0o755)):
            with self.subTest(path=path):
                original=stat.S_IMODE(path.stat().st_mode);path.chmod(mode)
                with self.assertRaises(c.CredentialError):
                    with c.private_directory() as fd:c._read(fd)
                path.chmod(original)

    def test_reject_symlink_parent_file_and_hardlink(self):
        self.setup_vault();original=self.file.read_bytes()
        other=self.root/'other';self.file.rename(other);self.file.symlink_to(other)
        with self.assertRaises(c.CredentialError):
            with c.private_directory() as fd:c._read(fd)
        self.file.unlink();os.link(other,self.file)
        with self.assertRaises(c.CredentialError):
            with c.private_directory() as fd:c._read(fd)
        self.file.unlink();other.unlink();self.file.write_bytes(original);self.file.chmod(0o600)
        new=self.root/'private';self.file.parent.rename(new);self.file.parent.symlink_to(new,target_is_directory=True)
        with self.assertRaises(c.CredentialError):
            with c.private_directory():pass

    def test_reject_unsafe_parent_and_repository_path(self):
        self.root.chmod(0o777)
        with self.assertRaises(c.CredentialError):
            with c.private_directory(create=True):pass
        self.root.chmod(0o700)
        (self.root/'.git').mkdir();(self.root/'.git/HEAD').write_text('ref: refs/heads/fixture')
        with self.assertRaisesRegex(c.CredentialError,'Git checkout'):c.vault_directory()
        with patch.dict(os.environ,{'XDG_CONFIG_HOME':'relative'}):
            with self.assertRaises(c.CredentialError):c.vault_directory()

    def test_oversize_and_fifo_fail_without_blocking(self):
        with c.private_directory(create=True):pass
        self.file.write_bytes(b'x'*(c.MAX_BYTES+1));self.file.chmod(0o600)
        with self.assertRaises(c.CredentialError):
            with c.private_directory() as fd:c._read(fd)
        self.file.unlink();os.mkfifo(self.file,0o600)
        with self.assertRaises(c.CredentialError):
            with c.private_directory() as fd:c._read(fd)

    def test_no_terminal_or_echo_fallback(self):
        with patch('builtins.open',side_effect=OSError('no tty')),patch.object(c.getpass,'getpass') as prompt:
            with self.assertRaises(c.CredentialError):c.hidden_input('secret: ')
            prompt.assert_not_called()
        tty=Mock();tty.__enter__=Mock(return_value=tty);tty.__exit__=Mock(return_value=False);tty.isatty.return_value=True
        def fallback(*args,**kw):warnings.warn('echo',c.getpass.GetPassWarning)
        with patch('builtins.open',return_value=tty),patch.object(c.getpass,'getpass',side_effect=fallback):
            with self.assertRaises(c.CredentialError):c.hidden_input('secret: ')

    def test_env_is_explicit_and_validated_without_persistence(self):
        with patch.dict(os.environ,{'ANTHROPIC_API_KEY':KEY}):
            with self.assertRaisesRegex(c.CredentialError,'Unset legacy'):c.load_credentials()
            with patch.dict(os.environ,{'PQC_CLAUDE_AUTH':'env','ANTHROPIC_WORKSPACE_ID':WORKSPACE}):
                self.assertEqual(c.load_credentials(),c.Credentials(KEY,WORKSPACE))
        self.assertFalse(self.file.exists())
        with self.assertRaises(c.CredentialError):c.validate(KEY, 'workspace\r\nInjected: header')
        with self.assertRaises(c.CredentialError):c.validate('key\nSECRET',WORKSPACE)

    def test_status_never_unlocks_or_calls_api(self):
        self.setup_vault()
        with patch.object(c,'hidden_input',side_effect=AssertionError('no prompt')),contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(c.main(['status']),0)
        self.assertIn('not been checked',output.getvalue())
        self.assertNotIn(KEY,output.getvalue())


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'PQC_ENABLE_LLM':'1'},clear=True)
        self.env.start();self.addCleanup(self.env.stop)
        self.sdk=NS(Anthropic=Mock(),DefaultHttpxClient=Mock())
        self.patches=[patch.dict(sys.modules,{'anthropic':self.sdk}),patch.object(c,'load_credentials',return_value=c.Credentials(KEY,WORKSPACE))]
        for item in self.patches:item.start();self.addCleanup(item.stop)

    def test_common_client_workspace_and_safety_options(self):
        l.create_client()
        kwargs=self.sdk.Anthropic.call_args.kwargs
        self.assertEqual(kwargs['api_key'],KEY)
        self.assertEqual(kwargs['default_headers'],{'anthropic-workspace-id':WORKSPACE})
        self.assertEqual(kwargs['max_retries'],0);self.assertEqual(kwargs['timeout'],120)
        self.assertEqual(kwargs['base_url'],'https://api.anthropic.com')
        self.assertIsNone(kwargs['auth_token'])
        self.sdk.DefaultHttpxClient.assert_called_once_with(trust_env=False,follow_redirects=False)

    def test_no_workspace_header_for_legacy_scoped_key(self):
        with patch.object(c,'load_credentials',return_value=c.Credentials(KEY)):
            l.create_client()
        self.assertEqual(self.sdk.Anthropic.call_args.kwargs['default_headers'],{})

    def test_optin_and_conflicting_env_before_credential_read(self):
        for name,value in (('PQC_ENABLE_LLM','0'),('ANTHROPIC_BASE_URL','https://untrusted.invalid'),('ANTHROPIC_AUTH_TOKEN','dummy'),('ANTHROPIC_AUTH_TOKEN',''),('ANTHROPIC_CUSTOM_HEADERS','X-Api-Key: dummy'),('ANTHROPIC_CUSTOM_HEADERS',''),('ANTHROPIC_LOG','debug')):
            with self.subTest(name=name),patch.dict(os.environ,{name:value}),patch.object(c,'load_credentials') as load:
                with self.assertRaises(RuntimeError):l.create_client()
                load.assert_not_called()
        self.sdk.Anthropic.assert_not_called()

    def test_legacy_import_uses_same_credentials_module(self):
        spec=importlib.util.spec_from_file_location('llm_client',Path(l.__file__))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.create_client()
        self.assertEqual(self.sdk.Anthropic.call_args.kwargs['api_key'],KEY)

    def test_transport_children_cannot_propagate_to_debug_root(self):
        output=io.StringIO();handler=logging.StreamHandler(output);root=logging.getLogger();root.addHandler(handler)
        self.addCleanup(root.removeHandler,handler)
        logger=logging.getLogger('anthropic.fixture_old');logger.setLevel(logging.DEBUG)
        l.create_client()
        logger.error(KEY)
        logging.getLogger('anthropic.fixture_created_later').error(KEY)
        self.assertNotIn(KEY,output.getvalue())




class ProviderErrorTests(unittest.TestCase):
    def test_both_endpoints_redact_raw_error(self):
        class BadRequestError(Exception):
            status_code=400
            body={'error':{'message':KEY+' not scoped to a workspace; specify anthropic-workspace-id'}}
        source=NS(create=Mock(side_effect=BadRequestError(KEY)),count_tokens=Mock(side_effect=BadRequestError(KEY)))
        messages=l.SafeMessages(source)
        from agent.claude_errors import SafeProviderError, safe_error
        for endpoint in (messages.count_tokens,messages.create):
            with self.assertRaises(SafeProviderError) as result:endpoint(model='fixture')
            self.assertNotIn(KEY,str(result.exception))
            self.assertEqual(safe_error(result.exception,'token_count')['error_category'],'workspace_required')
            self.assertEqual(safe_error(result.exception,'token_count')['provider_http_status'],400)
        source.create.assert_called_once();source.count_tokens.assert_called_once()

    @unittest.skipUnless(importlib.util.find_spec('cryptography'), 'Install llm extra')
    def test_deep_json_normalized(self):
        with self.assertRaises(c.CredentialError):c._decrypt(b'['*2000+b']'*2000,PASSWORD)


@unittest.skipUnless(os.name=='posix' and importlib.util.find_spec('cryptography'), 'POSIX and llm extra required')
class TerminalIntegrationTests(unittest.TestCase):
    def test_actual_pty_setup_and_unlock_without_secret_echo(self):
        import pty
        import select
        import time
        with tempfile.TemporaryDirectory() as td:
            pid,fd=pty.fork()
            if pid==0:
                try:
                    os.environ.clear();os.environ['XDG_CONFIG_HOME']=td;c._CACHE=None
                    code=c.main(['setup'])
                    if code:os._exit(code)
                    value=c.load_credentials()
                    print('ROUNDTRIP_OK' if value==c.Credentials(KEY,WORKSPACE) else 'MISMATCH',flush=True)
                    os._exit(0)
                except BaseException:os._exit(99)
            output=b''
            steps=[(b'Claude API key',KEY),(b'Workspace ID',WORKSPACE),(b'New vault passphrase',PASSWORD),
                   (b'Confirm vault passphrase',PASSWORD),(b'Unlock Claude vault',PASSWORD)]
            deadline=time.monotonic()+15
            try:
                while time.monotonic()<deadline:
                    if select.select([fd],[],[],.2)[0]:
                        try:chunk=os.read(fd,4096)
                        except OSError:break
                        if not chunk:break
                        output+=chunk
                        if steps and steps[0][0] in output:
                            _,answer=steps.pop(0);os.write(fd,answer.encode()+b'\n')
                    done,status=os.waitpid(pid,os.WNOHANG)
                    if done:
                        pid=None
                        self.assertEqual(os.waitstatus_to_exitcode(status),0,output.decode(errors='replace'))
                        break
                self.assertFalse(steps,output.decode(errors='replace'))
                self.assertIn(b'ROUNDTRIP_OK',output)
                for secret in (KEY,WORKSPACE,PASSWORD):self.assertNotIn(secret.encode(),output)
            finally:
                os.close(fd)
                if pid:
                    done,status=os.waitpid(pid,os.WNOHANG)
                    if not done:
                        import signal
                        os.kill(pid,signal.SIGKILL);os.waitpid(pid,0)

@unittest.skipUnless(importlib.util.find_spec('anthropic'),'Install llm extra for real SDK/mock transport checks')
class SDKTransportTests(unittest.TestCase):
    def make_client(self, handler):
        import anthropic
        import httpx
        self.transport=httpx.MockTransport(handler)
        transport_client=httpx.Client(transport=self.transport,trust_env=False,follow_redirects=False)
        self.addCleanup(transport_client.close)
        with patch.dict(os.environ,{'PQC_ENABLE_LLM':'1'},clear=True),patch.object(c,'load_credentials',return_value=c.Credentials(KEY,WORKSPACE)),patch.object(anthropic,'DefaultHttpxClient',return_value=transport_client):
            return l.create_client()

    def test_real_sdk_sends_workspace_header_on_both_requests(self):
        import httpx
        seen=[]
        def handle(request):
            seen.append(request)
            if request.url.path.endswith('/count_tokens'):
                return httpx.Response(200,json={'input_tokens':10})
            return httpx.Response(200,json={'id':'msg_fixture','type':'message','role':'assistant','model':'fixture','content':[{'type':'text','text':'{"status":"STOP"}'}],
                                           'stop_reason':'end_turn','stop_sequence':None,'usage':{'input_tokens':10,'output_tokens':10}})
        client=self.make_client(handle)
        params={'model':'fixture','messages':[{'role':'user','content':'fixture'}]}
        self.assertEqual(client.messages.count_tokens(**params).input_tokens,10)
        self.assertEqual(client.messages.create(**params,max_tokens=10).stop_reason,'end_turn')
        self.assertEqual(len(seen),2)
        for request in seen:
            self.assertEqual(request.url.host,'api.anthropic.com')
            self.assertEqual(request.headers['anthropic-workspace-id'],WORKSPACE)
            self.assertEqual(request.headers['x-api-key'],KEY)
            self.assertNotIn('authorization',request.headers)

    def test_real_sdk_error_has_one_attempt_no_retry_and_no_raw_body(self):
        import httpx
        seen=[]
        def handle(request):
            seen.append(request)
            return httpx.Response(429,json={'type':'error','error':{'type':'rate_limit_error','message':KEY}},headers={'retry-after':'0'})
        client=self.make_client(handle)
        from agent.claude_errors import SafeProviderError
        with self.assertRaises(SafeProviderError) as result:
            client.messages.create(model='fixture',max_tokens=10,messages=[{'role':'user','content':'fixture'}])
        self.assertEqual(len(seen),1)
        self.assertEqual(result.exception.category,'rate_limit')
        self.assertNotIn(KEY,str(result.exception))

    def test_real_sdk_does_not_follow_redirect(self):
        import httpx
        seen=[]
        def handle(request):
            seen.append(request)
            return httpx.Response(307,headers={'location':'https://untrusted.invalid/messages'})
        client=self.make_client(handle)
        from agent.claude_errors import SafeProviderError
        with self.assertRaises(SafeProviderError):
            client.messages.count_tokens(model='fixture',messages=[{'role':'user','content':'fixture'}])
        self.assertEqual(len(seen),1)
        self.assertEqual(seen[0].url.host,'api.anthropic.com')





class ProcessBoundaryTests(unittest.TestCase):
    def test_legacy_standalone_import_without_checkout_on_path(self):
        import subprocess
        repo=Path(__file__).resolve().parents[1]
        program="""import os, sys
from types import SimpleNamespace as NS
sys.path.insert(0, sys.argv[1])
import llm_client
sys.modules['anthropic']=NS(Anthropic=lambda **kw:NS(messages=NS()), DefaultHttpxClient=lambda **kw:object())
os.environ['PQC_ENABLE_LLM']='1'
os.environ['PQC_CLAUDE_AUTH']='env'
os.environ['ANTHROPIC_API_KEY']='dummy-key-for-standalone-fixture'
llm_client.create_client()
print('CLIENT_CREATED_OFFLINE')
"""
        with tempfile.TemporaryDirectory() as td:
            result=subprocess.run([sys.executable,'-I','-c',program,str(repo/'agent')],cwd=td,env={},text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'CLIENT_CREATED_OFFLINE')

    def test_detached_input_fails_promptly_without_stdin_fallback(self):
        import subprocess
        repo=Path(__file__).resolve().parents[1]
        program="""import sys
sys.path.insert(0, sys.argv[1])
from agent.claude_credentials import hidden_input, CredentialError
try:hidden_input('Hidden: ')
except CredentialError as error:
    print(str(error))
    raise SystemExit(2)
raise SystemExit(99)
"""
        result=subprocess.run([sys.executable,'-I','-c',program,str(repo)],input=KEY,text=True,capture_output=True,start_new_session=True,timeout=10)
        self.assertEqual(result.returncode,2)
        self.assertIn('terminal',result.stdout)
        self.assertNotIn(KEY,result.stdout+result.stderr)


if __name__ == '__main__':unittest.main()
