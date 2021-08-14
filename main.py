import logging
import datetime
import decimal

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.redis import RedisStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import exceptions as aiogram_ex

from config import T_TOKEN, T_EXPIRE, REDIS_HOST, DEBUG
from utils import helpers, buttons, validators, exceptions as exep, api, helper_send_email
from db.db_api import (
    user_api,
    order_api,
    admin_api,
    e_wallet_api,
)

if DEBUG:
    logging.basicConfig(level=logging.INFO, filename="logs.txt")
else:
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%d-%m-%Y:%H:%M:%S',
        level=logging.INFO,
        filename='logs.txt'
    )
bot = Bot(token=T_TOKEN)
storage = RedisStorage(host=REDIS_HOST)
dp = Dispatcher(bot, storage=storage)


class ExchangeStorage(StatesGroup):
    BUY = "buy_event"
    SELL = "sell_event"

    exchange_type = State()
    crypto = State()
    fiat = State()
    payment_type = State()
    quantity = State()
    bill = State()
    memo = State()
    _message_id = State()
    _last_bot_message = State()
    _order_id = State()
    _payment_url = State()
    cost_fiat = State()
    email = State()


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


@dp.message_handler(commands=['start'], state="*")
async def process_start_command(message: types.Message, state):
    # write user in ti db
    await user_api.UserAPI.create_user_if_necessary(
        chat_id=message.chat.id,
        language=message.from_user.language_code,
        username=message.from_user.username
    )
    await state.finish()
    text = """
<strong>Вас приветствует сервис для обмена валюты - Plus bot!</strong>
Обмен производится мгновенно в автоматическом режиме. 
Время обмена зависит от выбранной валюты , количества подтверждений и загруженности сети.
        """
    await bot.send_message(
        chat_id=message.from_user.id,
        text=text,
        reply_markup=buttons.StartScreen.buttons,
        parse_mode=types.ParseMode.HTML
    )


@dp.message_handler(lambda message: message.text, state="*")
async def message_router(message, state):
    _value_handler0_keys = {"crypto", "exchange_type", "fiat", "payment_type"}
    _value_handler_0_1_keys = {"crypto", "exchange_type", "fiat", "payment_type", "quantity"}
    _value_handler1_keys = {"crypto", "exchange_type", "fiat", "payment_type", "quantity", "bill"}
    _value_handler2_keys = {
        "crypto", "exchange_type", "fiat", "payment_type", "quantity", "bill", "total_cost"
    }

    state_data = await state.get_data()
    msg_text = message.text

    async def processing(cls_):
        inst = cls_(bot, message, state, state_data, msg_text, data_query=msg_text)
        return await inst.handler()

    if msg_text in ["🔄 Новый обмен"]:
        # return select buy or sale event
        return await processing(NewExchange)

    elif msg_text in ["ℹ️ Поддержка"]:
        return await processing(ProcessSupport)

    elif msg_text in ["ℹ️ Информация"]:
        return await processing(ProcessInfo)

    elif msg_text in ["💎 Мои обмены"]:
        return await processing(ProcessExchangeHistory)

    elif msg_text in ["🗣 Язык"]:
        return await processing(ProcessLanguages)

    elif helpers.state_machine_handler(_value_handler0_keys, state_data):
        # accepting bill
        return await processing(ExchangeValueHandler)

    elif helpers.state_machine_handler(_value_handler_0_1_keys, state_data):
        return await processing(ExchangeValueHandler01)

    elif helpers.state_machine_handler(_value_handler1_keys, state_data):
        # accepting email
        return await processing(ExchangeValueHandler1)

    elif helpers.state_machine_handler(_value_handler2_keys, state_data):
        # await state.reset_data("quantity")
        return await processing(ExchangeValueHandler2)

    else:
        await bot.send_message(message.from_user.id, text="Извините, я вас не понимаю.")


@dp.callback_query_handler(lambda query: query.data, state="*")
async def query_router(query, state):
    state_data = await state.get_data()
    msg_query = query.data
    query_path, data_query = helpers.parse_query(msg_query)
    query_value = data_query.get("value", [None])[0]

    async def processing(cls_):
        inst = cls_(bot, query, state, state_data, msg_query, query_path, query_value)
        return await inst.handler()

    if query_path in ["new_exchange"]:
        # return select buy or sale event
        return await processing(NewExchange)

    elif query_path in ["event", "exchange_step1"]:
        # return select crypto
        return await processing(Exchange1Step)

    elif query_path in ["crypto", "exchange_step2"]:
        # return select fiat
        # it was exchange_step
        return await processing(Exchange2Step)

    elif query_path in ["fiat", "exchange_step3"]:
        # return select payment type
        return await processing(ExchangeSelectPaymentStep)

    elif query_path in ["exchange_step3_4"]:
        state_data.pop("bill")
        await state.set_data(state_data)
        return await processing(Exchange34Step)

    elif query_path in ["payment_type", "exchange_step4"]:
        # return input email
        if "quantity" in state_data.keys():
            state_data.pop("quantity")
            await state.set_data(state_data)
        return await processing(Exchange3Step)

    elif query_path in ["exchange_step5"]:
        return await processing(Exchange5Step)

    elif query_path in ["admin_approve"]:
        await admin_success_order(query, state)

    else:
        await bot.send_message(query.message.chat.id, text="Извините, я вас не понимаю.")


class ProcessSupport(helpers.BaseHandler):

    TEXT = """
ℹ️ Поддержка

Если у Вас возникли вопросы по обмену, свяжитесь с нашим оператором @DanilPsol.
Если желаете обсудить индивидуальные условия, просьба написать нам на почту xplus_crypto@protonmail.com
    """

    async def handler(self, *args, **kwargs):
        await self.send_msg()


class ProcessInfo(helpers.BaseHandler):
    TEXT = """
Plus bot - бот для быстрого, безопасного и анонимного обмена криптовалюты на валюту Вашей страны, либо на другую криптовалюту. Самые низкие комиссии и актуальный курс по криптовалютным парам.  Поддержка в реальном режиме 24/7!
    """

    async def handler(self, *args, **kwargs):
        await self.send_msg()


class ProcessLanguages(helpers.BaseHandler):

    TEXT = """
🗣 Язык

Раздел находится в процессе разработки.
    """

    async def handler(self, *args, **kwargs):
        await self.send_msg()


class ProcessExchangeHistory(helpers.BaseHandler):
    TEXT = """
💎 Мои обмены

Раздел находится в процессе разработки.
        """

    async def handler(self, *args, **kwargs):
        await self.send_msg()


class NewExchange(helpers.BaseHandler):
    TEXT = """ 
🔄 Новый обмен

Внимание!
Вне зависимости от того, в какую сторону будет изменен курс обмена, его окончательная фиксация будет произведена в момент фактического зачисления средств на наш кошелек.
"""
    BUTTONS = buttons.MyExchangeStep1.buttons

    async def handler(self, *args, **kwargs):
        if hasattr(self, "_message_id") and not isinstance(self.msg_query, types.CallbackQuery):
            await self.delete_msg_update_state_last_bot_message(self._message_id)
        await self.state.finish()
        await ExchangeStorage.exchange_type.set()
        await self.edit_msg_or_send()


class Exchange1Step(helpers.BaseHandler):
    TEXT = """
🔄 Новый обмен

Что хочешь {event}?
    """
    BUTTONS = buttons.Crypto.get_all_crypto_btn()

    async def handler(self, *args, **kwargs):
        if self.query_path == "exchange_step1":
            assert self.exchange_type
        else:
            await self.update_state_data(exchange_type=self.data_query)
        self.format_msg_text(event=self.event())
        await self.edit_msg()


class Exchange2Step(helpers.BaseHandler):
    TEXT = """
🔄 Новый обмен

За какую валюту ты хочешь {event} {crypto}?
"""

    async def handler(self, *args, **kwargs):
        if self.query_path == "exchange_step2":
            if self.state_data.get("quantity"):
                await self.reset_state_data("quantity")
        else:
            await self.update_state_data(crypto=self.data_query)
        self.BUTTONS = buttons.Fiat.get_button_separate_coin(self.crypto)
        self.format_msg_text(event=self.event(), crypto=self.crypto.upper())
        await self.edit_msg()


class ExchangeSelectPaymentStep(helpers.BaseHandler):
    TEXT = f"""
🔄 Новый обмен

Выберите способ оплаты.
            """

    async def handler(self, *args, **kwargs):
        if not self.query_path == "exchange_step3":
            await self.update_state_data(fiat=self.data_query)
        await self.update_state_data(_message_id=self.msg_id)
        if self.exchange_type == self.SELL and self.fiat in (self.UAH, self.RUB):
            self.BUTTONS = buttons.PaymentType().get_payment_type_buttons(
                self.query_path, self.fiat, self.exchange_type
            )
            await self.edit_msg()
        else:
            # await self.update_state_data()
            data_query = buttons.PaymentType.BILL if self.fiat not in self.FIAT else buttons.PaymentType.VISA_KEY
            inst = Exchange3Step(
                bot=self.bot,
                msg_query=self.msg_query,
                state=self.state,
                state_data=self.state_data,
                data_query=data_query
            )
            return await inst.handler()


class Exchange3Step(helpers.BaseHandler):
    TEXT = """
🔄 Новый обмен

Введите количесвто {crypto} которое хотите {event}
    """
    BUTTONS = buttons.exchange_step_2()

    async def handler(self, *args, **kwargs):
        if not self.query_path == "exchange_step4":
            await self.update_state_data(payment_type=self.data_query)
        self.format_msg_text(crypto=self.crypto.upper(), event=self.event())
        await self.update_state_data(_message_id=self.msg_id)
        await self.edit_msg()


class Exchange34Step(helpers.BaseHandler):
    TEXT = """
🔄 Новый обмен

<b>{event}:</b> {crypto} за {fiat}
<b>Способ оплаты:</b> {payment_rus_descr}
<b>Количесвто {crypto}:</b> {quantity}
<b>Стоимость:</b> {total_cost} {fiat}

<strong>Введите {optional_msg} куда хотите получить оплату</strong>
    """
    BUTTONS = buttons.exchange_step_3()

    async def handler(self, *args, **kwargs):
        self.format_msg_text(
            event=self.event(False, False), crypto=self.crypto.upper(),
            fiat=self.fiat.upper(), optional_msg_up=self.payment_type_optional_msg.upper(),
            quantity=self.quantity, total_cost=await self._total_cost,
            optional_msg=self.payment_type_optional_msg, payment_rus_descr=self.payment_rus_descr()
        )
        await self.edit_msg()


class ExchangeValueHandler(helpers.BaseHandler):

    async def handler(self, *args, **kwargs):
        quantity = self.msg_data.replace(",", ".")
        min_deposit, _, _ = await api.KunaApi().parse_fees_v2(self.crypto)
        try:
            quantity = decimal.Decimal(quantity)
            if quantity < min_deposit:
                raise exep.MinDepositValueEx()
        except (decimal.InvalidOperation, exep.MinDepositValueEx) as ex:
            self.TEXT = f"{self.msg_data} - невалидное количесвто {self.crypto}!"
            if isinstance(ex, exep.MinDepositValueEx):
                self.TEXT = self.TEXT + f" Минимальное кол-во {min_deposit}"
            await self.message_delete_processing()
        else:
            if hasattr(self, "_last_bot_message") and getattr(self, "_last_bot_message"):
                await bot.delete_message(chat_id=self.chat_id, message_id=self._last_bot_message)
            await self.update_state_data(quantity=quantity)
            await self.delete_msg_update_state_last_bot_message()
            inst = Exchange34Step(bot, self.msg_query, self.state, self.state_data, self.data_query)
            inst.msg_id = self.state_data.get("_message_id") or self.msg_id
            await inst.handler()


class ExchangeValueHandler01(helpers.BaseHandler):

    async def handler(self, *args, **kwargs):
        if not self.validator(self.msg_data):
            self.TEXT = f"Невалидный {self.payment_type_optional_msg}. '{self.msg_data}' - невалидное значениие!"
            return await self.message_delete_processing()
        await self.update_state_data(bill=self.msg_data)
        if (self.exchange_type == self.BUY and self.crypto in self.MEMO_COINS) or (
                self.exchange_type == self.SELL and self.fiat in self.MEMO_COINS):
            self.TEXT = """
🔄 Новый обмен

Для {coin} необходимо ввести MEMO.
            """
            coin = self.fiat if self.fiat in self.MEMO_COINS else self.crypto
            self.format_msg_text(coin=coin.upper())
            await bot.delete_message(chat_id=self.chat_id, message_id=self.msg_id)
            await self.edit_msg(self._message_id, save=False)
            if hasattr(self, "last_bot_message"):
                await bot.delete_message(chat_id=self.chat_id, message_id=self.last_bot_message)
        else:
            await self.update_state_data(memo=None)
            # bot, message, state, state_data, msg_text, data_query=msg_text
            inst = ExchangeValueHandler1(
                self.bot,
                self.msg_query,
                self.state,
                self.state_data,
                self.msg_data,
                data_query=self.data_query
            )
            return await inst.handler()


class ExchangeValueHandler1(helpers.BaseHandler):

    TEXT = """
🔄 Новый обмен

<strong>Проверьте правильность введенных данных:</strong>

<b>Заявка:</b> №-{order_id}
<b>{exchange_event}:</b> {crypto} за {fiat}
<b>Способ оплаты:</b> {payment_rus_descr}
<b>Время:</b> {msg_date}
<b>Количесвто {crypto}:</b> {quantity}
<b>Стоимость:</b> {total_cost} {fiat}
<b>{payment_type_optional_msg_cap}:</b> {msg}
{optional_msg_memo}

{optional_msg}

По факту совершения оплаты нажмите на кнопку - "Оплачено".
Время ожидание оплаты - {expire} мин., в случае отсутствия перевода
заявка аннулируется!

Заявка будет активна до {active_to}.
Для получения реквизитов на почту - введте почту.
         """

    async def handler(self, *args, **kwargs):
        if not hasattr(self, "memo"):
            if not validators.memo_validator(self.msg_data):
                self.TEXT = f"Невалидный MEMO. '{self.msg_data}' - невалидное значениие!"
                return await self.message_delete_processing()
            else:
                await self.update_state_data(memo=self.msg_data)
        total_cost = await self._total_cost
        await self.update_state_data(cost_fiat=str(total_cost))
        await self.update_state_data(total_cost=total_cost)
        order_data = {k: v for k, v in self.state_data.items() if k not in (
            "_message_id", "_last_bot_message", "_order_id", "total_cost", "_payment_url"
        )}
        order_data["cost_fiat"] = order_data.pop("cost_fiat")
        order_id = await order_api.OrderAPI().create_order({**order_data, **{"user_id": self.msg_user_id}})
        await self.update_state_data(_order_id=order_id)
        payment_url = None
        if self.fiat in [self.USD, self.RUB, self.UAH] and self.exchange_type == self.BUY:
            payment_url = await api.KunaApi().get_payment_url(self.fiat, float(total_cost))
            await self.update_state_data(_payment_url=payment_url)
            optional_msg = """
Сумма для оплаты привышает лимит автоматической оплаты. 
Ваша заявка будет обрабатываться в индивидуальном порядке.""" if not payment_url else ""
        else:
            e_wallet = await e_wallet_api.EWalletsApi().get(
                self.crypto if self.exchange_type == self.SELL else self.fiat
            )
            optional_msg = f"<b>Номер кошелька:</b> {e_wallet.wallet}"
            if e_wallet.memo:
                optional_msg = optional_msg + f"\n<b>MEMO:</b> {e_wallet.memo}"
        optional_msg_memo = None
        if hasattr(self, "memo") and getattr(self, "memo") is not None:
            optional_msg_memo = f"<b>MEMO:</b> {self.memo}"
        self.BUTTONS = buttons.exchange_step_3_4(order_id, payment_url)
        self.format_msg_text(
            order_id=order_id, exchange_event=self.event(False, False), fiat=self.fiat.upper(),
            crypto=self.crypto.upper(),
            payment_type_optional_msg=buttons.PaymentType._collections.get(self.payment_type, [])[0],
            msg_date=self.msg_date, quantity=self.quantity,
            payment_type_optional_msg_cap=self.payment_type_optional_msg.capitalize(),
            msg=self.bill, total_cost=total_cost, optional_msg=optional_msg,
            expire=T_EXPIRE, active_to=str(self.msg_date + datetime.timedelta(minutes=T_EXPIRE)),
            payment_rus_descr=self.payment_rus_descr(), optional_msg_memo=optional_msg_memo or ""
        )
        await bot.delete_message(chat_id=self.chat_id, message_id=self.msg_id)
        await self.edit_msg(self._message_id, save=False)
        if hasattr(self, "last_bot_message"):
            await bot.delete_message(chat_id=self.chat_id, message_id=self.last_bot_message)


class ExchangeValueHandler2(helpers.BaseHandler):

    async def handler(self, *args, **kwargs):
        if not validators.email_validator(self.msg_data):
            self.TEXT = f"{self.msg_data} - невалидный почтовый адресс!"
            return await self.message_delete_processing()
        await self.update_state_data(email=self.msg_data)
        if hasattr(self, "email") and getattr(self, "email"):
            if self.email == self.msg_data:
                self.TEXT = f"Письмо на почту '{self.msg_data} уже было высланно ранее.'"
                await self.message_delete_processing()
        self.TEXT = f"На вашу почту '{self.msg_data} отправленны реквизиты.'"
        await self.send_msg()
        if hasattr(self, "_last_bot_message") and getattr(self, "_last_bot_message"):
            await bot.delete_message(chat_id=self.chat_id, message_id=self._last_bot_message)
            await self.update_state_data(_last_bot_message=None)
        # send email
        exchange_event = self.event(False, False)
        payment_url = payment_msg = wallet = memo = None
        if hasattr(self, "_payment_url"):
            if getattr(self, "_payment_url") is not None:
                payment_url = self._payment_url
            else:
                payment_msg = """
                    Сумма для оплаты привышает лимит автоматической оплаты. 
                    Ваша заявка будет обрабатываться в индивидуальном порядке.
                    """
        else:
            e_wallet = await e_wallet_api.EWalletsApi().get(
                self.crypto if self.exchange_type == self.SELL else self.fiat
            )
            wallet = e_wallet.wallet
            memo = e_wallet.memo
        substitutions = dict(
            order_id=self._order_id,
            fiat=self.fiat.upper(),
            exchange_event=exchange_event,
            crypto=self.crypto.upper(),
            payment_type_optional_msg=buttons.PaymentType._collections.get(self.payment_type, [])[0],
            quantity=self.quantity,
            payment_type_optional_msg_cap=self.payment_type_optional_msg.capitalize(),
            total_cost=self.cost_fiat,
            optional_msg_memo=self.memo if hasattr(self, "memo") and getattr(self, "memo") else '',
            payment_rus_descr=self.payment_rus_descr(),
            bill=self.bill,
            payment_url=payment_url,
            memo=memo,
            payment_msg=payment_msg,
            wallet=wallet,
        )
        html_contents = helpers.render_payment_details_template(substitutions)
        contents = {"html": (html_contents, "html")}
        msg = helper_send_email.setup_email_contents(
            [self.msg_data], "Official_Plus_bot", contents
        )
        async with helper_send_email.EmailAPI() as send_email:
            res = await send_email(msg)


async def admin_msg_telegram_new_order_approved(order_id: str, order_is_expired, time_expired):
    order_data = await order_api.OrderAPI().retrieve(int(order_id))
    user_data = await user_api.UserAPI().retrieve(order_data.user_id)
    exchange_event = helpers.Constant().get_exchange_type_descriptor(order_data.exchange_type, False, False)
    admins = await admin_api.AdminApi().get_admin()
    text = f"""
<b>Заявка:</b> №-{order_id}
<b>{exchange_event.capitalize()}:</b> {order_data.crypto.upper()} за {order_data.fiat.upper()}
<b>Способ оплаты:</b> {buttons.PaymentType._collections.get(order_data.payment_type, [])[0]}
<b>Время:</b> {order_data.cr_date.strftime("%Y-%m-%d %H:%M:%S")}
<b>Количесвто {order_data.crypto.upper()}:</b> {order_data.quantity}
<b>Стоимость:</b> {order_data.cost_fiat} {order_data.fiat.upper()}
<b>Оплата просрочена:</b> {order_is_expired} {time_expired or ''}
<b>{order_data.payment_type.upper()}:</b> {order_data.bill}
{f'<b>MEMO:</b> {order_data.memo}' if order_data.memo else ''}

<strong>Пользователь</strong>
<b>Дата регистрации:</b> {user_data.registration_date.strftime("%Y-%m-%d %H:%M:%S")}
<b>Язык:</b> {user_data.language.upper() if user_data.language else 'None'}
<b>Username:</b> @{user_data.username}
    """
    for data in admins:
        # send telegram message 1
        # send email message
        # data.email
        btn = buttons.Admin().order_request(order_id)
        try:
            await bot.send_message(
                chat_id=data.chat_id,
                text=text,
                reply_markup=btn,
                parse_mode=types.ParseMode.HTML
            )
        except aiogram_ex.ChatNotFound:
            continue


class Exchange5Step(helpers.BaseHandler):

    async def handler(self, *args, **kwargs):
        order_is_expired, order, expired_time = await order_api.OrderAPI().checking_expiration(self.data_query)
        await admin_msg_telegram_new_order_approved(self.data_query, order_is_expired, expired_time)
        # set order approved
        # send message from admin
        # todo: implement send message from admin hear
        await order_api.OrderAPI().set_approve(int(self.data_query))
        if not order_is_expired:
            self.TEXT = """
<strong>Ваша заявка обрабатывается ⌛</strong>
<b>Заявка:</b> №-{order_id}
Больше Вам не нужно ничего делать, после 
подтверждения платежа статус обновится автоматически.

Время ожидания зависит от загруженности сети.
При возникновении вопросов по Вашей заявке
просьба обратится в нашу службу поддержки.

<strong>Спасибо что выбрали наш сервис!</strong>
            """
            self.format_msg_text(order_id=self.data_query)
        else:
            self.TEXT = """
<strong>{expire} минут с момента создания вашей заявки истекли 😕</strong>
<b>Заявка:</b> №-{order_id}
В случае если Вы произвели оплату, но срок заявки истек - обратитесь
в нашу службу поддержки нажав на кнопку "ℹ️ Поддержка".

<strong>Спасибо что выбрали наш сервис!</strong>
            """
            self.format_msg_text(expire=T_EXPIRE, order_id=self.data_query)
        await self.edit_msg(save=False)


async def admin_success_order(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = helpers.get_val_query(callback_query.data)
    order_data = await order_api.OrderAPI().retrieve(int(order_id))
    if order_data.approve:
        return

    exchange_type_descr = helpers.Constant().get_exchange_type_descriptor(order_data.exchange_type, verb=False)
    payment_type_descr = buttons.PaymentType.DESCRIPTOR_VALUE.get(
            order_data.payment_type if order_data.exchange_type == helpers.Constant.SELL else buttons.PaymentType.BILL)
    text = f"""
<strong>Обмен успешно выполнен!</strong>
<b>Заявка</b> №-{order_id} обработана, ожидайте зачисление средств на Ваш счет.

<b>{exchange_type_descr}:</b> {order_data.crypto.upper()} за {order_data.fiat.upper()}
<b>Способ оплаты:</b> {order_data.payment_type}
<b>Время:</b> {callback_query.message.date.strftime("%Y-%m-%d %H:%M:%S")}
<b>Количесвто {order_data.crypto.upper()}:</b> {order_data.quantity}
<b>{payment_type_descr.capitalize()}:</b> {order_data.bill}
<b>Стоимость:</b> {order_data.cost_fiat} {order_data.fiat.upper()}
    """
    await order_api.OrderAPI().set_success(int(order_id))
    await bot.send_message(
        chat_id=order_data.user_id,
        text=text,
        parse_mode=types.ParseMode.HTML
    )
    await order_api.OrderAPI().update(data={"approve": True}, pk=int(order_id))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_shutdown=shutdown)
