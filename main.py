from telethon import TelegramClient
from telethon.sessions import StringSession
import os
import asyncio
import logging
import boto3
import time

START = time.time()

sem = None

tg_client = None

bucket = boto3.resource(
    "s3",
    aws_access_key_id=os.environ["ACCESS_ID"],
    aws_secret_access_key=os.environ["ACCESS_SECRET"],
    endpoint_url=os.environ["ENDPOINT_URL"],
    region_name="",
).Bucket("test")

async def reset_semaphore(t):
    await asyncio.sleep(t)
    for _ in range(5):
        await sem.acquire()
    os.exit(0)

async def upload_oss_file_to_tg(chat, oss_file_path):
    async with sem:
        file_name = os.path.basename(oss_file_path)
        try:
            bucket.download_file(oss_file_path, f"/tmp/{oss_file_path}")
    
            await tg_client.send_file(
                entity=chat,
                file=f"/tmp/{oss_file_path}",
                caption=file_name,
                force_document=False,
                supports_streaming=True,
                file_name=file_name,
            )
    
            bucket.Object(oss_file_path).delete()
            os.remove(f"/tmp/{oss_file_path}")
            return
    
        except Exception as e:
            logging.exception(e)


async def scan_oss_folder_and_upload():
    channel = await tg_client.get_entity(int(os.environ["TARGET"]))
    
    tasks = [upload_oss_file_to_tg(channel, file_obj.key) for file_obj in bucket.objects.all()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for file_obj in bucket.objects.all():
        if time.time() - START > 4 * 60 * 60:
            return
        await upload_oss_file_to_tg(channel, file_obj.key)
        
    os.exit(-1)


async def main():
    async with tg_client:
        await scan_oss_folder_and_upload()


if __name__ == "__main__":
    while time.time() - START < 4 * 60 * 60:
        try:
            sem = asyncio.Semaphore(5)
            timeout_task  = asyncio.create_task(reset_semaphore(START + 4 * 60 * 60 - time.time()))
            tg_client = TelegramClient(
                StringSession(os.environ["TOKEN"]),
                int(os.environ["API_ID"]),
                os.environ["API_HASH"],
            )
            asyncio.run(main())
        except:
                timeout_task.cancel()
                try:
                    await timeout_task
                except asyncio.CancelledError:
                    pass
