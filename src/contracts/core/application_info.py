from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Contact:
    """Contact information for the exposed API."""

    name: str | None = None
    url: str | None = None
    email: str | None = None


@dataclass
class License:
    """License information for the exposed API."""

    name: str | None = None
    url: str | None = None


@dataclass
class Tag:
    """A tag for application API documentation control."""

    name: str
    description: str | None = None
    external_docs: str | None = None
