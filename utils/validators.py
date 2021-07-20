import re


def email_validator(value: str) -> bool:
    regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    if re.match(regex, value):
        return True


def phone_validator(value: str) -> bool:
    expected_operator = {
        "39", "50", "63", "66", "67", "68", "70", "73", "80", "90",
        "91", "92", "93", "94", "95", "96", "97", "98", "99"
    }
    return any(filter(lambda x: f"+380{x}" == value[:6], expected_operator)) and len(value) == 13


def qiwi_validator(value: str) -> bool:
    # Not implemented yet
    return True if len(value) != 0 else False


def bill_validator(value: str) -> bool:
    # Not implemented yet
    return True if len(value) != 0 else False


def memo_validator(value: str) -> bool:
    # Not implemented yet
    return True if len(value) != 0 else False


def bank_card_validator(value: str) -> bool:
    return 12 < len(value) < 17 and (value[0] == "4" or value[0] == "5" and "0" < value[1] < "6")

