"""Routers module."""

from . import health
from . import moderator_suppliers
from . import keywords
from . import blacklist
from . import parsing
from . import parsing_runs
from . import domains_queue
from . import attachments
from . import checko
from . import comet

__all__ = [
    "health",
    "moderator_suppliers",
    "keywords",
    "blacklist",
    "parsing",
    "parsing_runs",
    "domains_queue",
    "attachments",
    "checko",
    "comet",
]
