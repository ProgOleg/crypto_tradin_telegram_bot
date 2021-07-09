import typing

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from utils import validators


class StartScreen:

    new_exchange = KeyboardButton("🔄 Новый обмен",)
    language = KeyboardButton("🗣 Язык")
    support = KeyboardButton("ℹ️ Поддержка")
    my_exchange = KeyboardButton("💎 Мои обмены")
    information = KeyboardButton("ℹ️ Информация")

    buttons = ReplyKeyboardMarkup(
        resize_keyboard=True
    ).row(
        my_exchange, support
    ).row(
        information, language
    ).row(new_exchange)


class MyExchangeStep1:
    buy = InlineKeyboardButton("Купить", callback_data='event?value=buy_event')
    sell = InlineKeyboardButton("Продать", callback_data="event?value=sell_event")

    buttons = InlineKeyboardMarkup(row_width=2).add(buy, sell)


def exchange_step_2():
    back = InlineKeyboardButton("↩️ Назад", callback_data="exchange_step2")
    buttons = InlineKeyboardMarkup().row(back)
    return buttons


def exchange_step_3():
    back = InlineKeyboardButton("↩️ Назад", callback_data="exchange_step4")
    buttons = InlineKeyboardMarkup().row(back)
    return buttons


def exchange_step_3_4(order_id, url: typing.Optional[str] = None):
    # back = InlineKeyboardButton("↩️ Назад", callback_data="exchange_step3_4")
    payment_url = InlineKeyboardButton("Ссылка на оплату", url=url)
    paid = InlineKeyboardButton("✅ Оплачено", callback_data=f"exchange_step5?value={order_id}")
    if not url:
        buttons = InlineKeyboardMarkup().row(paid)
    else:
        buttons = InlineKeyboardMarkup().row(paid).row(payment_url)

    return buttons


def exchange_step_4(order_id):
    paid = InlineKeyboardButton("✅ Оплачено", callback_data=f"exchange_step5?value={order_id}")
    buttons = InlineKeyboardMarkup().row(paid)
    return buttons


class Admin:

    @classmethod
    def order_request(cls, order_id):

        approve = InlineKeyboardButton("✅ Готово", callback_data=f"admin_approve?order_id={order_id}")
        return InlineKeyboardMarkup().row(approve)


class ButtonsConst:
    BUY = "buy_event"
    SELL = "sell_event"

    BTC = "btc"
    ETH = "eth"
    LTC = "ltc"
    XRP = "xrp"
    TRX = "trx"
    USDT = "usdt"

    USDC = "usdc"
    BCH = "bch"
    XLM = "xlm"
    DASH = "dash"
    TON = "ton"
    SHIB = "shib"
    DOGE = "doge"

    UAH = "uah"
    RUB = "rub"
    USD = "usd"

    CONST_RELATIONS = {
        BTC: {UAH, USDT, USDC, RUB, USD, ETH},
        ETH: {UAH, BTC, USDT, RUB},
        LTC: {UAH, USDT},
        XRP: {UAH, USDT, RUB},
        TRX: {UAH, USDT},
        USDT: {UAH, BTC, ETH, RUB, USD, XRP, LTC, TRX, USDC, BCH, XLM, DASH, TON, SHIB, DOGE},
        USDC: {UAH, BTC, USDT},
        BCH: {UAH, USDT},
        XLM: {UAH, USDT},
        DASH: {UAH, USDT},
        TON: {USDT},
        SHIB: {UAH, USDT},
        DOGE: {UAH, USDT}
    }

    BACK_BUTTON_VALUE = ""
    QUERY_PARAM_ALIAS = ""


class PaymentType(ButtonsConst):
    BACK_BUTTON_VALUE = "exchange_step2"

    VISA_KEY = "visa"
    QUIWI = "qiwi"
    VISA = "visa/mastercard"
    MOBILE = "mobile"
    BILL = "bill"

    DESCRIPTOR_VALUE = {
        VISA_KEY: "номер карты",
        QUIWI: "номер кошелька",
        MOBILE: "номер телефона",
        BILL: "номер кошелька"
    }

    VALIDATORS = {
        VISA_KEY: validators.bank_card_validator,
        MOBILE: validators.phone_validator,
        BILL: validators.bill_validator,
        QUIWI: validators.qiwi_validator
    }

    _collections = {
        QUIWI: [QUIWI.upper(), QUIWI],
        VISA_KEY: [VISA.upper(), VISA_KEY],
        MOBILE: ["Пополнение мобильного", MOBILE],
        BILL: ["Кошелек", BILL]
    }

    @classmethod
    def get_buttons(cls, btns: list):
        container = InlineKeyboardMarkup(row_width=3)
        for btn in btns:
            btn_name, btn_val = cls._collections.get(btn)
            container.row(InlineKeyboardButton(
                btn_name, callback_data=f"payment_type?value={btn_val}"
            ))
        container.row(InlineKeyboardButton("↩️ Назад", callback_data=cls.BACK_BUTTON_VALUE))
        return container

    @classmethod
    def get_payment_type_buttons(cls, query_path, fiat, exchange_type):
        if query_path == "fiat" and fiat in [cls.UAH, cls.RUB, cls.USD]:
            if fiat == cls.RUB:
                but = ["qiwi"]
            elif exchange_type == cls.SELL and fiat == cls.UAH:
                but = ["mobile", "visa"]
            else:
                but = ["visa"]
        else:
            but = ["bill"]
        return cls.get_buttons(but)


class ButtonsFabric(ButtonsConst):

    @classmethod
    def get_buttons(cls, coins):
        container = InlineKeyboardMarkup(row_width=3)
        temp_ = []

        def generator():
            for coin in coins:
                button = InlineKeyboardButton(
                    coin.upper(), callback_data=f"{cls.QUERY_PARAM_ALIAS}?value={coin}"
                )
                yield button

        for btn in generator():
            temp_.append(btn)
            if len(temp_) == 3:
                container.row(*temp_)
                temp_.clear()
        else:
            container.row(*temp_)
            container.row(InlineKeyboardButton("↩️ Назад", callback_data=cls.BACK_BUTTON_VALUE))
        return container


class Crypto(ButtonsFabric):
    BACK_BUTTON_VALUE = "new_exchange?"
    QUERY_PARAM_ALIAS = "crypto"

    @classmethod
    def get_all_crypto_btn(cls):
        return cls.get_buttons(cls.CONST_RELATIONS.keys())


class Fiat(ButtonsFabric):
    BACK_BUTTON_VALUE = "exchange_step1?"
    QUERY_PARAM_ALIAS = "fiat"

    @classmethod
    def get_button_separate_coin(cls, value: str):
        coins = cls.CONST_RELATIONS.get(value)
        return cls.get_buttons(coins)
