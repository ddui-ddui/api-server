from contextvars import ContextVar
from typing import Optional

request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
client_ip: ContextVar[Optional[str]] = ContextVar('client_ip', default=None)
user_agent: ContextVar[Optional[str]] = ContextVar('user_agent', default=None)