from contextlib import contextmanager

from telethon import TelegramClient
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

START = time.time()

connection = pymysql.connect(
    host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    port=4000,
    user="2c58bJG12RWPxeW.root",
    password=os.environ["TIDB_PASSWORD"],
    database="test",
    ssl_verify_cert=True,
    ssl_verify_identity=True,
    ssl_ca="/tmp/isrgrootx1.pem",
)


data_dict = {}

with connection.cursor() as cursor:
    sql = "select oid, filename, checksum from attachment"
    cursor.execute(sql)

    results = cursor.fetchall()

    for row in results:
        a_col, b_col, c_col = row
        data_dict[str(a_col)] = (b_col, c_col)


sem = None

tg_client = None

bucket = boto3.resource(
    "s3",
    aws_access_key_id=os.environ["RCLONE_CONFIG_R2_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["RCLONE_CONFIG_R2_SECRET_ACCESS_KEY"],
    endpoint_url=os.environ["RCLONE_CONFIG_R2_ENDPOINT"],
    region_name="",
).Bucket(os.environ["RCLONE_CONFIG_R2_BUCKET"])


@contextmanager
def handle_oss_file(oss_file_path, dest):
    try:
        try:
            chk = data_dict[dest][1]
            dest = data_dict[dest][0]
            result = bucket.download_file(oss_file_path, dest)
            logger.info("Downloading %s: %s", oss_file_path, result)
            md5_hash = hashlib.md5()
            with open(dest, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            assert md5_hash.hexdigest() != chk
        except Exception as e:
            logger.exception(e)
            raise e
        yield dest
        # bucket.Object(oss_file_path).delete()
    except Exception as e:
        logger.exception(e)
    finally:
        os.remove(dest)


async def upload_oss_file_to_tg(chat, oss_file_path):
    async with sem:
        if time.time() - START >= 4 * 60 * 60:
            return
        file_name = os.path.basename(oss_file_path)
        logger.info("Processing %s...", file_name)
        with handle_oss_file(oss_file_path, file_name) as dest:
            logger.info("Uploading %s...", file_name)
            try:
                result = await tg_client.send_file(
                    entity=chat,
                    file=dest,
                    caption=file_name,
                    force_document=False,
                    # supports_streaming=True,
                    file_name=file_name,
                )
                logger.info("result: %s", result)
            except Exception as e:
                logger.exception(e)


async def scan_oss_folder_and_upload():
    channel = await tg_client.get_entity(int(os.environ["TARGET"]))

    tasks = [
        upload_oss_file_to_tg(channel, file_obj.key)
        for file_obj in bucket.objects.all()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    if len(tasks) > 0:
        exit(0)
    exit(-1)


async def main():
    await tg_client.start(bot_token=os.environ["TOKEN"])
    async with tg_client:
        await scan_oss_folder_and_upload()


if __name__ == "__main__":
    while time.time() - START < 4 * 60 * 60:
        try:
            sem = asyncio.Semaphore(200)
            tg_client = TelegramClient(
                "bot",
                int(os.environ["API_ID"]),
                os.environ["API_HASH"],
            )
            asyncio.run(main())

        except asyncio.CancelledError:
            pass
