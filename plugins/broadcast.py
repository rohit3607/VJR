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

# ==========================================
# CANCEL SYSTEM
# ==========================================
cancel_lock = asyncio.Lock()
is_canceled = False


# ==========================================
# AUTO DELETE
# ==========================================
async def auto_delete(sent_msg, duration):

    await asyncio.sleep(duration)

    try:
        await sent_msg.delete()
    except:
        pass


# ==========================================
# SEND BROADCAST MESSAGE
# ==========================================
async def broadcast_messages(
    bot,
    user_id,
    message,
    do_pin=False,
    do_delete=False,
    duration=0,
    silent=False
):

    try:

        sent_msg = await message.copy(
            chat_id=user_id,
            disable_notification=silent
        )

        # PIN MESSAGE
        if do_pin:

            try:
                await bot.pin_chat_message(
                    chat_id=user_id,
                    message_id=sent_msg.id,
                    both_sides=True
                )
            except:
                pass

        # AUTO DELETE
        if do_delete:
            asyncio.create_task(
                auto_delete(sent_msg, duration)
            )

        return True, "Success"

    except FloodWait as e:

        await asyncio.sleep(e.value)

        return await broadcast_messages(
            bot,
            user_id,
            message,
            do_pin,
            do_delete,
            duration,
            silent
        )

    except InputUserDeactivated:

        await db.delete_user(int(user_id))

        logging.info(
            f"{user_id} - Removed from Database (Deleted Account)"
        )

        return False, "Deleted"

    except UserIsBlocked:

        await db.delete_user(int(user_id))

        logging.info(
            f"{user_id} - Blocked the bot"
        )

        return False, "Blocked"

    except PeerIdInvalid:

        await db.delete_user(int(user_id))

        logging.info(
            f"{user_id} - PeerIdInvalid"
        )

        return False, "Error"

    except Exception as e:

        logging.error(
            f"Broadcast Error {user_id}: {e}"
        )

        return False, "Error"


# ==========================================
# CANCEL COMMAND
# ==========================================
@Client.on_message(
    filters.command("cancel")
    & filters.user(ADMINS)
)
async def cancel_broadcast(bot, message):

    global is_canceled

    async with cancel_lock:
        is_canceled = True

    await message.reply_text(
        "<b>Broadcast cancellation requested ❌</b>"
    )


# ==========================================
# BROADCAST COMMAND
# ==========================================
@Client.on_message(
    filters.command("broadcast")
    & filters.user(ADMINS)
    & filters.reply
)
async def verupikkals(bot, message: Message):

    global is_canceled

    args = message.text.split()[1:]

    # ======================================
    # MODES
    # ======================================
    do_pin = False
    do_delete = False
    duration = 0
    silent = False

    mode_text = []

    i = 0

    while i < len(args):

        arg = args[i].lower()

        if arg == "pin":

            do_pin = True
            mode_text.append("PIN")

        elif arg == "delete":

            do_delete = True

            try:
                duration = int(args[i + 1])
                i += 1

            except (IndexError, ValueError):

                return await message.reply_text(
                    "<b>Provide valid delete duration.</b>\n\n"
                    "Example:\n"
                    "<code>/broadcast delete 30</code>"
                )

            mode_text.append(
                f"DELETE({duration}s)"
            )

        elif arg == "silent":

            silent = True
            mode_text.append("SILENT")

        else:

            mode_text.append(arg.upper())

        i += 1

    if not mode_text:
        mode_text.append("NORMAL")

    # ======================================
    # RESET CANCEL FLAG
    # ======================================
    async with cancel_lock:
        is_canceled = False

    users = await db.get_all_users()

    b_msg = message.reply_to_message

    sts = await message.reply_text(
        text=(
            f"<b>Broadcast Started "
            f"({' + '.join(mode_text)})...</b>"
        )
    )

    start_time = time.time()

    total_users = await db.total_users_count()

    done = 0
    blocked = 0
    deleted = 0
    failed = 0
    success = 0

    # ======================================
    # PROGRESS SETTINGS
    # ======================================
    bar_length = 20
    progress_bar = ""

    # ======================================
    # LOOP
    # ======================================
    async for user in users:

        # CANCEL CHECK
        async with cancel_lock:

            if is_canceled:

                return await sts.edit_text(
                    "<b>Broadcast canceled ❌</b>"
                )

        # INVALID USER
        if 'id' not in user:

            done += 1
            failed += 1

            continue

        user_id = int(user['id'])

        pti, sh = await broadcast_messages(
            bot=bot,
            user_id=user_id,
            message=b_msg,
            do_pin=do_pin,
            do_delete=do_delete,
            duration=duration,
            silent=silent
        )

        # RESULTS
        if pti:

            success += 1

        else:

            if sh == "Blocked":
                blocked += 1

            elif sh == "Deleted":
                deleted += 1

            elif sh == "Error":
                failed += 1

        done += 1

        # ==================================
        # UPDATE STATUS
        # ==================================
        if not done % 20:

            percent = done / total_users

            filled = int(
                percent * bar_length
            )

            progress_bar = (
                "●" * filled
                + "○" * (bar_length - filled)
            )

            try:

                await sts.edit_text(
                    f"""
<b>📢 Broadcast In Progress...</b>

<blockquote>
[{progress_bar}] <code>{percent:.0%}</code>
</blockquote>

<b>Mode:</b> <code>{' + '.join(mode_text)}</code>

<b>Total Users:</b> <code>{total_users}</code>

<b>Completed:</b> <code>{done}/{total_users}</code>

<b>✅ Success:</b> <code>{success}</code>
<b>🚫 Blocked:</b> <code>{blocked}</code>
<b>🗑 Deleted:</b> <code>{deleted}</code>
<b>❌ Failed:</b> <code>{failed}</code>

<i>Use /cancel to stop broadcast.</i>
"""
                )

            except:
                pass

    # ======================================
    # FINAL STATUS
    # ======================================
    time_taken = datetime.timedelta(
        seconds=int(time.time() - start_time)
    )

    final_percent = done / total_users

    filled = int(final_percent * bar_length)

    progress_bar = (
        "●" * filled
        + "○" * (bar_length - filled)
    )

    await sts.edit_text(
        f"""
<b>📢 Broadcast Completed ✅</b>

<blockquote>
[{progress_bar}] <code>100%</code>
</blockquote>

<b>Mode:</b> <code>{' + '.join(mode_text)}</code>

<b>Total Users:</b> <code>{total_users}</code>

<b>Completed:</b> <code>{done}/{total_users}</code>

<b>✅ Success:</b> <code>{success}</code>
<b>🚫 Blocked:</b> <code>{blocked}</code>
<b>🗑 Deleted:</b> <code>{deleted}</code>
<b>❌ Failed:</b> <code>{failed}</code>

<b>⏱ Time Taken:</b> <code>{time_taken}</code>
"""
    )




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
