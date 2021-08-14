
class Constants:
    BUY = "buy_event"
    SELL = "sell_event"

    USDT = "usdt"

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
    CRYPTO_KOINS = {
        BTC, ETH, LTC, XRP, TRX, USDT_TRC20, USDT_ERC20,
        BCH, XLM, DASH, TON, SHIB, DOGE, USDC
    }
    ALL_COINS = CRYPTO_KOINS.union(FIAT)

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

    VARIATION_OF_COINS = {
        "btc,usdt", "btc,usdc", "btc,usd", "btc,uah", "btc,rub", "eth,btc", "eth,usdt", "eth,uah", "eth,rub",
        "ltc,usdt", "ltc,uah", "xrp,usdt", "xrp,uah", "xrp,rub", "bch,usdt", "xlm,usdt", "shib,usdt", "usdt,usdc",
        "usdt,usd", "doge,usdt", "ton,usdt", "trx,usdt", "usdt,uah", "usdt,rub", "dash,usdt", "trx,uah", "usdc,uah",
        "bch,uah", "xlm,uah", "dash,uah", "shib,uah", "doge,uah"
    }
