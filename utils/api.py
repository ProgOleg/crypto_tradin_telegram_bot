import aiohttp
import asyncio
import decimal
import time
import hashlib
import hmac
import json
from urllib import parse


from jsonpath_ng.ext import parser

import config
from utils import helpers


class KunaApi:

    BTC = "btc"
    ETH = "eth"
    LTC = "ltc"
    XRP = "xrp"
    TRX = "trx"
    USDT = "usdt"

    CRYPTO_KEYS = (
        BTC, ETH, LTC, XRP, TRX, USDT
    )

    @classmethod
    async def _get_exchange(cls, crypto_alias):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    config.KUNA_EXCHANGE_RATES + crypto_alias, headers={"Accept": "application/json"}
            ) as response:
                return await response.json()

    @classmethod
    def _get_uah_cost(cls, data):
        value = data.get("uah")
        return decimal.Decimal(value)

    @classmethod
    async def get_btc_cost(cls):
        data = await cls._get_exchange(cls.BTC)
        return cls._get_uah_cost(data)

    @classmethod
    async def get_eth_cost(cls):
        data = await cls._get_exchange(cls.ETH)
        return cls._get_uah_cost(data)

    @classmethod
    async def get_ltc_cost(cls):
        data = await cls._get_exchange(cls.LTC)
        return cls._get_uah_cost(data)

    @classmethod
    async def get_xrp_cost(cls):
        data = await cls._get_exchange(cls.XRP)
        return cls._get_uah_cost(data)

    @classmethod
    async def get_trx_cost(cls):
        data = await cls._get_exchange(cls.TRX)
        return cls._get_uah_cost(data)

    @classmethod
    async def get_usdt_cost(cls):
        data = await cls._get_exchange(cls.USDT)
        return cls._get_uah_cost(data)

    @classmethod
    async def get_cost(cls, crypto):
        getters = {
            cls.BTC: cls.get_btc_cost,
            cls.ETH: cls.get_eth_cost,
            cls.LTC: cls.get_ltc_cost,
            cls.XRP: cls.get_xrp_cost,
            cls.TRX: cls.get_trx_cost,
            cls.USDT: cls.get_usdt_cost,
        }

        func = getters.get(crypto)
        return await func() or None

    @classmethod
    async def _get_fees(cls):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    config.KUNA_FEES_URL, headers={"Accept": "application/json"}
            ) as response:
                return await response.json()

    @classmethod
    async def parse_fees(cls, crypto: str):
        # in the future, get a margin for the withdrawal of the hryvnia!
        data = await cls._get_fees()
        res = parser.parse(f"$[?(@.currency='{crypto}')]").find(data)
        value = res[0].value
        min_deposit = value["min_deposit"]["amount"]
        withdraw_fees = value["withdraw_fees"]
        fees_type = withdraw_fees[0]["type"]
        fees_amount = withdraw_fees[0]["asset"]["amount"]
        # HARD CODE fees_amount for USDT crypto!!!
        if crypto == cls.USDT:
            fees_amount = 1
        return decimal.Decimal(str(min_deposit)), fees_type, decimal.Decimal(str(fees_amount))

    @classmethod
    async def calculate_total_cost(
            cls,
            from_: str,
            to: str,
            quantity: decimal.Decimal,
            exchange_type: str
    ):
        # количество * курс(uah) *
        cost_for_1_unit, _fees = await asyncio.gather(
            cls.get_cost_tickers(from_, to),
            cls.parse_fees(to if exchange_type == helpers.Constant.BUY else from_)
        )
        _, fees_type, fees_amount = _fees
        cost_uah = cost_for_1_unit * quantity
        if fees_type != "fixed":
            fees = fees_amount * cost_for_1_unit
            cost_uah_plus_fees = cost_uah + fees
        else:
            fees = fees_amount + cost_for_1_unit
            cost_uah_plus_fees = cost_uah + fees
        markup = cost_uah_plus_fees * config.MARKUP
        if exchange_type == helpers.Constant.BUY:
            total = cost_uah_plus_fees + markup
        elif exchange_type == helpers.Constant.SELL:
            total = cost_uah_plus_fees - markup
        else:
            assert False
        return round(total, 2)

    @classmethod
    async def calculate_total_cost_v2(
            cls,
            from_: str,
            to: str,
            quantity: decimal.Decimal,
            exchange_type: str
    ):
        # количество * курс(uah) *
        cost_for_1_unit, is_reversed = await cls.get_cost_tickers(from_, to)
        cost_for_1_unit = 1 / cost_for_1_unit if is_reversed else cost_for_1_unit
        total_cost = cost_for_1_unit * quantity
        markup = total_cost * config.MARKUP
        if exchange_type == helpers.Constant.BUY:
            total = total_cost + markup
        elif exchange_type == helpers.Constant.SELL:
            total = total_cost - markup
        else:
            assert False
        if to in [helpers.Constant.USD, helpers.Constant.RUB, helpers.Constant.UAH]:
            return round(total, 2)
        else:
            return round(total, 6)

    @classmethod
    async def _encode_privat_method(cls, path: str, body: dict):
        path_ = parse.urlsplit("https://api.kuna.io/v3/auth/deposit").path
        nonce = str(int(time.time() * 1000.0))
        msg = path_.encode('ascii') + nonce.encode('ascii') + json.dumps(body).encode('ascii')
        kun_signature = hmac.new(bytes(config.KUNA_SECRET_KEY, 'utf-8'), msg, hashlib.sha384).hexdigest()
        headers = {
            "accept": "application/json",
            "kun-nonce": nonce,
            "kun-apikey": config.KUNA_PUBLIC_KEY,
            "kun-signature": kun_signature
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(path, headers=headers, json=body) as response:
                if response.status == 200:
                    return await response.json()

    @classmethod
    async def get_payment_url(cls, currency: str, amount: float):
        body = {
            "currency": currency,
            "amount": int(amount),
            "payment_service": "default",
            "deposit_from": "4111111111111111"
        }
        res = await cls._encode_privat_method(config.KUNDA_DEPOSIT_URL, body) or {}
        payment_url = res.get("payment_url")
        return payment_url

    @classmethod
    async def _get_cost_tickers(cls, from_, to) -> decimal.Decimal:
        symbols = from_ + to
        async with aiohttp.ClientSession() as session:
            async with session.get(config.KUNA_TIKETS_URL, data={"symbols": symbols}) as response:
                if response.status == 200:
                    cost = await response.json()
                    res = cost[0][7] or 0
                    res = decimal.Decimal(str(res))
                    return res

    @classmethod
    async def get_cost_tickers(cls, from_, to) -> (decimal.Decimal, bool):
        # first argument is cost for 1 unit, second is flag reverse args to from
        is_reversed = False
        res = await cls._get_cost_tickers(from_, to)
        if not res:
            res = await cls._get_cost_tickers(to, from_)
            is_reversed = True
        return res, is_reversed



if __name__ == '__main__':
    # asyncio.run(KunaApi.calculate_total_cost(KunaApi.BTC))
    print(asyncio.run(KunaApi.get_payment_url("uah", 29000)))
    # print(asyncio.run(KunaApi.calculate_total_cost_v2("btc", "eth", decimal.Decimal(1), helpers.Constant.BUY)))
