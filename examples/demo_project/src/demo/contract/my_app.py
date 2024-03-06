from __future__ import annotations

from demo.__about__ import __version__

from .my_endpoint import MyEndpoint

from contracts import Application


app = Application(
    id="https://github.com/charbonats/examples/typed",
    name="typed-example",
    version=__version__,
    description="Test service",
    operations=[MyEndpoint],
)
