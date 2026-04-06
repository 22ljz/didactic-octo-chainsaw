from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename
from telethon.sessions import StringSession
import subprocess
import os

bot = TelegramClient(
    StringSession(os.environ["TOKEN"]),
    int(os.environ["API_ID"]),
    os.environ["API_HASH"],
).start()


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Send a message when the command /start is issued."""
    await event.respond("Hi!")
    raise events.StopPropagation


@bot.on(events.NewMessage())
async def download_file(event):
    if event.file:
        filename = None
        for attr in event.message.media.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                filename = attr.file_name
                break

        await event.reply(f"Downloading {filename}...")

        await event.message.download_media(
            file=filename,
            progress_callback=lambda d, t: print(
                f"Download: {d / t * 100:.1f}% ({d}/{t} bytes)", end="\r"
            ),
        )
        await event.reply("File downloaded successfully!")
        output = subprocess.check_output(["bash", "-c", f"./transfer lit {filename}"]).decode().strip().split("\n")[-1].strip()
        await event.reply(output)

        bot.disconnect()


def main():
    bot.run_until_disconnected()


if __name__ == "__main__":
    main()
