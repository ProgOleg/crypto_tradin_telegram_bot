import aiohttp
import asyncio
import decimal
import time
import hashlib
import hmac
import json
import logging
from urllib import parse


from jsonpath_ng.ext import parser

import config
from utils import helpers
from db.db_api import settings_api, cost_pair_api, fees_api
from utils import constant as const


class KunaApi(const.Constants):
    NORMALIZE_COINS = {
        const.Constants.USDT_ERC20: "usdt_eth",
        const.Constants.USDT_TRC20: "usdt_trx",
        const.Constants.BTC: "satoshi",
        const.Constants.SHIB: "shib_eth",
        const.Constants.USDC: "usdc_eth"
    }

    @classmethod
    def __revers_bool(cls, val: bool) -> bool:
        return False if val else True

    @classmethod
    async def _get_exchange(cls, crypto_alias):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    config.KUNA_EXCHANGE_RATES + crypto_alias, headers={"Accept": "application/json"}
            ) as response:
                return await response.json()

    @classmethod
    async def _get_fees(cls):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    config.KUNA_FEES_URL, headers={"Accept": "application/json"}
            ) as response:
                return await response.json()


    # @classmethod
    # async def calculate_total_cost(
    #         cls,
    #         from_: str,
    #         to: str,
    #         quantity: decimal.Decimal,
    #         exchange_type: str
    # ):
    #     # количество * курс(uah) *
    #     cost_for_1_unit, _fees = await asyncio.gather(
    #         cls.get_cost_tickers(from_, to),
    #         cls.parse_fees(to if exchange_type == helpers.Constant.BUY else from_)
    #     )
    #     _, fees_type, fees_amount = _fees
    #     cost_uah = cost_for_1_unit * quantity
    #     if fees_type == "fixed":
    #         fees = fees_amount + cost_for_1_unit
    #         cost_uah_plus_fees = cost_uah + fees
    #     else:
    #         fees = fees_amount * cost_for_1_unit
    #         cost_uah_plus_fees = cost_uah + fees
    #
    #     markup = cost_uah_plus_fees * config.MARKUP
    #     if exchange_type == helpers.Constant.BUY:
    #         total = cost_uah_plus_fees + markup
    #     elif exchange_type == helpers.Constant.SELL:
    #         total = cost_uah_plus_fees - markup
    #     else:
    #         assert False
    #     return round(total, 2)


    @classmethod
    async def calculate_total_cost_v2(
            cls,
            from_: str,
            to: str,
            quantity: decimal.Decimal,
            exchange_type: str
    ):
        # количество * курс(uah) *
        # normalize USDT(ERC20-TRC20) -> USDT
        from_, to = (cls.USDT if el in (cls.USDT_ERC20, cls.USDT_TRC20) else el for el in [from_, to])
        quantity = decimal.Decimal(quantity)
        cost_for_1_unit, is_reversed = await cls.get_cost_coins_pair(from_, to)
        cost_for_1_unit = 1 / cost_for_1_unit if is_reversed else cost_for_1_unit
        total_cost = cost_for_1_unit * quantity
        markup_value = await settings_api.SettingsApi().get_markup()
        markup = total_cost * markup_value
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
            "kun-signature": kun_signature,
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
    async def _get_cost_tickers_api(cls, from_, to) -> (decimal.Decimal, bool):
        # first argument is cost for 1 unit, second is flag reverse args to from
        is_reversed = False
        res = await cls._get_cost_tickers(from_, to)
        if not res:
            res = await cls._get_cost_tickers(to, from_)
            is_reversed = True
            if not res:
                logging.error(
                    f"get_cost_tickers return nothing! args: from_={from_}, to={to}"
                )
        return res or 0, is_reversed

    @classmethod
    async def get_cost_coins_pair(cls, from_: str, to: str) -> (decimal.Decimal, bool):
        # first argument is cost for 1 unit, second is flag reverse args to from
        is_reversed = False
        pair = [from_, to]
        split_pair = ",".join(pair)
        # optimization request from api
        if split_pair not in cls.VARIATION_OF_COINS:
            is_reversed = True
            pair = [to, from_]
            split_pair = ",".join(pair)

        res_from_db = await cost_pair_api.CostPairApi().retrieve_cost(split_pair)
        if res_from_db:
            cost, is_reversed_from_db = res_from_db
            is_reversed = cls.__revers_bool(is_reversed) if is_reversed_from_db else is_reversed
        else:
            cost, is_reversed_from_api = await cls._get_cost_tickers_api(*pair)
            if is_reversed_from_api:
                is_reversed = cls.__revers_bool(is_reversed) if is_reversed_from_api else is_reversed
            if cost:
                pair = [to, from_] if is_reversed else pair
                await cost_pair_api.CostPairApi().create(pair="".join(pair), cost=cost)
        return cost or 0, is_reversed

    @classmethod
    async def _parse_fees(cls, crypto: str):
        """
        Note:
            withdraw fees - комиссия за снятие
        """
        crypto = cls.NORMALIZE_COINS.get(crypto, crypto)
        data = await cls._get_fees()
        res = parser.parse(f"$[?(@.code='{crypto}')]").find(data)
        if len(res) != 0:
            value = res[0].value
            min_deposit = value["min_deposit"]["amount"]
            withdraw_fees = value["withdraw_fees"]
            fees_type = withdraw_fees[0]["type"]
            fees_amount = withdraw_fees[0]["asset"]["amount"]
            return decimal.Decimal(str(min_deposit)), fees_type, decimal.Decimal(str(fees_amount))
        else:
            logging.error(
                f"parse_fees_v2 return nothing! args: crypto={crypto}"
            )
            return 0, "fixed", 0

    @classmethod
    async def parse_fees_v2(cls, crypto: str):
        res = await fees_api.FeesApi().retrieve_fees(crypto)
        if res:
            min_deposit, fees_type, fees_amount = res
        else:
            min_deposit, fees_type, fees_amount = await cls._parse_fees(crypto)
            await fees_api.FeesApi().create(
                coin=crypto, data=dict(min_deposit=min_deposit, fees_type=fees_type, fees_amount=fees_amount)
            )
        return min_deposit, fees_type, fees_amount


if __name__ == '__main__':
    # asyncio.run(KunaApi.calculate_total_cost(KunaApi.BTC))
    # print(asyncio.run(KunaApi.get_payment_url("uah", 29000)))
    # print(asyncio.run(KunaApi.calculate_total_cost_v2("btc", "eth", decimal.Decimal(1), helpers.Constant.BUY)))

    async def test_parse_fees():
        inst = KunaApi()
        for el in inst.CRYPTO_KOINS:
            res = await inst.parse_fees_v2(el)
            print(res)


    """
    Test const coin pair cost
    """
    async def test_get_cost_coins_pair():
        # only in test db!
        # await cost_pair_api.CostPairApi().delete_(all_=True)
        # res = await cost_pair_api.CostPairApi()._get(all_=True)
        # assert res == []
        inst = KunaApi()
        expected_results = {}

        for key, val in inst.CONST_RELATIONS.items():
            if key in (inst.USDT_ERC20, inst.USDT_TRC20):
                key = inst.USDT
            for el in val:
                if el in (inst.USDT_ERC20, inst.USDT_TRC20):
                    el = inst.USDT
                pair = [key, el]
                key_ = f"{key}{el}"
                expected_res = await inst.get_cost_coins_pair(*pair)
                if not expected_res[0]:
                    print("i'm slip.")
                    await asyncio.sleep(60)
                    expected_res = await inst.get_cost_coins_pair(*pair)
                    if not expected_res[0]:
                        print("CRITICAL ERROR!")
                expected_results[key_] = expected_res

        for key, val in inst.CONST_RELATIONS.items():
            if key in (inst.USDT_ERC20, inst.USDT_TRC20):
                key = inst.USDT
            for el in val:
                if el in (inst.USDT_ERC20, inst.USDT_TRC20):
                    el = inst.USDT
                pair = [key, el]
                key_ = f"{key}{el}"
                value_from_get_cost_coins_pair = await inst.get_cost_coins_pair(*pair)
                if not value_from_get_cost_coins_pair[0]:
                    print("i'm slip.")
                    await asyncio.sleep(60)
                    value_from_get_cost_coins_pair = await inst.get_cost_coins_pair(*pair)
                    if not value_from_get_cost_coins_pair[0]:
                        print("CRITICAL ERROR!")
                try:
                    assert expected_results[key_] == value_from_get_cost_coins_pair
                except AssertionError as ex:
                    print(f"{expected_results[key_]}{value_from_get_cost_coins_pair}")
                    print(key_)
                    raise ex

    # asyncio.run(test_parse_fees())
