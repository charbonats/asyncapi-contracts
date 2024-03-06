# asyncapi-contracts

## Description

`asyncapi-contracst` is a framework which lets you design your APIs using AsyncAPI specification in a Pythonic way.

You must first define operations using decorated classes, and then define an application that must implement these operations.

Once an application is defined, you can generate AsyncAPI specification from it.

It also integrates with [`nats-micro`](https://charbonats.github.io/nats-micro) to easily deploy an application as a NATS Micro service.

## Example

Checkout the [example project](examples/demo_project/README.md) to see how to use `asyncapi-contracts`.

## Motivation

I always wanted to try design first approach for my APIs.

Design first approach is a way to design your APIs before you start implementing them. This approach is very useful when you are working in a team and you want to make sure that everyone is on the same page.

This [blog post from Swagger.io](https://swagger.io/blog/code-first-vs-design-first-api/) explains the difference between design first and code first approach.

However, in order to use design first approach, you need to have a way to describe your API. The most successfull way to describe RESTful APIs is [OpenAPI](https://www.openapis.org/). Its counterpart for event driven application is [AsyncAPI](https://www.asyncapi.com/).

Turns out it's not that easy to find a good tool to design your APIs using AsyncAPI. An online editor is available at [https://studio.asyncapi.com/](https://studio.asyncapi.com/), but it's quite slow on a slow internet connection / old computer. Also, it's not easy navigating through all the sections of the AsyncAPI specification.

Due to these reasons, I decided to create a simple tool to design my APIs using AsyncAPI, with a big difference being that API specification is not written directly in AsyncAPI, but using Python classes and objects.
