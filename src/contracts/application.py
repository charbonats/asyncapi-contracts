from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .operation import BaseOperation
from .event import EventConsumer


@dataclass
class Contact:
    """Contact information for the exposed API."""

    name: str | None = None
    url: str | None = None
    email: str | None = None


def contact(
    name: str | None = None, url: str | None = None, email: str | None = None
) -> Contact:
    """Create a new contact."""
    return Contact(name, url, email)


@dataclass
class License:
    """License information for the exposed API."""

    name: str | None = None
    url: str | None = None


def license(name: str | None = None, url: str | None = None) -> License:
    """Create a new license."""
    return License(name, url)


@dataclass
class Tag:
    """A tag for application API documentation control."""

    name: str
    description: str | None = None
    external_docs: str | None = None


def tag(
    name: str, description: str | None = None, external_docs: str | None = None
) -> Tag:
    """Create a new tag."""
    return Tag(name, description, external_docs)


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
        components: list[
            type[BaseOperation[Any, Any, Any, Any, Any] | EventConsumer[Any, Any, Any]]
        ]
        | None = None,
        contact: Contact | None = None,
        license: License | None = None,
        tags: list[Tag] | None = None,
        title: str | None = None,
        external_docs: str | None = None,
    ) -> None:
        """Create a new typed service.

        Args:
            id: Application id
            name: Application name. Must be a valid NATS subject when used with nats-micro.
            version: Application version.
            description: Application description.
            metadata: Application metadata.
            components: List of operations that this application must implement.
            terms_of_service: A URL to the Terms of Service for the API. This MUST be in the form of an absolute URL.
            contact: The contact information for the exposed API.
            license: The license information for the exposed API.
            tags: A list of tags for application API documentation control. Tags can be used for logical grouping of applications.
            title: A human friendly title for the application.
            external_docs: Additional external documentation.
        """
        self.id = id
        self.name = name
        self.version = version
        self.description = description
        self.metadata = metadata or {}
        self.terms_of_service = terms_of_service
        self.components = components or []
        self.contact = contact
        self.license = license
        self.tags = tags or []
        self.external_docs = external_docs
        self.title = title


def validate_operations(
    app: Application,
    components: Iterable[
        BaseOperation[Any, Any, Any, Any, Any] | EventConsumer[Any, Any, Any]
    ],
) -> list[BaseOperation[Any, Any, Any, Any, Any]]:
    subjects: dict[str, str] = {}
    operations: list[BaseOperation[Any, Any, Any, Any, Any]] = []
    for endpoint in components:
        if isinstance(endpoint, EventConsumer):
            continue
        for candidate in app.components:
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


def validate_consumers(
    app: Application,
    components: Iterable[
        BaseOperation[Any, Any, Any, Any, Any] | EventConsumer[Any, Any, Any]
    ],
) -> list[EventConsumer[Any, Any, Any]]:
    subjects: dict[str, str] = {}
    consumers: list[EventConsumer[Any, Any, Any]] = []
    for consumer in components:
        if isinstance(consumer, BaseOperation):
            continue
        for candidate in app.components:
            if isinstance(consumer, candidate):
                break
        else:
            raise ValueError(f"Consumer {consumer} is not supported by the service")
        if consumer.event_spec.address.subject in subjects:
            existing_consumer = subjects[consumer.event_spec.address.subject]
            raise ValueError(
                f"Consumer {consumer} uses the same subject as consumer {existing_consumer}: {consumer.event_spec.address.subject}"
            )
        subjects[consumer.event_spec.address.subject] = consumer.event_spec.name
        consumers.append(consumer)
    return consumers
