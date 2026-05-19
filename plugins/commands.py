import asyncio 
from pyrogram import Client, filters, enums
from config import LOG_CHANNEL, API_ID, API_HASH, NEW_REQ_MODE
from plugins.database import db
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

LOG_TEXT = """<b>#NewUser
    
ID - <code>{}</code>

Nᴀᴍᴇ - {}</b>
"""

@Client.on_message(filters.command('start'))
async def start_message(c,m):
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id, m.from_user.first_name)
        await c.send_message(LOG_CHANNEL, LOG_TEXT.format(m.from_user.id, m.from_user.mention))
    await m.reply_photo(f"https://te.legra.ph/file/119729ea3cdce4fefb6a1.jpg",
        caption=f"<b>Hello {m.from_user.mention} 👋\n\nI Am Join Request Acceptor Bot. I Can Accept All Old Pending Join Request.\n\nFor All Pending Join Request Use - /accept</b>",
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("❣️ ᴅᴇᴠᴇʟᴏᴘᴇʀ", url='https://t.me/roger_pro'),
                InlineKeyboardButton("🤖 ᴜᴘᴅᴀᴛᴇ", url='https://t.me/Codeflix_Bots')
            ]]
        )
    )

@Client.on_message(filters.command('accept') & filters.private)
async def accept(client, message):
    show = await message.reply("**Please Wait.....**")
    user_data = await db.get_session(message.from_user.id)
    if user_data is None:
        await show.edit("**For Accepte Pending Request You Have To /login First.**")
        return
    try:
        acc = Client("joinrequest", session_string=user_data, api_hash=API_HASH, api_id=API_ID)
        await acc.connect()
    except:
        return await show.edit("**Your Login Session Expired. So /logout First Then Login Again By - /login**")

    show = await show.edit("**Now Forward A Message From Your Channel Or Group With Forward Tag\n\nMake Sure Your Logged In Account Is Admin In That Channel Or Group With Full Rights.**")
    vj = await client.listen(message.chat.id)

    if vj.forward_from_chat and not vj.forward_from_chat.type in [enums.ChatType.PRIVATE, enums.ChatType.BOT]:
        chat_id = vj.forward_from_chat.id
        try:
            info = await acc.get_chat(chat_id)
        except:
            return await show.edit("**Error - Make Sure Your Logged In Account Is Admin In This Channel Or Group With Rights.**")
    else:
        return await message.reply("**Message Not Forwarded From Channel Or Group.**")

    await vj.delete()
    msg = await show.edit("**Accepting all join requests... Please wait until it's completed.**")

    success = 0
    failed = 0
    try:
        while True:
            join_requests = [req async for req in acc.get_chat_join_requests(chat_id)]
            if not join_requests:
                break
            for req in join_requests:
                try:
                    await acc.approve_chat_join_request(chat_id, req.from_user.id)
                    try:
                        await client.send_message(
                            req.from_user.id,
                            f"**Hello {req.from_user.mention}!\nWelcome To {info.title}\n\n__Powered By : @Codeflix_bots__**"
                        )
                    except Exception as e:
                        print(f"Failed to send message to {req.from_user.id}: {e}")
                    success += 1
                except Exception as e:
                    print(f"Failed to approve {req.from_user.id}: {e}")
                    failed += 1
            await asyncio.sleep(1)
        await msg.edit(f"**Successfully accepted join requests.**\n\n✅ Success: {success}\n❌ Failed: {failed}")
    except Exception as e:
        await msg.edit(f"**An error occurred:** {str(e)}")
        
@Client.on_chat_join_request(filters.group | filters.channel)
async def approve_new(client, m):
    if NEW_REQ_MODE == False:
        return 
    try:
        if not await db.is_user_exist(m.from_user.id):
            await db.add_user(m.from_user.id, m.from_user.first_name)
            await client.send_message(LOG_CHANNEL, LOG_TEXT.format(m.from_user.id, m.from_user.mention))
        await client.approve_chat_join_request(m.chat.id, m.from_user.id)
        try:
            await client.send_message(m.from_user.id, "**Hello {}!\nWelcome To {}\n\n__Powered By : @Codeflix_bots __**".format(m.from_user.mention, m.chat.title))
        except:
            pass
    except Exception as e:
        print(str(e))
        pass

# =========================
# broadcast+ stats
# =========================


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
