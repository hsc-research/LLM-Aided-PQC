"""Bounded provider diagnostics. Raw SDK exception text is never written to logs/records by this wrapper."""


class SafeProviderError(RuntimeError):
    def __init__(self, fields):
        self.status_code = fields['provider_http_status']
        self.category = fields['error_category']
        self.provider_error_type = fields['error_type']
        super().__init__('Claude request failed: ' + self.category + '; no automatic retry.')


def safe_error(exc, stage):
    """Allowlisted diagnostics only; never persist SDK text, headers or body."""
    known={'BadRequestError','AuthenticationError','PermissionDeniedError','NotFoundError',
           'RateLimitError','InternalServerError','APIConnectionError','APITimeoutError',
           'TimeoutError','ValueError','RuntimeError','CredentialError','ImportError','KeyboardInterrupt','ResponseFormatError','JSONDecodeError','EditError'}
    name=type(exc).__name__
    status=getattr(exc,'status_code',None)
    status=status if type(status) is int and 100<=status<=599 else None
    category={400:'invalid_request',401:'authentication',403:'permission',404:'not_found',
              429:'rate_limit'}.get(status,'provider_unavailable' if status and status>=500 else 'unknown')
    if name in {'ResponseFormatError','JSONDecodeError'}:category='response_format'
    elif name=='EditError':category='proposal_validation'
    elif name=='KeyboardInterrupt':category='interrupted'
    elif name=='CredentialError':category='local_credentials'
    elif name in {'APIConnectionError','APITimeoutError','TimeoutError'}:category='connection_or_timeout'
    elif name in {'ValueError','RuntimeError','ImportError'} and status is None:category='local_configuration_or_validation'
    # Read only the bounded error message in memory to identify a workspace failure.
    body=getattr(exc,'body',None)
    if status==400 and isinstance(body,dict):
        error=body.get('error',body)
        message=error.get('message') if isinstance(error,dict) else None
        if isinstance(message,str) and len(message)<=8192 and ('anthropic-workspace-id' in message.lower() or 'not scoped to a workspace' in message.lower()):
            category='workspace_required'
    if isinstance(exc,SafeProviderError):
        category=exc.category if exc.category in {'response_format','proposal_validation','interrupted','workspace_required','authentication','permission','not_found','rate_limit','provider_unavailable','local_credentials','connection_or_timeout','local_configuration_or_validation','invalid_request','unknown'} else 'unknown'
        name=exc.provider_error_type
    return {'error_type':name if name in known else 'OtherError',
            'provider_http_status':status,'error_category':category,'failure_stage':stage}
