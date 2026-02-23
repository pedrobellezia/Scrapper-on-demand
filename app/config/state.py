from contextvars import ContextVar
from os import urandom

worker_id: ContextVar[str] = ContextVar("worker_id")
