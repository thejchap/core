"""Test Home Assistant ssl utility functions."""

from tryke import expect, test

from homeassistant.util.ssl import (
    SSL_ALPN_HTTP11,
    SSL_ALPN_HTTP11_HTTP2,
    SSL_ALPN_NONE,
    SSLCipherList,
    client_context,
    client_context_no_verify,
    create_client_context,
    create_no_verify_ssl_context,
    get_default_context,
    get_default_no_verify_context,
)


@test
def ssl_context_caching() -> None:
    """Test that SSLContext instances are cached correctly."""
    expect(client_context() is client_context(SSLCipherList.PYTHON_DEFAULT)).to_be(True)
    expect(
        create_no_verify_ssl_context()
        is create_no_verify_ssl_context(SSLCipherList.PYTHON_DEFAULT)
    ).to_be(True)


@test
def ssl_context_cipher_bucketing() -> None:
    """Test that SSL contexts are bucketed by cipher list."""
    default_ctx = client_context(SSLCipherList.PYTHON_DEFAULT)
    modern_ctx = client_context(SSLCipherList.MODERN)
    intermediate_ctx = client_context(SSLCipherList.INTERMEDIATE)
    insecure_ctx = client_context(SSLCipherList.INSECURE)

    expect(default_ctx is not modern_ctx).to_be(True)
    expect(default_ctx is not intermediate_ctx).to_be(True)
    expect(default_ctx is not insecure_ctx).to_be(True)
    expect(modern_ctx is not intermediate_ctx).to_be(True)
    expect(modern_ctx is not insecure_ctx).to_be(True)
    expect(intermediate_ctx is not insecure_ctx).to_be(True)

    expect(client_context(SSLCipherList.PYTHON_DEFAULT) is default_ctx).to_be(True)
    expect(client_context(SSLCipherList.MODERN) is modern_ctx).to_be(True)


@test
def no_verify_ssl_context_cipher_bucketing() -> None:
    """Test that no-verify SSL contexts are bucketed by cipher list."""
    default_ctx = create_no_verify_ssl_context(SSLCipherList.PYTHON_DEFAULT)
    modern_ctx = create_no_verify_ssl_context(SSLCipherList.MODERN)

    expect(default_ctx is not modern_ctx).to_be(True)

    expect(
        create_no_verify_ssl_context(SSLCipherList.PYTHON_DEFAULT) is default_ctx
    ).to_be(True)
    expect(create_no_verify_ssl_context(SSLCipherList.MODERN) is modern_ctx).to_be(True)


@test
def create_client_context_independent() -> None:
    """Test create_client_context independence."""
    shared_context = client_context()
    independent_context_1 = create_client_context()
    independent_context_2 = create_client_context()
    expect(shared_context is not independent_context_1).to_be(True)
    expect(independent_context_1 is not independent_context_2).to_be(True)


@test
def ssl_context_alpn_bucketing() -> None:
    """Test that SSL contexts are bucketed by ALPN protocols.

    Different ALPN protocol configurations should return different cached contexts
    to prevent downstream libraries (e.g., httpx/httpcore) from mutating shared
    contexts with incompatible settings.
    """
    http1_context = client_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11)
    http2_context = client_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11_HTTP2)
    no_alpn_context = client_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_NONE)
    expect(http1_context is not http2_context).to_be(True)
    expect(http1_context is not no_alpn_context).to_be(True)
    expect(http2_context is not no_alpn_context).to_be(True)

    expect(
        client_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11) is http1_context
    ).to_be(True)
    expect(
        client_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11_HTTP2)
        is http2_context
    ).to_be(True)
    expect(
        client_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_NONE) is no_alpn_context
    ).to_be(True)

    http1_no_verify = client_context_no_verify(
        SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11
    )
    http2_no_verify = client_context_no_verify(
        SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11_HTTP2
    )
    no_alpn_no_verify = client_context_no_verify(
        SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_NONE
    )
    expect(http1_no_verify is not http2_no_verify).to_be(True)
    expect(http1_no_verify is not no_alpn_no_verify).to_be(True)
    expect(http2_no_verify is not no_alpn_no_verify).to_be(True)

    expect(
        create_no_verify_ssl_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11)
        is http1_no_verify
    ).to_be(True)
    expect(
        create_no_verify_ssl_context(
            SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11_HTTP2
        )
        is http2_no_verify
    ).to_be(True)
    expect(
        create_no_verify_ssl_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_NONE)
        is no_alpn_no_verify
    ).to_be(True)


@test
def ssl_context_insecure_alpn_bucketing() -> None:
    """Test that INSECURE cipher list SSL contexts are bucketed by ALPN protocols.

    INSECURE cipher list is used by some integrations that need to connect to
    devices with outdated TLS implementations.
    """
    http1_context = client_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11)
    http2_context = client_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11_HTTP2)
    no_alpn_context = client_context(SSLCipherList.INSECURE, SSL_ALPN_NONE)
    expect(http1_context is not http2_context).to_be(True)
    expect(http1_context is not no_alpn_context).to_be(True)
    expect(http2_context is not no_alpn_context).to_be(True)

    expect(
        client_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11) is http1_context
    ).to_be(True)
    expect(
        client_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11_HTTP2) is http2_context
    ).to_be(True)
    expect(
        client_context(SSLCipherList.INSECURE, SSL_ALPN_NONE) is no_alpn_context
    ).to_be(True)

    http1_no_verify = client_context_no_verify(SSLCipherList.INSECURE, SSL_ALPN_HTTP11)
    http2_no_verify = client_context_no_verify(
        SSLCipherList.INSECURE, SSL_ALPN_HTTP11_HTTP2
    )
    no_alpn_no_verify = client_context_no_verify(SSLCipherList.INSECURE, SSL_ALPN_NONE)
    expect(http1_no_verify is not http2_no_verify).to_be(True)
    expect(http1_no_verify is not no_alpn_no_verify).to_be(True)
    expect(http2_no_verify is not no_alpn_no_verify).to_be(True)

    expect(
        create_no_verify_ssl_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11)
        is http1_no_verify
    ).to_be(True)
    expect(
        create_no_verify_ssl_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11_HTTP2)
        is http2_no_verify
    ).to_be(True)
    expect(
        create_no_verify_ssl_context(SSLCipherList.INSECURE, SSL_ALPN_NONE)
        is no_alpn_no_verify
    ).to_be(True)


@test
def get_default_context_uses_http1_alpn() -> None:
    """Test that get_default_context returns context with HTTP1 ALPN."""
    default_ctx = get_default_context()
    default_no_verify_ctx = get_default_no_verify_context()

    expect(
        default_ctx is client_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11)
    ).to_be(True)
    expect(
        default_no_verify_ctx
        is client_context_no_verify(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11)
    ).to_be(True)


@test
def client_context_default_no_alpn() -> None:
    """Test that client_context defaults to no ALPN for backward compatibility."""
    default_ctx = client_context()
    http1_ctx = client_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_HTTP11)

    expect(default_ctx is not http1_ctx).to_be(True)
    expect(
        default_ctx is client_context(SSLCipherList.PYTHON_DEFAULT, SSL_ALPN_NONE)
    ).to_be(True)
