class OAIError(Exception):
    """Base exception for OAI-PMH client errors."""


class OAITransportError(OAIError):
    """Network, timeout, or HTTP transport failure."""


class OAIProtocolError(OAIError):
    """An OAI-PMH error returned by the repository."""


class OAIParseError(OAIError):
    """Malformed or unexpected OAI-PMH XML response."""


class OAIRequestError(OAIError):
    """Invalid verb or request parameters."""
