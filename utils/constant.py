
class Constants:
    BUY = "buy_event"
    SELL = "sell_event"

    BTC = "btc"
    ETH = "eth"
    LTC = "ltc"
    XRP = "xrp"
    TRX = "trx"
    USDT_TRC20 = "usdt(trc20)"
    USDT_ERC20 = "usdt(erc20)"
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

    FIAT = {UAH, RUB, USD}
    MEMO_COINS = {XRP, XLM}

    QUIWI = "qiwi"
    VISA = "visa/mastercard"
    MOBILE = "mobile"
    BILL = "bill"
    VISA_KEY = "visa"

    CONST_RELATIONS = {
        BTC: {UAH, USDT_TRC20, USDT_ERC20, USDC, RUB, USD, ETH},
        ETH: {UAH, BTC, USDT_TRC20, USDT_ERC20, RUB},
        LTC: {UAH, USDT_TRC20, USDT_ERC20},
        XRP: {UAH, USDT_TRC20, USDT_ERC20, RUB},
        USDT_TRC20: {UAH, BTC, ETH, RUB, USD, XRP, LTC, TRX, USDC, BCH, XLM, DASH, TON, SHIB, DOGE},
        USDT_ERC20: {UAH, BTC, ETH, RUB, USD, XRP, LTC, TRX, USDC, BCH, XLM, DASH, TON, SHIB, DOGE},
        TRX: {UAH, USDT_TRC20, USDT_ERC20},
        USDC: {UAH, BTC, USDT_TRC20, USDT_ERC20},
        BCH: {UAH, USDT_TRC20, USDT_ERC20},
        XLM: {UAH, USDT_TRC20, USDT_ERC20},
        DASH: {UAH, USDT_TRC20, USDT_ERC20},
        TON: {USDT_TRC20, USDT_ERC20},
        SHIB: {UAH, USDT_TRC20, USDT_ERC20},
        DOGE: {UAH, USDT_TRC20, USDT_ERC20}
    }
