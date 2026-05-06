"""Test Home Assistant volume utility functions."""

from ipaddress import ip_address

from tryke import expect, test

from homeassistant.util import network as network_util


@test
def is_loopback() -> None:
    """Test loopback addresses."""
    expect(network_util.is_loopback(ip_address("127.0.0.2"))).to_be_truthy()
    expect(network_util.is_loopback(ip_address("127.0.0.1"))).to_be_truthy()
    expect(network_util.is_loopback(ip_address("::1"))).to_be_truthy()
    expect(network_util.is_loopback(ip_address("::ffff:127.0.0.0"))).to_be_truthy()
    expect(network_util.is_loopback(ip_address("0:0:0:0:0:0:0:1"))).to_be_truthy()
    expect(network_util.is_loopback(ip_address("0:0:0:0:0:ffff:7f00:1"))).to_be_truthy()
    expect(network_util.is_loopback(ip_address("104.26.5.238"))).to_be_falsy()
    expect(
        network_util.is_loopback(ip_address("2600:1404:400:1a4::356e"))
    ).to_be_falsy()


@test
def is_private() -> None:
    """Test private addresses."""
    expect(network_util.is_private(ip_address("192.168.0.1"))).to_be_truthy()
    expect(network_util.is_private(ip_address("172.16.12.0"))).to_be_truthy()
    expect(network_util.is_private(ip_address("10.5.43.3"))).to_be_truthy()
    expect(network_util.is_private(ip_address("fd12:3456:789a:1::1"))).to_be_truthy()
    expect(network_util.is_private(ip_address("127.0.0.1"))).to_be_falsy()
    expect(network_util.is_private(ip_address("::1"))).to_be_falsy()


@test
def is_link_local() -> None:
    """Test link local addresses."""
    expect(network_util.is_link_local(ip_address("169.254.12.3"))).to_be_truthy()
    expect(
        network_util.is_link_local(ip_address("fe80::1234:5678:abcd"))
    ).to_be_truthy()
    expect(network_util.is_link_local(ip_address("127.0.0.1"))).to_be_falsy()
    expect(network_util.is_link_local(ip_address("::1"))).to_be_falsy()


@test
def is_invalid() -> None:
    """Test invalid address."""
    expect(network_util.is_invalid(ip_address("0.0.0.0"))).to_be_truthy()
    expect(network_util.is_invalid(ip_address("127.0.0.1"))).to_be_falsy()


@test
def is_local() -> None:
    """Test local addresses."""
    expect(network_util.is_local(ip_address("192.168.0.1"))).to_be_truthy()
    expect(network_util.is_local(ip_address("127.0.0.1"))).to_be_truthy()
    expect(network_util.is_local(ip_address("fd12:3456:789a:1::1"))).to_be_truthy()
    expect(network_util.is_local(ip_address("fe80::1234:5678:abcd"))).to_be_truthy()
    expect(network_util.is_local(ip_address("::ffff:192.168.0.1"))).to_be_truthy()
    expect(network_util.is_local(ip_address("208.5.4.2"))).to_be_falsy()
    expect(network_util.is_local(ip_address("198.51.100.1"))).to_be_falsy()
    expect(network_util.is_local(ip_address("2001:DB8:FA1::1"))).to_be_falsy()
    expect(network_util.is_local(ip_address("::ffff:208.5.4.2"))).to_be_falsy()


@test
def is_ip_address() -> None:
    """Test if strings are IP addresses."""
    expect(network_util.is_ip_address("192.168.0.1")).to_be_truthy()
    expect(network_util.is_ip_address("8.8.8.8")).to_be_truthy()
    expect(network_util.is_ip_address("::ffff:127.0.0.0")).to_be_truthy()
    expect(network_util.is_ip_address("192.168.0.999")).to_be_falsy()
    expect(network_util.is_ip_address("192.168.0.0/24")).to_be_falsy()
    expect(network_util.is_ip_address("example.com")).to_be_falsy()


@test
def is_ipv4_address() -> None:
    """Test if strings are IPv4 addresses."""
    expect(network_util.is_ipv4_address("192.168.0.1") is True).to_be(True)
    expect(network_util.is_ipv4_address("8.8.8.8") is True).to_be(True)
    expect(network_util.is_ipv4_address("192.168.0.999") is False).to_be(True)
    expect(network_util.is_ipv4_address("192.168.0.0/24") is False).to_be(True)
    expect(network_util.is_ipv4_address("example.com") is False).to_be(True)


@test
def is_ipv6_address() -> None:
    """Test if strings are IPv6 addresses."""
    expect(network_util.is_ipv6_address("::1") is True).to_be(True)
    expect(network_util.is_ipv6_address("8.8.8.8") is False).to_be(True)
    expect(network_util.is_ipv6_address("8.8.8.8") is False).to_be(True)


@test
def is_valid_host() -> None:
    """Test if strings are IPv6 addresses."""
    expect(network_util.is_host_valid("::1")).to_be_truthy()
    expect(network_util.is_host_valid("::ffff:127.0.0.0")).to_be_truthy()
    expect(
        network_util.is_host_valid("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
    ).to_be_truthy()
    expect(network_util.is_host_valid("8.8.8.8")).to_be_truthy()
    expect(network_util.is_host_valid("local")).to_be_truthy()
    expect(network_util.is_host_valid("host-host")).to_be_truthy()
    expect(network_util.is_host_valid("example.com")).to_be_truthy()
    expect(network_util.is_host_valid("example.com.")).to_be_truthy()
    expect(network_util.is_host_valid("Example123.com")).to_be_truthy()
    expect(network_util.is_host_valid("")).to_be_falsy()
    expect(network_util.is_host_valid("192.168.0.1:8080")).to_be_falsy()
    expect(network_util.is_host_valid("192.168.0.999")).to_be_falsy()
    expect(network_util.is_host_valid("2001:hb8::1:0:0:1")).to_be_falsy()
    expect(network_util.is_host_valid("-host-host")).to_be_falsy()
    expect(network_util.is_host_valid("host-host-")).to_be_falsy()
    expect(network_util.is_host_valid("host_host")).to_be_falsy()
    expect(network_util.is_host_valid("example.com/path")).to_be_falsy()
    expect(network_util.is_host_valid("example.com:8080")).to_be_falsy()
    expect(network_util.is_host_valid("verylonghostname" * 4)).to_be_falsy()
    expect(network_util.is_host_valid("verydeepdomain." * 18)).to_be_falsy()


@test
def normalize_url() -> None:
    """Test the normalizing of URLs."""
    expect(network_util.normalize_url("http://example.com")).to_equal(
        "http://example.com"
    )
    expect(network_util.normalize_url("https://example.com")).to_equal(
        "https://example.com"
    )
    expect(network_util.normalize_url("https://example.com/")).to_equal(
        "https://example.com"
    )
    expect(network_util.normalize_url("https://example.com:443")).to_equal(
        "https://example.com"
    )
    expect(network_util.normalize_url("http://example.com:80")).to_equal(
        "http://example.com"
    )
    expect(network_util.normalize_url("https://example.com:80")).to_equal(
        "https://example.com:80"
    )
    expect(network_util.normalize_url("http://example.com:443")).to_equal(
        "http://example.com:443"
    )
    expect(network_util.normalize_url("https://example.com:443/test/")).to_equal(
        "https://example.com/test"
    )
    expect(network_util.normalize_url("/test/")).to_equal("/test")
