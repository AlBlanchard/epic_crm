import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from crm.utils.validations import Validations


def test_validate_user_id_valid():
    assert Validations.validate_user_id("123", ["123", "456"]) is True


def test_validate_user_id_invalid():
    with pytest.raises(ValueError):
        Validations.validate_user_id("999", ["123", "456"])


def test_validate_number_valid():
    assert Validations.validate_number("123") is None


def test_validate_number_invalid():
    with pytest.raises(ValueError):
        Validations.validate_number("12a")


def test_is_in_list_valid():
    assert Validations.is_in_list("apple", ["apple", "banana"]) is True


def test_is_in_list_invalid():
    with pytest.raises(ValueError):
        Validations.is_in_list("orange", ["apple", "banana"])


def test_not_empty_valid():
    assert Validations.not_empty("hello") is True


@pytest.mark.parametrize("value", ["", "   "])
def test_not_empty_invalid(value):
    with pytest.raises(ValueError):
        Validations.not_empty(value)


def test_validate_year_valid():
    Validations.validate_year(datetime.now().year)


def test_validate_year_invalid():
    with pytest.raises(ValueError):
        Validations.validate_year(datetime.now().year - 1)


@pytest.mark.parametrize("month", [1, 12])
def test_validate_month_valid(month):
    Validations.validate_month(month)


@pytest.mark.parametrize("month", [0, 13])
def test_validate_month_invalid(month):
    with pytest.raises(ValueError):
        Validations.validate_month(month)


def test_validate_day_in_month_valid():
    Validations.validate_day_in_month(28, 2, 2024)  # année bissextile


@pytest.mark.parametrize("day", [0, 32])
def test_validate_day_in_month_invalid_range(day):
    with pytest.raises(ValueError):
        Validations.validate_day_in_month(day, 1, 2024)


def test_validate_day_in_month_invalid_too_large():
    with pytest.raises(ValueError):
        Validations.validate_day_in_month(31, 2, 2023)


@pytest.mark.parametrize("hour", [0, 23])
def test_validate_hour_valid(hour):
    Validations.validate_hour(hour)


@pytest.mark.parametrize("hour", [-1, 24])
def test_validate_hour_invalid(hour):
    with pytest.raises(ValueError):
        Validations.validate_hour(hour)


@pytest.mark.parametrize("minute", [0, 59])
def test_validate_minute_valid(minute):
    Validations.validate_minute(minute)


@pytest.mark.parametrize("minute", [-1, 60])
def test_validate_minute_invalid(minute):
    with pytest.raises(ValueError):
        Validations.validate_minute(minute)


def test_validate_future_datetime_valid():
    future = datetime.now() + timedelta(days=1)
    Validations.validate_future_datetime(future)


def test_validate_future_datetime_invalid():
    past = datetime.now() - timedelta(days=1)
    with pytest.raises(ValueError):
        Validations.validate_future_datetime(past)


def test_validate_date_order_valid():
    start = datetime.now()
    end = start + timedelta(days=1)
    Validations.validate_date_order(start, end)


def test_validate_date_order_invalid():
    start = datetime.now()
    end = start
    with pytest.raises(ValueError):
        Validations.validate_date_order(start, end)


def test_validate_str_max_length_valid():
    Validations.validate_str_max_length("ok", max_length=5)


def test_validate_str_max_length_invalid():
    with pytest.raises(ValueError):
        Validations.validate_str_max_length("toolong", max_length=5)


def test_validate_email_valid():
    Validations.validate_email("test@example.com")


@pytest.mark.parametrize("email", ["bad@", "no_at.com", "x" * 255 + "@a.com"])
def test_validate_email_invalid(email):
    with pytest.raises(ValueError):
        Validations.validate_email(email)


def test_validate_int_max_length_valid():
    Validations.validate_int_max_length("123", max_length=5)


@pytest.mark.parametrize("value", [None, "abc", 10**11])
def test_validate_int_max_length_invalid(value):
    with pytest.raises(ValueError):
        Validations.validate_int_max_length(value, max_length=10)


def test_validate_phone_valid():
    Validations.validate_phone("+1234567890")


@pytest.mark.parametrize("phone", ["", "abcd", "1" * 20])
def test_validate_phone_invalid(phone):
    with pytest.raises(ValueError):
        Validations.validate_phone(phone)


def test_validate_currency_valid():
    Validations.validate_currency("123.45")
    Validations.validate_currency(Decimal("99.99"))


@pytest.mark.parametrize("value", ["12.345", "abc"])
def test_validate_currency_invalid(value):
    with pytest.raises(ValueError):
        Validations.validate_currency(value)


def test_validate_positive_integer_valid():
    Validations.validate_positive_integer("123", max_length=5)


@pytest.mark.parametrize("value", ["0", "-1", "abc"])
def test_validate_positive_integer_invalid(value):
    with pytest.raises(ValueError):
        Validations.validate_positive_integer(value)


def test_validate_employee_number_valid():
    Validations.validate_employee_number("123", [456, 789])


def test_validate_employee_number_invalid():
    with pytest.raises(ValueError):
        Validations.validate_employee_number("123", [123, 456])
