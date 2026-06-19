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
        channel = await tg_client.get_entity(int(os.environ["TARGET"]))
        channel2 = await tg_client.get_entity(int(os.environ["TARGET2"]))
        message_list = []
        async for msg in tg_client.iter_messages(channel, limit=None):
            if msg.text is not None and isinstance(msg.text, str):
                message_list.append(msg)
        message_list = sorted(message_list, key=lambda msg: int(msg.text))
        for i in range(0, len(message_list), 100):
            chunk = message_list[i : i + 100]
            logger.info(f"Processing {len(chunk)}...")
            await tg_client.forward_messages(channel2, chunk, drop_author=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except asyncio.CancelledError:
        pass
