from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
from plugins.database import db
from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMINS
import asyncio
import datetime
import time
import logging
import psutil
import platform
import shutil




logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"


@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def verupikkals(bot, message):
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    sts = await message.reply_text(
        text='Broadcasting your messages...'
    )
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    blocked = 0
    deleted = 0
    failed =0

    success = 0
    async for user in users:
        if 'id' in user:
            pti, sh = await broadcast_messages(int(user['id']), b_msg)
            if pti:
                success += 1
            elif pti == False:
                if sh == "Blocked":
                    blocked += 1
                elif sh == "Deleted":
                    deleted += 1
                elif sh == "Error":
                    failed += 1
            done += 1
            if not done % 20:
                await sts.edit(f"Broadcast in progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")    
        else:
            # Handle the case where 'id' key is missing in the user dictionary
            done += 1
            failed += 1
            if not done % 20:
                await sts.edit(f"Broadcast in progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")    
    
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.edit(f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")




# =========================
# /stats COMMAND
# =========================
@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats_handler(bot: Client, message: Message):

    start = time.time()

    # USERS
    total_users = await db.total_users_count()

    # CHATS
    total_groups = 0
    total_channels = 0
    total_supergroups = 0

    async for dialog in bot.get_dialogs():

        try:
            chat = dialog.chat

            # only where bot is admin/member
            if chat.type.name in ["GROUP", "SUPERGROUP"]:
                total_groups += 1

                if chat.type.name == "SUPERGROUP":
                    total_supergroups += 1

            elif chat.type.name == "CHANNEL":
                total_channels += 1

        except:
            pass

    # SYSTEM INFO
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()

    disk = shutil.disk_usage("/")

    total_disk = disk.total // (1024**3)
    used_disk = disk.used // (1024**3)
    free_disk = disk.free // (1024**3)

    uptime_seconds = time.time() - psutil.boot_time()
    uptime = str(datetime.timedelta(seconds=int(uptime_seconds)))

    ping = round((time.time() - start) * 1000)

    txt = f"""
<b>📊 BOT STATISTICS</b>

<b>👥 Total Users:</b> <code>{total_users}</code>

<b>💬 Groups:</b> <code>{total_groups}</code>
<b>🏢 Supergroups:</b> <code>{total_supergroups}</code>
<b>📢 Channels:</b> <code>{total_channels}</code>

<b>🖥 Server Stats</b>

<b>⚡ CPU Usage:</b> <code>{cpu}%</code>
<b>🧠 RAM Usage:</b> <code>{ram.percent}%</code>

<b>💾 Disk Used:</b> <code>{used_disk} GB / {total_disk} GB</code>
<b>🆓 Disk Free:</b> <code>{free_disk} GB</code>

<b>⏰ Server Uptime:</b> <code>{uptime}</code>

<b>🐧 OS:</b> <code>{platform.system()} {platform.release()}</code>

<b>🚀 Ping:</b> <code>{ping} ms</code>
"""

    await message.reply_text(txt)
