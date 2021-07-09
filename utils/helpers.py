from urllib.parse import urlparse, parse_qs
from typing import Union, Optional

from aiogram import types, Bot
from aiogram.dispatcher import FSMContext

from utils import api, buttons


def format_delta(delta):
    d = {"days": delta.days}
    d["hours"], rem = divmod(delta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return "{days} Дней {hours}:{minutes}:{seconds}".format(**d)


async def message_delete_processing(bot, message, state, state_data, ms_text):

    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    if state_data.get("_last_bot_message"):
        await bot.edit_message_text(
            ms_text,
            chat_id=message.chat.id,
            message_id=state_data.get("_last_bot_message")
        )
    else:
        ms = await bot.send_message(message.chat.id, ms_text)
        await state.update_data(_last_bot_message=ms.message_id)


def parse_query(query) -> (str, str):
    query_ = urlparse(query)
    return query_.path, parse_qs(query_.query)


def get_val_query(query) -> Union[str, int]:
    path, data = parse_query(query)
    assert len(data.keys()) == 1
    return list(data.values())[0][0]


def state_machine_handler(
        expected_keys: set,
        state_data: dict,
        ignore_keys: Optional[set] = None,
) -> bool:
    _state_data = state_data.copy()
    default_ignore_keys = {"_last_bot_message", "_message_id", "_order_id", "cost_fiat"}
    _state_data_keys = _state_data.keys()
    if ignore_keys:
        [default_ignore_keys.add(val) for val in ignore_keys]
    [_state_data.pop(key) for key in default_ignore_keys if key in _state_data_keys]
    return _state_data_keys == expected_keys and all(_state_data.values())


class Constant:
    BUY = "buy_event"
    SELL = "sell_event"

    BTC = "btc"
    ETH = "eth"
    LTC = "ltc"
    XRP = "xrp"
    TRX = "trx"
    USDT = "usdt"

    UAH = "uah"
    RUB = "rub"
    USD = "usd"

    @classmethod
    def get_exchange_type_descriptor(
            cls,
            val: str,
            lower_: bool = True,
            verb: bool = True
    ) -> str:
        res = ""
        if val == cls.BUY:
            res = "Купить" if verb else "Покупка"
        elif val == cls.SELL:
            res = "Продать" if verb else "Продажа"
        return res.lower() if lower_ else res


class BaseHandler(Constant):
    CALL_BACK_QUERY = "CALL_BACK_QUERY"
    MESSAGE = "MESSAGE"

    TEXT = ""
    BUTTONS = None
    # BACK_BTN = ""

    def __init__(
            self,
            bot: Bot,
            msg_query,
            state: FSMContext,
            state_data: dict,
            msg_data: Optional[str] = None,
            query_path: Optional[str] = None,
            data_query: Optional[str] = None
    ):
        self.bot = bot
        self.msg_query = msg_query
        self.state_data = state_data
        self.__fill_self(msg_query)
        self.state = state
        if state_data:
            for key, val in state_data.items():
                setattr(self, key, val)
        # msg query or msg test
        self.msg_data = msg_data
        self.query_path = query_path
        self.data_query = data_query

        self.text = ""
        self.btns = None

    def __fill_self(self, msg_query):
        # do better
        if isinstance(msg_query, types.CallbackQuery):
            self.msg_type = self.CALL_BACK_QUERY
            self.chat_id = msg_query.message.chat.id
            self.msg_id = msg_query.message.message_id
            self.msg_date = msg_query.message.date
        elif isinstance(msg_query, types.Message):
            self.msg_type = self.MESSAGE
            self.chat_id = msg_query.chat.id
            self.msg_id = msg_query.message_id
            self.msg_date = msg_query.values["date"]
        self.msg_user_id = msg_query.from_user.id

    async def handler(self, *args, **kwargs):
        raise NotImplemented

    async def edit_msg_or_send(self):
        if self.msg_type == self.CALL_BACK_QUERY:
            await self.edit_msg()
        else:
            await self.send_msg()

    async def edit_msg(self, msg_id: int = None):
        await self.bot.edit_message_text(
            chat_id=self.chat_id,
            message_id=msg_id or self.msg_id,
            text=self.text or self.TEXT,
            reply_markup=self.BUTTONS,
            parse_mode=types.ParseMode.HTML
        )

    async def send_msg(self):
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=self.text or self.TEXT,
            parse_mode=types.ParseMode.HTML,
            reply_markup=self.BUTTONS
        )

    async def delete_msg_update_state_last_bot_message(self):
        await self.bot.delete_message(chat_id=self.chat_id, message_id=self.msg_id)
        await self.update_state_data(_last_bot_message=None)

    async def message_delete_processing(self):
        await self.bot.delete_message(chat_id=self.chat_id, message_id=self.msg_id)
        if hasattr(self, "_last_bot_message") and getattr(self, "_last_bot_message"):
            await self.bot.edit_message_text(
                self.TEXT,
                chat_id=self.chat_id,
                message_id=self._last_bot_message
            )
        else:
            ms = await self.bot.send_message(self.chat_id, self.TEXT)
            await self.update_state_data(_last_bot_message=ms.message_id)

    def format_msg_text(self, *args, **kwargs):
        self.text = self.TEXT.format(**kwargs)

    async def update_state_data(self, **kwargs):
        await self.state.update_data(**kwargs)
        for key, val in kwargs.items():
            self.state_data.update({key: val})
            setattr(self, key, val)

    def event(self, lower_: bool = True, verb: bool = True):
        event = self.exchange_type if hasattr(self, "exchange_type") else self.data_query
        return self.get_exchange_type_descriptor(event, lower_, verb)

    @property
    async def _total_cost(self):
        return await api.KunaApi().calculate_total_cost_v2(
            self.crypto, self.fiat, self.quantity, self.exchange_type
        )

    @property
    def payment_type_optional_msg(self):
        return buttons.PaymentType.DESCRIPTOR_VALUE.get(
            self.payment_type) if Constant.SELL else "номер кошелька"

    @property
    def validator(self):
        if self.exchange_type == self.SELL:
            return buttons.PaymentType.VALIDATORS.get(self.payment_type)
        else:
            return buttons.PaymentType.VALIDATORS.get(buttons.PaymentType.BILL)


