"""Optional paid LLM access. Imports and offline commands never create a client."""
import logging
import os


def create_client():
    """Require cost opt-in; unlock locally; constrain endpoint, headers and retries."""
    if os.environ.get('PQC_ENABLE_LLM') != '1':
        raise RuntimeError('Paid model calls are disabled. Set PQC_ENABLE_LLM=1 only after reviewing the model, data sent, and budget; install the [llm] extra.')
    if any(name in os.environ for name in ('ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL', 'ANTHROPIC_CUSTOM_HEADERS')):
        raise RuntimeError('Custom Anthropic endpoints/auth tokens/headers are not supported by this credential flow; unset their environment variables.')
    if os.environ.get('ANTHROPIC_LOG'):
        raise RuntimeError('Unset ANTHROPIC_LOG; verbose provider logging is disabled for credential safety.')
    # Disable provider/transport loggers, including propagation to a debug root logger.
    # The caller's ordinary application logging remains unchanged.
    names = {'anthropic', 'httpx', 'httpcore'}
    names.update(name for name in logging.root.manager.loggerDict
                 if name.startswith(('anthropic.', 'httpx.', 'httpcore.')))
    for name in names:
        logger = logging.getLogger(name)
        logger.disabled = True
        logger.propagate = False
        logger.handlers = [logging.NullHandler()]
    try:
        import anthropic
        # Legacy standalone scripts put only REPO/agent on sys.path.
        # Add the verified package parent so all callers share one unlock cache.
        import sys
        from pathlib import Path
        parent = str(Path(__file__).resolve().parents[1])
        if parent not in sys.path:
            sys.path.insert(0, parent)
        from agent.claude_credentials import load_credentials
        from agent.claude_errors import SafeProviderError, safe_error
    except ImportError:
        raise RuntimeError('Optional LLM dependencies missing; install this project with [llm].') from None
    credentials = load_credentials()
    headers = {'anthropic-workspace-id': credentials.workspace_id} if credentials.workspace_id else {}
    # No environment proxy, ambient auth token, SDK retry, or endpoint redirection.
    # No credential is placed in subprocess args, environment, records or dashboards.
    try:
        client = anthropic.Anthropic(
            api_key=credentials.api_key, auth_token=None,
            base_url='https://api.anthropic.com', default_headers=headers,
            http_client=anthropic.DefaultHttpxClient(trust_env=False, follow_redirects=False),
            max_retries=0, timeout=120.0)
    except Exception as exc:
        raise SafeProviderError(safe_error(exc, 'credential_setup')) from None
    return SafeClient(client)


class SafeMessages:
    """Only the synchronous endpoints used here; no raw SDK exception escapes."""
    def __init__(self, messages):
        self._messages = messages

    def _call(self, method, kwargs):
        from agent.claude_errors import SafeProviderError, safe_error
        try:
            return getattr(self._messages, method)(**kwargs)
        except Exception as exc:
            raise SafeProviderError(safe_error(exc, 'provider_request')) from None

    def create(self, **kwargs):
        if kwargs.get('stream'):
            raise RuntimeError('Streaming is not supported by the guarded Claude client.')
        return self._call('create', kwargs)

    def count_tokens(self, **kwargs):
        return self._call('count_tokens', kwargs)


class SafeClient:
    def __init__(self, client):
        self._client = client
        self.messages = SafeMessages(client.messages)

    def close(self):
        self._client.close()
