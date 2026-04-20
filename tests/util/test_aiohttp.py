"""Test aiohttp request helper."""

from aiohttp import web
from tryke import expect, test

from homeassistant.util import aiohttp


@test
async def request_json() -> None:
    """Test a JSON request."""
    request = aiohttp.MockRequest(b'{"hello": 2}', mock_source="test")
    expect(request.status).to_equal(200)
    expect(await request.json()).to_equal({"hello": 2})


@test
async def request_text() -> None:
    """Test bytes in request."""
    request = aiohttp.MockRequest(b"hello", status=201, mock_source="test")
    expect(request.body_exists).to_be_truthy()
    expect(request.status).to_equal(201)
    expect(await request.text()).to_equal("hello")


@test
async def request_body_exists() -> None:
    """Test body exists."""
    request = aiohttp.MockRequest(b"", mock_source="test")
    expect(request.body_exists).to_be_falsy()


@test
async def request_post_query() -> None:
    """Test a JSON request."""
    request = aiohttp.MockRequest(
        b"hello=2&post=true", query_string="get=true", method="POST", mock_source="test"
    )
    expect(request.method).to_equal("POST")
    expect(await request.post()).to_equal({"hello": "2", "post": "true"})
    expect(request.query).to_equal({"get": "true"})


@test
def serialize_text() -> None:
    """Test serializing a text response."""
    response = web.Response(status=201, text="Hello")
    expect(aiohttp.serialize_response(response)).to_equal(
        {
            "status": 201,
            "body": "Hello",
            "headers": {"Content-Type": "text/plain; charset=utf-8"},
        }
    )


@test
def serialize_body_str() -> None:
    """Test serializing a response with a str as body."""
    response = web.Response(status=201, body="Hello")
    expect(aiohttp.serialize_response(response)).to_equal(
        {
            "status": 201,
            "body": "Hello",
            "headers": {"Content-Type": "text/plain; charset=utf-8"},
        }
    )


@test
def serialize_body_None() -> None:
    """Test serializing a response with a str as body."""
    response = web.Response(status=201, body=None)
    expect(aiohttp.serialize_response(response)).to_equal(
        {
            "status": 201,
            "body": None,
            "headers": {},
        }
    )


@test
def serialize_body_bytes() -> None:
    """Test serializing a response with a str as body."""
    response = web.Response(status=201, body=b"Hello")
    expect(aiohttp.serialize_response(response)).to_equal(
        {
            "status": 201,
            "body": "Hello",
            "headers": {},
        }
    )


@test
def serialize_json() -> None:
    """Test serializing a JSON response."""
    response = web.json_response({"how": "what"})
    expect(aiohttp.serialize_response(response)).to_equal(
        {
            "status": 200,
            "body": '{"how": "what"}',
            "headers": {"Content-Type": "application/json; charset=utf-8"},
        }
    )
