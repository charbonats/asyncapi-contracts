# asyncapi-contracts

## Description

`asyncapi-contracst` is a framework which lets you design, serve and consume your APIs using AsyncAPI specification in a Pythonic way.

You must first define operations using decorated classes, and then define an application that must implement these operations.

Once an application is defined, and even before operations are implemented, you can generate AsyncAPI specification from it. You can also start writing typed-safe client code to consume the yet to be written operations.

It also integrates with [`nats-micro`](https://charbonats.github.io/nats-micro) to easily deploy an application as a NATS Micro service.


## Motivation

I always wanted to try design first approach for my APIs.

Design first approach is a way to design your APIs before you start implementing them. This approach is very useful when you are working in a team and you want to make sure that everyone is on the same page.

This [blog post from Swagger.io](https://swagger.io/blog/code-first-vs-design-first-api/) explains the difference between design first and code first approach.

However, in order to use design first approach, you need to have a way to describe your API. The most successfull way to describe RESTful APIs is [OpenAPI](https://www.openapis.org/). Its counterpart for event driven application is [AsyncAPI](https://www.asyncapi.com/).

Turns out it's not that easy to find a good tool to design your APIs using AsyncAPI. An online editor is available at [https://studio.asyncapi.com/](https://studio.asyncapi.com/), but it's quite slow on a slow internet connection / old computer. Also, it's not easy navigating through all the sections of the AsyncAPI specification.

Due to these reasons, I decided to create a simple tool to design my APIs using AsyncAPI, with a big difference being that API specification is not written directly in AsyncAPI, but using Python classes and objects.

## Example

Checkout the [example project](examples/demo_project/README.md) to see how to use `asyncapi-contracts`.

## Basic Usage

### Defining operations

```python
from dataclasses import dataclass

from contracts import operation


@dataclass
class ProjectParameters:
    project_id: str


@dataclass
class CreateProjectUserRequest:
    username: str
    email: str


@dataclass
class CreateProjectUserResponse:
    user_id: str


@operation(
    address="project.{project_id}.user.create",
    parameters=ProjectParameters,
    request_schema=CreateProjectUserRequest,
    response_schema=CreateProjectUserResponse,
    error_schema=str,
)
class CreateProjectUser:
    """Operation to create a new project user."""
```

The `operation` decorator is used to define an operation:

- the `address` parameter is used to define the address of the operation. In AsyncAPI, an operation is not associated to an address, but to [a channel](https://www.asyncapi.com/docs/concepts/channel). However, `asyncapi-contracts` will take care of identifying the channels used by the application and [adding them in the documentation](https://www.asyncapi.com/docs/concepts/asyncapi-document/adding-channels), based on the operations specifications.
- the `parameters` parameter is used to define the parameters found in the operation's address. Just like addresses, in AsyncAPI, parameters are defined for [channels](https://www.asyncapi.com/docs/concepts/channel) but `asyncapi-contracts` will take care of identifying the parameters used by the application and [adding them in the documentation](https://www.asyncapi.com/docs/concepts/asyncapi-document/dynamic-channel-address), based on the operations specifications.
- the `request_schema` parameter is used to define the request schema of the operation. In AsyncAPI, this corresponds to a [message](https://www.asyncapi.com/docs/concepts/message) defined in a [channel](https://www.asyncapi.com/docs/concepts/channel).
- the `response_schema` parameter is used to define the response schema of the operation. In AsyncAPI, this corresponds to a [message](https://www.asyncapi.com/docs/concepts/message) defined in a [reply channel](https://www.asyncapi.com/docs/concepts/channel). `asyncapi-contracts` will take care of identifying the reply channels used by the application and [adding them in the documentation](https://www.asyncapi.com/docs/concepts/asyncapi-document/reply-info), based on the operations specifications.
- the `error_schema` parameter is used to define the error schema of the operation. In AsyncAPI, this corresponds to a [message](https://www.asyncapi.com/docs/concepts/message) defined in a [reply channel](https://www.asyncapi.com/docs/concepts/channel). `asyncapi-contracts` will take care of identifying the reply channels used by the application and [adding them in the documentation](https://www.asyncapi.com/docs/concepts/asyncapi-document/reply-info), based on the operations specifications.

Other parameters are available but are not documented yet.

### Defining an application

```python
from contracts import Application

from .operations import CreateUser

app = Application(
    id="http://example.com/user-service",
    version="0.0.1",
    name="user-service",
    operations=[
        CreateUser,
    ],
)
```

The `Application` class is used to define an application:

- the `id` parameter is used to define the [id of the application](https://www.asyncapi.com/docs/reference/specification/v3.0.0#A2SIdString). It must conform to the URI format, according to [RFC3986](https://datatracker.ietf.org/doc/html/rfc3986).

- the `version` parameter is used to define the [version found in the application info](https://www.asyncapi.com/docs/reference/specification/v3.0.0#infoObject).

- the `name` parameter is used to define the [title found in the application info](https://www.asyncapi.com/docs/reference/specification/v3.0.0#infoObject).

- the `operations` parameter is used to define [the operations](https://www.asyncapi.com/docs/reference/specification/v3.0.0#operationObject) of the application.

### Generate AsyncAPI specification

```python
from contracts.specification import build_spec


spec = build_spec(app)
print(spec.export_json())
```

The `build_spec` function is used to generate an AsyncAPI specification from an application.

The output of the `export_json` method is a JSON string representing the AsyncAPI specification.

You can checkout the output of the example project: [examples/demo_project/asyncapi.json](examples/demo_project/asyncapi.json)

### Server side: Implement the operations

```python
from contracts import Message
from .operations import CreateUser, CreateUserRequest, CreatedUser


class CreateUserImpl(CreateUser):
    """Implements the CreateUser operation."""

    async def handle(self, message: Message[CreateUser]) -> None:
        """Handle an incoming request message."""
        # Create a user
        user_id = "123"
        await message.respond(CreatedUser(user_id=user_id))
```

The `handle` method must be an async method, and it must accept a single argument of type `Message`.

The `handle` method must not return a value. Instead, use the `respond` method to send a response back to the sender.

This is because the `contracts` framework is designed to work with different backends, and the `respond` method is a generic way to send a response back to the sender, regardless of the backend.

Also, returning a value does not allow to distinguish between a successful response and an error response. By using the `respond` method, it is implied that the response is a successful response. If you want to send an error response, you can use the `respond_error` method.

### Server side: Start the application using a backend

```python
import nats_contrib.micro as micro
from contracts.backends.micro import start_micro_server

from .app import app
from .implementation import CreateUserImpl

async def setup(ctx: micro.Context) -> None:
    """An example setup function to start a micro service."""

    # Start the app as a NATS Micro service
    await start_micro_server(
        ctx,
        # Provide the application
        app,
        # Provide the operation implementations
        [
            CreateUserImpl(),
        ],
    )
```
> Note: At the time of writing, an application MAY be started without implementations for all operations. However, this will change in the future, and an error will be raised if an operation is not implemented in order to match with AsyncAPI spec.
> See https://www.asyncapi.com/docs/reference/specification/v3.0.0#operationsObject

## Client side: Consume the operations

```python
from contracts import Message
from contracts.interfaces import Client

class DoCreateUser:
    """A class that can call the create_user operation remotely."""
    def __init__(self, client: Client) -> None:
        self.client = client

    async def create_user(self, user_id: str) -> str:
        """Create a user."""
        # Send the request message
        response = await self.client.send(
            # Create a request message
            CreateUser.request(
                # First argument is the request data
                CreateUserRequest(user_id=user_id),
                # Second argument is the message parameters
                project_id=1000,
            )
        )
        # This will decode the response data into a CreateProjectUserResponse object
        user_created = response.data()
        return user_created.user_id
```

At the time of writing, a single client implementation is provided, which is the `MicroClient` class. This class is used to send and receive messages using NATS thankts to [`nats-micro`](https://github.com/charbonats/nats-micro) package. 
