from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, PORT as port
import asyncio
import os


# =========================
async def tcp_server():

    async def handle(reader, writer):
        try:
            writer.write(b"Bot Running")
            await writer.drain()
        except:
            pass
        finally:
            writer.close()

    server = await asyncio.start_server(
        handle,
        "0.0.0.0",
        port
    )

    print(f"TCP Server Running On Port {port}")

    async with server:
        await server.serve_forever()


# =========================
# BOT CLIENT
# =========================
class Bot(Client):

    def __init__(self):
        super().__init__(
            "vj join request bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=50,
            sleep_threshold=10
        )

    async def start(self):

        await super().start()

        me = await self.get_me()

        self.username = '@' + me.username

        print(f'Bot Started -> {self.username}')

        # START TCP SERVER
        asyncio.create_task(tcp_server())

    async def stop(self, *args):

        await super().stop()

        print('Bot Stopped')


# =========================
# START BOT
# =========================
Bot().run()