import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from config import TOKEN
from indicatorManager import get_indicator

triger_RSI_5m = 55
triger_RSI_30m = 65
triger_CCI_60m = 85

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"👋 Привет, {html.bold(message.from_user.full_name)}!\nВ этот чат будут отправляться сигналы с рекомендацией покупки 🟡 XAU₮, которые основаны на RSI и CCI показателях.")        

@dp.message(Command('signal'))
async def get_signal_handler(message: Message) -> None:
    while True:
        signal_data = get_indicator()

        symbol = signal_data.get('Symbol')
        rsi_5m = signal_data.get('RSI_5m')
        rsi_30m = signal_data.get('RSI_30m')
        cci_60m = signal_data.get('CCI_60m')

        # Checking all signal conditions
        if rsi_5m < triger_RSI_5m and rsi_30m < triger_RSI_30m and cci_60m < triger_CCI_60m:
            # Signal detected, send message
            await message.answer(
                f"🚀 Рекомендуется покупка\n\n🟡 {symbol}\n\nRSI 5 минут: {rsi_5m}\nRSI 30 минут: {rsi_30m}\nCCI 60 минут: {cci_60m}"
            )

        await asyncio.sleep(60)  # Waiting for next check in seconds

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())