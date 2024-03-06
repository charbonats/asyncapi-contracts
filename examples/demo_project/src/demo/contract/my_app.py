from __future__ import annotations

from demo.__about__ import __version__

from .my_endpoint import MyEndpoint

from contracts import Application
from contracts.application import Tag


app = Application(
    id="https://github.com/charbonats/asyncapi-contracts/examples/demo_project",
    name="typed-example",
    version=__version__,
    description="Test service",
    operations=[MyEndpoint],
    tags=[Tag("example")],
    external_docs="https://github.com/charbonats/asyncapi-contracts",
)
