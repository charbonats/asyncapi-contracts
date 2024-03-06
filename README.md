# asyncapi-contracts

## Description

`asyncapi-contracst` is a framework which lets you design your APIs using AsyncAPI specification in a Pythonic way.

You must first define operations using decorated classes, and then define an application that must implement these operations.

Once an application is defined, you can generate AsyncAPI specification from it.

It also integrates with [`nats-micro`](https://charbonats.github.io/nats-micro) to easily deploy an application as a NATS Micro service.

## Example

Checkout the [example project](examples/demo_project/README.md) to see how to use `asyncapi-contracts`.

## Basic Usage

### Defining operations

```python
from dataclasses import dataclass

from contracts import operation


@dataclass
class CreateUserRequest:
    username: str
    email: str


@dataclass
class CreatedUser:
    user_id: str


@operation(
    address="user.create",
    request_schema=CreateUserRequest,
    response_schema=CreatedUser,
)
class CreateUser:
    """Operation to create a new user."""
```

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

### Implement the operations

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

### Start the application using a backend

```python
import nats_contrib.micro as micro
from contracts.backends.micro.micro import start_micro_server

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

## Motivation

I always wanted to try design first approach for my APIs.

Design first approach is a way to design your APIs before you start implementing them. This approach is very useful when you are working in a team and you want to make sure that everyone is on the same page.

This [blog post from Swagger.io](https://swagger.io/blog/code-first-vs-design-first-api/) explains the difference between design first and code first approach.

However, in order to use design first approach, you need to have a way to describe your API. The most successfull way to describe RESTful APIs is [OpenAPI](https://www.openapis.org/). Its counterpart for event driven application is [AsyncAPI](https://www.asyncapi.com/).

Turns out it's not that easy to find a good tool to design your APIs using AsyncAPI. An online editor is available at [https://studio.asyncapi.com/](https://studio.asyncapi.com/), but it's quite slow on a slow internet connection / old computer. Also, it's not easy navigating through all the sections of the AsyncAPI specification.

Due to these reasons, I decided to create a simple tool to design my APIs using AsyncAPI, with a big difference being that API specification is not written directly in AsyncAPI, but using Python classes and objects.
