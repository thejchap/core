"""Test Home Assistant util methods."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from tryke import expect, test

from homeassistant import util
from homeassistant.util import dt as dt_util


@test
def raise_if_invalid_filename() -> None:
    """Test raise_if_invalid_filename."""
    expect(util.raise_if_invalid_filename("test") is None).to_be(True)

    expect(lambda: util.raise_if_invalid_filename("/test")).to_raise(ValueError)
    expect(lambda: util.raise_if_invalid_filename("..test")).to_raise(ValueError)
    expect(lambda: util.raise_if_invalid_filename("\\test")).to_raise(ValueError)
    expect(lambda: util.raise_if_invalid_filename("\\../test")).to_raise(ValueError)


@test
def raise_if_invalid_path() -> None:
    """Test raise_if_invalid_path."""
    expect(util.raise_if_invalid_path("test/path") is None).to_be(True)

    expect(lambda: util.raise_if_invalid_path("~test/path")).to_raise(ValueError)
    expect(lambda: util.raise_if_invalid_path("~/../test/path")).to_raise(ValueError)


@test
def slugify() -> None:
    """Test slugify."""
    expect(util.slugify("T-!@#$!#@$!$est")).to_equal("t_est")
    expect(util.slugify("Test More")).to_equal("test_more")
    expect(util.slugify("Test_(More)")).to_equal("test_more")
    expect(util.slugify("Tèst_Mörê")).to_equal("test_more")
    expect(util.slugify("B8:27:EB:00:00:00")).to_equal("b8_27_eb_00_00_00")
    expect(util.slugify("test.com")).to_equal("test_com")
    expect(util.slugify("greg_phone - exp_wayp1")).to_equal("greg_phone_exp_wayp1")
    expect(util.slugify("We are, we are, a... Test Calendar")).to_equal(
        "we_are_we_are_a_test_calendar"
    )
    expect(util.slugify("Tèst_äöüß_ÄÖÜ")).to_equal("test_aouss_aou")
    expect(util.slugify("影師嗎")).to_equal("ying_shi_ma")
    expect(util.slugify("けいふぉんと")).to_equal("keihuonto")
    expect(util.slugify("$")).to_equal("unknown")
    expect(util.slugify("Ⓐ")).to_equal("a")
    expect(util.slugify("ⓑ")).to_equal("b")
    expect(util.slugify("$$$")).to_equal("unknown")
    expect(util.slugify("$something")).to_equal("something")
    expect(util.slugify("")).to_equal("")
    expect(util.slugify(None)).to_equal("")


@test
def repr_helper() -> None:
    """Test repr_helper."""
    expect(util.repr_helper("A")).to_equal("A")
    expect(util.repr_helper(5)).to_equal("5")
    expect(util.repr_helper(True)).to_equal("True")
    expect(util.repr_helper({"test": 1})).to_equal("test=1")

    tz = dt_util.get_time_zone("Europe/Copenhagen")
    with patch("homeassistant.util.dt.DEFAULT_TIME_ZONE", tz):
        expect(util.repr_helper(datetime(1986, 7, 9, 12, 0, 0))).to_equal(
            "1986-07-09T12:00:00+02:00"
        )


@test
def convert() -> None:
    """Test convert."""
    expect(util.convert("5", int)).to_equal(5)
    expect(util.convert("5", float)).to_equal(5.0)
    expect(util.convert("True", bool) is True).to_be(True)
    expect(util.convert("NOT A NUMBER", int, 1)).to_equal(1)
    expect(util.convert(None, int, 1)).to_equal(1)
    expect(util.convert(object, int, 1)).to_equal(1)


@test
def ensure_unique_string() -> None:
    """Test ensure_unique_string."""
    expect(util.ensure_unique_string("Beer", ["Beer", "Beer_2"])).to_equal("Beer_3")
    expect(util.ensure_unique_string("Beer", ["Wine", "Soda"])).to_equal("Beer")


@test
def throttle() -> None:
    """Test the add cooldown decorator."""
    calls1: list[int] = []
    calls2: list[int] = []

    @util.Throttle(timedelta(seconds=4))
    def test_throttle1() -> None:
        calls1.append(1)

    @util.Throttle(timedelta(seconds=4), timedelta(seconds=2))
    def test_throttle2() -> None:
        calls2.append(1)

    now = dt_util.utcnow()
    plus3 = now + timedelta(seconds=3)
    plus5 = plus3 + timedelta(seconds=2)

    # Call first time and ensure methods got called
    test_throttle1()
    test_throttle2()

    expect(len(calls1)).to_equal(1)
    expect(len(calls2)).to_equal(1)

    # Call second time. Methods should not get called
    test_throttle1()
    test_throttle2()

    expect(len(calls1)).to_equal(1)
    expect(len(calls2)).to_equal(1)

    # Call again, overriding throttle, only first one should fire
    test_throttle1(no_throttle=True)
    test_throttle2(no_throttle=True)

    expect(len(calls1)).to_equal(2)
    expect(len(calls2)).to_equal(1)

    with patch("homeassistant.util.utcnow", return_value=plus3):
        test_throttle1()
        test_throttle2()

    expect(len(calls1)).to_equal(2)
    expect(len(calls2)).to_equal(1)

    with patch("homeassistant.util.utcnow", return_value=plus5):
        test_throttle1()
        test_throttle2()

    expect(len(calls1)).to_equal(3)
    expect(len(calls2)).to_equal(2)


@test
def throttle_per_instance() -> None:
    """Test that the throttle method is done per instance of a class."""

    class Tester:
        """A tester class for the throttle."""

        @util.Throttle(timedelta(seconds=1))
        def hello(self) -> bool:
            """Test the throttle."""
            return True

    expect(Tester().hello()).to_be_truthy()
    expect(Tester().hello()).to_be_truthy()


@test
def throttle_on_method() -> None:
    """Test that throttle works when wrapping a method."""

    class Tester:
        """A tester class for the throttle."""

        def hello(self) -> bool:
            """Test the throttle."""
            return True

    tester = Tester()
    throttled = util.Throttle(timedelta(seconds=1))(tester.hello)

    expect(throttled()).to_be_truthy()
    expect(throttled() is None).to_be(True)


@test
def throttle_on_two_method() -> None:
    """Test that throttle works when wrapping two methods."""

    class Tester:
        """A test class for the throttle."""

        @util.Throttle(timedelta(seconds=1))
        def hello(self) -> bool:
            """Test the throttle."""
            return True

        @util.Throttle(timedelta(seconds=1))
        def goodbye(self) -> bool:
            """Test the throttle."""
            return True

    tester = Tester()

    expect(tester.hello()).to_be_truthy()
    expect(tester.goodbye()).to_be_truthy()


@test
@patch.object(util, "random")
def get_random_string(mock_random: MagicMock) -> None:
    """Test get random string."""
    results = ["A", "B", "C"]

    def mock_choice(choices: object) -> str:
        return results.pop(0)

    generator = MagicMock()
    generator.choice.side_effect = mock_choice
    mock_random.SystemRandom.return_value = generator

    expect(util.get_random_string(length=3)).to_equal("ABC")


@test
async def throttle_async() -> None:
    """Test Throttle decorator with async method."""

    @util.Throttle(timedelta(seconds=2))
    async def test_method() -> bool:
        """Only first call should return a value."""
        return True

    expect((await test_method()) is True).to_be(True)
    expect((await test_method()) is None).to_be(True)

    @util.Throttle(timedelta(seconds=2), timedelta(seconds=0.1))
    async def test_method2() -> bool:
        """Only first call should return a value."""
        return True

    expect((await test_method2()) is True).to_be(True)
    expect((await test_method2()) is None).to_be(True)


@test.cases(
    test.case("fooBar", input="fooBar", expected="foo_bar"),
    test.case("FooBar", input="FooBar", expected="foo_bar"),
    test.case("Foobar", input="Foobar", expected="foobar"),
    test.case("Foo.bar", input="Foo.bar", expected="foo_bar"),
    test.case("_foo-Bar", input="_foo-Bar", expected="_foo_bar"),
    test.case("HTTP", input="HTTP", expected="http"),
    test.case("HTTPResponse", input="HTTPResponse", expected="http_response"),
    test.case("iPhone", input="iPhone", expected="i_phone"),
    test.case("IPAddress", input="IPAddress", expected="ip_address"),
    test.case("IP_Address", input="IP_Address", expected="ip_address"),
    test.case("My IP Address", input="My IP Address", expected="my_ip_address"),
    test.case("LocalIP", input="LocalIP", expected="local_ip"),
    test.case("Python3Thing", input="Python3Thing", expected="python3_thing"),
    test.case("mTLS", input="mTLS", expected="m_tls"),
    test.case("DTrace", input="DTrace", expected="dtrace"),
    test.case("IPv4", input="IPv4", expected="ipv4"),
    test.case("ID", input="ID", expected="id"),
    test.case("empty", input="", expected=""),
)
def snakecase(input: str, expected: str) -> None:
    """Test snake casing a string."""
    expect(util.snakecase(input)).to_equal(expected)
