from contextlib import contextmanager

from telethon import TelegramClient
from telethon.sessions import StringSession
import os
import asyncio
import logging
import boto3
import time
import pymysql
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("telethon").setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)

tg_client = None

bucket = boto3.resource(
    "s3",
    aws_access_key_id=os.environ["RCLONE_CONFIG_R2_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["RCLONE_CONFIG_R2_SECRET_ACCESS_KEY"],
    endpoint_url=os.environ["RCLONE_CONFIG_R2_ENDPOINT"],
    region_name="",
).Bucket(os.environ["RCLONE_CONFIG_R2_BUCKET"])


async def main():
    async with tg_client:
        delete_objects = []
        channel = await tg_client.get_entity(int(os.environ["TARGET"]))
        async for msg in tg_client.iter_messages(channel, limit=None):
            if msg.text is not None and isinstance(msg.text, str):
                text = msg.text.strip()
                logger.debug("Deleting %s...", text)
                delete_objects.append({"Key": text})
        for i in range(0, len(delete_objects), 1000):
            chunk = delete_objects[i : i + 1000]
            bucket.delete_objects(
                Delete={
                    "Objects": chunk,
                    "Quiet": True,
                }
            )
            logger.info(f"Deleted {len(chunk)} items")


if __name__ == "__main__":
    tg_client = TelegramClient(
        StringSession(os.environ["TOKEN"]),
        int(os.environ["API_ID"]),
        os.environ["API_HASH"],
    )
    asyncio.run(main())
