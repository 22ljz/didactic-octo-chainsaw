import time

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
# logging.getLogger("telethon").setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


async def main():
    try:
        await asyncio.wait_for(task(), timeout=5 * 60 * 60)
    except asyncio.TimeoutError:
        pass


async def task():
    global tg_client
    tg_client = TelegramClient(
        StringSession(os.environ["TOKEN"]),
        int(os.environ["API_ID"]),
        os.environ["API_HASH"],
        request_retries=10,
        flood_sleep_threshold=float("inf"),
    )
    async with tg_client:
        cnt = 0
        start_time = time.time()
        channel2 = await tg_client.get_entity(int(os.environ["TARGET2"]))
        async for msg in tg_client.iter_messages(channel2, limit=None):
            if msg.text and isinstance(msg.text, str):
                await msg.edit(text="")
                cnt += 1
                if cnt > 10:
                    sleep_time = clamp(1 - (time.time() - start_time), 0.1, 1)
                    logger.info(f"Processing 10 (sleep {sleep_time:.1f}s)...")
                    await asyncio.sleep(sleep_time)
                    cnt = 0
                    start_time = time.time()
    exit(-1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(e)
        raise e
    except asyncio.CancelledError:
        pass
