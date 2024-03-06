from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .operation import Operation


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


class Application:
    """Typed service definition."""

    def __init__(
        self,
        id: str,
        name: str,
        version: str,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
        terms_of_service: str | None = None,
        operations: list[type[Operation[Any, Any, Any, Any, Any]]] | None = None,
        contact: Contact | None = None,
        license: License | None = None,
        tags: list[Tag] | None = None,
        external_docs: str | None = None,
    ) -> None:
        """Create a new typed service.

        Args:
            id: Application id
            name: Application name.
            version: Application version.
            description: Application description.
            metadata: Application metadata.
            operations: List of operations that this application must implement.
            terms_of_service: A URL to the Terms of Service for the API. This MUST be in the form of an absolute URL.
            contact: The contact information for the exposed API.
            license: The license information for the exposed API.
            tags: A list of tags for application API documentation control. Tags can be used for logical grouping of applications.
            external_docs: Additional external documentation.
        """
        self.id = id
        self.name = name
        self.version = version
        self.description = description
        self.metadata = metadata or {}
        self.terms_of_service = terms_of_service
        self.endpoints = operations or []
        self.contact = contact
        self.license = license
        self.tags = tags or []
        self.external_docs = external_docs


def validate(
    app: Application,
    endpoints: Iterable[Operation[Any, Any, Any, Any, Any]],
) -> list[Operation[Any, Any, Any, Any, Any]]:
    subjects: dict[str, str] = {}
    operations: list[Operation[Any, Any, Any, Any, Any]] = []
    for endpoint in endpoints:
        for candidate in app.endpoints:
            if isinstance(endpoint, candidate):
                break
        else:
            raise ValueError(f"Endpoint {endpoint} is not supported by the service")
        if endpoint.spec.address.subject in subjects:
            existing_endpoint = subjects[endpoint.spec.address.subject]
            raise ValueError(
                f"Endpoint {endpoint} uses the same subject as endpoint {existing_endpoint}: {endpoint.spec.address.subject}"
            )
        subjects[endpoint.spec.address.subject] = endpoint.spec.name
        operations.append(endpoint)
    return operations
