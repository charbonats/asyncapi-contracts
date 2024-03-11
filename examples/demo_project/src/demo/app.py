from __future__ import annotations

from demo.__about__ import __version__

from contracts import Application, contact, tag

from .components.my_operation import MyOperation

app = Application(
    id="https://github.com/charbonats/asyncapi-contracts/examples/demo_project",
    name="demo-project",
    title="Demo Project",
    version=__version__,
    description="Test service",
    tags=[
        tag("example", "An example tag", "https://example.com"),
    ],
    contact=contact(
        name="John Doe",
        email="john-doe@example.com",
    ),
    external_docs="https://github.com/charbonats/asyncapi-contracts",
    components=[
        MyOperation,
    ],
)
