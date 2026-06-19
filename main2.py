from telethon import TelegramClient
from telethon.sessions import StringSession
import os
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("telethon").setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)


async def main():
    global tg_client
    tg_client = TelegramClient(
        StringSession(os.environ["TOKEN"]),
        int(os.environ["API_ID"]),
        os.environ["API_HASH"],
        request_retries=2,
    )
    async with tg_client:
        channel = await tg_client.get_entity(os.environ["TARGET"])
        channel2 = await tg_client.get_entity(os.environ["TARGET2"])
        message_list = await tg_client.iter_messages(channel, limit=None)
        message_list = sorted(message_list, key=lambda msg: int(msg.text))
        await tg_client.forward_messages(channel2, message_list)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except asyncio.CancelledError:
        pass
