from .__about__ import __version__

# The base class for applications
from .application import Application, tag, contact, license

# The class used to annotate messages received by operations
from .message import Message

# The class used to annotate messages received by consumers
from .event import Event

# The decorator and helper classes for operations
from .operation import format_error, operation

# The decorator and helper classes for events
from .event import event, consumer

# The class used to define the schema of the messages
from .schema import schema

# The function used to generate specs
from .specification import build_spec


__all__ = [
    "__version__",
    # App related
    "Application",
    "tag",
    "contact",
    "license",
    # Common
    "schema",
    # Operation related
    "operation",
    "format_error",
    "Message",
    # Consumers related
    "Event",
    "event",
    "consumer",
    # Async API related
    "build_spec",
]
