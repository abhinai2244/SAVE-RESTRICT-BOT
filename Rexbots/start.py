# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official



import os
import asyncio
import random
import time
import shutil
import re
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant, 
    InviteHashExpired, UsernameNotOccupied, AuthKeyUnregistered, UserDeactivated, UserDeactivatedBan
)
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import API_ID, API_HASH, ERROR_MESSAGE, LOG_CHANNEL, ADMINS
from database.db import db
import math
from Rexbots.strings import HELP_TXT, COMMANDS_TXT
from logger import LOGGER

def clean_caption(caption: str) -> str:
    """Remove Telegram links and channel references from caption"""
    if not caption:
        return None
    
    # Remove Telegram t.me links
    caption = re.sub(r'https?:\/\/t\.me\/\S*', '', caption)
    # Remove t.me references without https
    caption = re.sub(r't\.me\/\S*', '', caption)
    # Remove channel references like @channelname
    caption = re.sub(r'@\w+', '', caption)
    # Clean up extra whitespace
    caption = re.sub(r'\s+', ' ', caption).strip()
    
    return caption if caption else None

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "")
    
    if not tmp:
        tmp = ((str(milliseconds) + "ms, ") if milliseconds else "")
        
    return tmp[:-2] if tmp else "0s"

logger = LOGGER(__name__)

class batch_temp(object):
    IS_BATCH = {}

# Simple ask function for Pyrogram
async def ask_user(client, chat_id, text):
    """Simple ask function to get user input"""
    from asyncio import Queue, TimeoutError
    import asyncio

    # Create a queue for responses
    response_queue = Queue()
    user_queues[chat_id] = response_queue

    await client.send_message(chat_id, text)

    try:
        # Wait for response with timeout
        response = await asyncio.wait_for(response_queue.get(), timeout=300)  # 5 minutes timeout
        return response
    except TimeoutError:
        await client.send_message(chat_id, "Timeout! Please try again.")
        return None
    finally:
        user_queues.pop(chat_id, None)

# Global queue for user responses
user_queues = {}

def get_link(string):
    """Extract link from text"""
    import re
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»""'']))"
    url = re.findall(regex, string)
    try:
        link = [x[0] for x in url][0]
        if link:
            return link
        else:
            return False
    except Exception:
        return False

async def chk_user(message, user_id):
    """Check if user is premium or admin"""
    # For now, allow all users - you can implement premium check later
    return 0

def get_chat_id_from_link(link):
    """Extract chat ID from link"""
    if 't.me/c/' in link:
        return int('-100' + link.split("/")[-2])
    elif 't.me/b/' in link:
        return link.split("/")[-2]
    else:
        return link.split("/")[-2]

def get_msg_id_from_link(link):
    """Extract message ID from link"""
    return int(link.split("/")[-1])

# -------------------
# Batch processing users
# -------------------
users_loop = {}

# Conversation states for batch
batch_states = {}

# -------------------
# Supported Telegram Reactions
# -------------------

REACTIONS = [
    "🤝", "😇", "🤗", "😍", "👍", "🎅", "😐", "🥰", "🤩",
    "😱", "🤣", "😘", "👏", "😛", "😈", "🎉", "⚡️", "🫡",
    "🤓", "😎", "🏆", "🔥", "🤭", "🌚", "🆒", "👻", "😁"
]

# Animated loading spinner frames
LOADING_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠃"]
PULSE_FRAMES = ["▓", "▒", "░"]
SPINNER_FRAMES = ["◐", "◓", "◑", "◒"]

# Hindi Motivational Quotes for Progress Bar
MOTIVATIONAL_QUOTES = [
    "शुरुआत ही जीत की आधी राह है!",
    "हर कदम आगे बढ़ाएगा!",
    "मेहनत रंग लाएगी!",
    "सपने सच बनाओ!",
    "आज का प्रयास कल की सफलता!",
    "रोकना मत, चलते रहो!",
    "तुम्हारी मेहनत फल देगी!",
    "लक्ष्य तक पहुंचने का समय!",
    "थोड़ा और प्रयास, जीत करीब!",
    "पूर्णता का द्वार खुल रहा है!",
    "बधाई! आपने इसे पूरा किया!"
]

# Enhanced Animated Progress Bars for each 10% level
PROGRESS_BARS = {
    0: "🔹🔸🔻🔹🔸🔻🔹🔸🔻🔹",
    10: "💥🔹⭐🍀🌙🔥🎯⚡🍩🔸",
    20: "🌟🎧🎲🍫🧩⚙️🎈😎💧🔥",
    30: "🍪🧩🌀💣🦄🧲🌙🚦🍟🐾",
    40: "🧱🍀🎯🍩💥🎧💤🦋🎮🔊",
    50: "🎉🌞🍫🧲🍕🎲🧃💥🎧🍀",
    60: "🎯🧊🎈💜⭐🍩🧩🐢☀️🛸",
    70: "🧩💥🎧🍪🎮🌀⚙️🍀🎲🌈",
    80: "🎊🍕🎈🛸🍫🌙🦄🔥🍟⭐",
    90: "🌀🧲🎯🌈🍕💥⭐🎮🧩🍀",
    100: "🌈🌈🌈🌈🌈🌈🌈🌈🌈🌈"
}

# Colorful Animated Progress Bar - Emoji Style
PROGRESS_BAR_DASHBOARD = """\
{animated_bar} {percentage:.1f}%
{quote}
"""

# Compact progress bar for inline updates
COMPACT_PROGRESS = """\
{spinner} {status} |{bar}| {percentage:.1f}% | {current}/{total} | {speed}/s | ETA: {eta}
"""



# -------------------
# Download status
# -------------------

async def downstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(2)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r", encoding='utf-8') as downread:
                txt = downread.read()
            await client.edit_message_text(
                chat,
                message.id,
                f"╔══════════════════════════════╗\n║     📥 **DOWNLOADING**        ║\n╠══════════════════════════════╣\n{txt}",
                parse_mode=enums.ParseMode.HTML
            )
            await asyncio.sleep(5)
        except:
            await asyncio.sleep(3)

# -------------------
# Upload status
# -------------------

async def upstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(2)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r", encoding='utf-8') as upread:
                txt = upread.read()
            await client.edit_message_text(
                chat,
                message.id,
                f"╔══════════════════════════════╗\n║     📤 **UPLOADING**          ║\n╠══════════════════════════════╣\n{txt}",
                parse_mode=enums.ParseMode.HTML
            )
            await asyncio.sleep(5)
        except:
            await asyncio.sleep(3)

# -------------------
# Progress writer
# -------------------

def progress(current, total, message, type):
    # Check for cancellation
    if batch_temp.IS_BATCH.get(message.from_user.id):
        raise Exception("Cancelled")

    # Initialize cache if not exists
    if not hasattr(progress, "cache"):
        progress.cache = {}
    if not hasattr(progress, "frame_index"):
        progress.frame_index = 0

    now = time.time()
    task_id = f"{message.id}{type}"
    last_time = progress.cache.get(task_id, 0)

    # Track start time for speed calc
    if not hasattr(progress, "start_time"):
        progress.start_time = {}
    if task_id not in progress.start_time:
        progress.start_time[task_id] = now

    # Update every 0.5 seconds for smoother animation
    if (now - last_time) > 0.5 or current == total:
        try:
            percentage = current * 100 / total
            speed = current / (now - progress.start_time[task_id]) if (now - progress.start_time[task_id]) > 0 else 0
            eta = (total - current) / speed if speed > 0 else 0
            elapsed = now - progress.start_time[task_id]

            # Status emoji and text based on type
            if type == "down":
                status_emoji = "📥 DOWNLOAD"
                status_color = "🔵"
            else:
                status_emoji = "📤 UPLOAD"
                status_color = "🟢"

            # Get animated spinner frame (cycles through different animations)
            frame_idx = int(now * 3) % len(LOADING_FRAMES)
            spinner = LOADING_FRAMES[frame_idx]

            # Progress Bar - 20 blocks with gradient effect
            filled_length = int(percentage / 5)  # 20 blocks for 100%
            bar = '█' * filled_length + '░' * (20 - filled_length)

            # Animated progress indicator with color
            progress_anim = "░░░░░░░░░░"[int(percentage/10):] + "▓▓▓▓▓▓▓▓▓▓"[:int(percentage/10)]

            # Dynamic status color based on progress
            if percentage < 25:
                status_color = "🔴"
            elif percentage < 50:
                status_color = "🟠"
            elif percentage < 75:
                status_color = "🟡"
            else:
                status_color = "🟢"

            status = f"{status_color} {status_emoji}"

            # Get progress level (0,10,20,...,100)
            progress_level = int(percentage // 10) * 10
            if progress_level > 100:
                progress_level = 100

            # Determine color based on progress
            if percentage < 25:
                bar_color = '#ff0000'  # red
            elif percentage < 50:
                bar_color = '#ffa500'  # orange
            elif percentage < 75:
                bar_color = '#ffff00'  # yellow
            else:
                bar_color = '#00ff00'  # green

            # Create colorful progress bar
            filled_length = int(percentage / 5)  # 20 blocks
            bar = f'<span style="color:{bar_color}">' + '█' * filled_length + '</span>' + '░' * (20 - filled_length)

            status_formatted = f"{spinner} {status_emoji} |{bar}| {percentage:.1f}% | Speed: {speed:.2f} B/s | ETA: {TimeFormatter(int(eta))}"

            with open(f'{message.id}{type}status.txt', "w", encoding='utf-8') as fileup:
                fileup.write(status_formatted)

            progress.cache[task_id] = now

            if current == total:
                # Cleanup cache
                progress.start_time.pop(task_id, None)
                progress.cache.pop(task_id, None)

        except:
            pass

# -------------------
# Start command
# -------------------

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)

    session = await db.get_session(message.from_user.id)
    login_status = "✅ Logged In" if session else "❌ Not Logged In"

    buttons = [
        [
            InlineKeyboardButton("🆘 How To Use", callback_data="help_btn"),
            InlineKeyboardButton("ℹ️ About Bot", callback_data="about_btn"),
        ],
        [
              InlineKeyboardButton("⚙️ Settings", callback_data="settings_btn")
        ],
        [
            InlineKeyboardButton('📢 Official Channel', url='https://t.me/RexBots_Official'),
            InlineKeyboardButton('👨‍💻 Developer', url='https://t.me/about_zani/143')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await client.send_message(
        chat_id=message.chat.id,
        text=(
            f"<blockquote><b>👋 Welcome {message.from_user.mention}!</b></blockquote>\n\n"
            "<b>I am the Advanced Save Restricted Content Bot by RexBots.</b>\n\n"
            "<blockquote><b>🚀 What I Can Do:</b>\n"
            "<b>‣ Save Restricted Post (Text, Media, Files)</b>\n"
            "<b>‣ Support Private & Public Channels</b>\n"
            "<b>‣ Batch/Bulk Mode Supported</b></blockquote>\n\n"
            f"<blockquote><b>🔐 Status:</b> {login_status}</blockquote>\n\n"
            "<blockquote><b>⚠️ Note:</b> <i>You must <code>/login</code> to your account to use the downloading features.</i></blockquote>"
        ),
        reply_markup=reply_markup,
        reply_to_message_id=message.id,
        parse_mode=enums.ParseMode.HTML
    )

    # try:
    #     await message.react(
    #         emoji=random.choice(REACTIONS),
    #         big=True
    #     )
    # except Exception as e:
    #     print(f"Reaction failed: {e}")

# -------------------
# Help command (standalone)
# -------------------

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(
        chat_id=message.chat.id,
        text=f"{HELP_TXT}"
    )

# -------------------
# Batch command handler
# -------------------

@Client.on_message(filters.private & filters.command(["batch"]))
async def batch_command(client: Client, message: Message):
    user_id = message.chat.id
    lol = await chk_user(message, user_id)
    if lol == 1:
        return

    is_premium = await db.check_premium(user_id)
    is_admin = user_id in ADMINS
    limit = 1000 if is_premium or is_admin else 100

    start = await ask_user(client, message.chat.id, "Please send the start link.")
    if not start:
        return
    start_id = start.text
    s = start_id.split("/")[-1]
    cs = int(s)

    last = await ask_user(client, message.chat.id, "Please send the end link.")
    if not last:
        return
    last_id = last.text
    l = last_id.split("/")[-1]
    cl = int(l)

    if cl - cs > limit:
        await client.send_message(message.chat.id, f"Only {limit} messages allowed in batch size... Purchase premium to fly 💸")
        return

    try:
        user_data = await db.get_session(user_id)

        if user_data:
            session = user_data
            try:
                userbot = Client(":userbot:", api_id=API_ID, api_hash=API_HASH, session_string=session)
                await userbot.start()
            except:
                return await client.send_message(message.chat.id, "Your login expired ... /login again")
        else:
            await client.send_message(message.chat.id, "Login in bot first ...")

        try:
            users_loop[user_id] = True

            for i in range(int(s), int(l)):
                if user_id in users_loop and users_loop[user_id]:
                    msg = await client.send_message(message.chat.id, "Processing!")
                    try:
                        x = start_id.split('/')
                        y = x[:-1]
                        result = '/'.join(y)
                        url = f"{result}/{i}"
                        link = get_link(url)
                        await handle_private(client, userbot, message, get_chat_id_from_link(link), get_msg_id_from_link(link))
                        sleep_msg = await client.send_message(message.chat.id, "Sleeping for 10 seconds to avoid flood...")
                        await asyncio.sleep(8)
                        await sleep_msg.delete()
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"Error processing link {url}: {e}")
                        continue
                else:
                    break
        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {str(e)}")

    except FloodWait as fw:
        await client.send_message(message.chat.id, f'Try again after {fw.x} seconds due to floodwait from Telegram.')
    except Exception as e:
        await client.send_message(message.chat.id, f"Error: {str(e)}")

# -------------------
# Cancel command
# -------------------

@Client.on_message(filters.private & filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    logger.info(f"Cancel command received from user {message.from_user.id}")

    user_id = message.chat.id
    if user_id in users_loop:
        users_loop[user_id] = False
        await client.send_message(message.chat.id, "Batch processing stopped.")
    else:
        await client.send_message(message.chat.id, "No active batch processing to stop.")


# -------------------
# Handle incoming messages
# -------------------

# Handler for batch conversation responses
@Client.on_message(filters.private & filters.text & ~filters.regex("^/"))
async def handle_batch_response(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in user_queues:
        await user_queues[chat_id].put(message)
        return

@Client.on_message(filters.private & filters.regex(r'https?://[^\s]+') & ~filters.create(lambda _, __, msg: msg.chat.id in user_queues))
async def single_link(client: Client, message: Message):
    user_id = message.chat.id
    lol = await chk_user(message, user_id)
    if lol == 1:
        return

    link = get_link(message.text)

    try:
        msg = await message.reply("Processing...")

        # Try to get user session if available
        user_data = await db.get_session(user_id)
        session = None
        userbot = None

        if user_data:
            session = user_data
            try:
                userbot = Client(":userbot:", api_id=API_ID, api_hash=API_HASH, session_string=session)
                await userbot.start()
            except:
                await msg.edit_text("Login expired /login again...")
                return

        if 't.me/' in link:
            await process_single_link(client, userbot, user_id, msg.id, link, message)

    except Exception as e:
        await msg.edit_text(f"Link: `{link}`\n\n**Error:** {str(e)}")

async def process_single_link(client, userbot, sender, edit_id, msg_link, message):
    edit = ""
    chat = ""

    if "?single" in msg_link:
        msg_link = msg_link.split("?single")[0]

    msg_id = int(msg_link.split("/")[-1])

    if 't.me/c/' in msg_link or 't.me/b/' in msg_link:
        if 't.me/b/' not in msg_link:
            chat = int('-100' + str(msg_link.split("/")[-2]))
        else:
            chat = msg_link.split("/")[-2]

        try:
            if userbot:
                msg = await userbot.get_messages(chat, msg_id)
                if msg.service or msg.empty:
                    return

                if msg.media and msg.media == MessageMediaType.WEB_PAGE:
                    await client.edit_message_text(sender, edit_id, "Cloning...")
                    safe_repo = await client.send_message(sender, msg.text.markdown)
                    if LOG_CHANNEL:
                        await safe_repo.copy(LOG_CHANNEL)
                    await client.delete_messages(sender, edit_id)
                    return

                if not msg.media and msg.text:
                    await client.edit_message_text(sender, edit_id, "Cloning...")
                    safe_repo = await client.send_message(sender, msg.text.markdown)
                    if LOG_CHANNEL:
                        await safe_repo.copy(LOG_CHANNEL)
                    await client.delete_messages(sender, edit_id)
                    return

                await client.edit_message_text(sender, edit_id, "Trying to Download...")
                file = await userbot.download_media(msg, progress=progress, progress_args=[message, "down"])

                # Process file and upload
                await process_and_upload(client, userbot, sender, edit_id, msg, file, message)

        except Exception as e:
            await client.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')

    else:
        # Public channel - try direct copy first
        await client.edit_message_text(sender, edit_id, "Cloning...")
        try:
            chat = msg_link.split("/")[-2]
            await copy_message_public(client, sender, chat, msg_id, message)
            await client.delete_messages(sender, edit_id)
        except Exception as e:
            await client.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')

async def copy_message_public(client, sender, chat_id, message_id, original_message):
    try:
        msg = await client.get_messages(chat_id, message_id)

        if msg.media:
            if msg.media == MessageMediaType.VIDEO:
                result = await client.send_video(sender, msg.video.file_id, caption=msg.caption)
            elif msg.media == MessageMediaType.DOCUMENT:
                result = await client.send_document(sender, msg.document.file_id, caption=msg.caption)
            elif msg.media == MessageMediaType.PHOTO:
                result = await client.send_photo(sender, msg.photo.file_id, caption=msg.caption)
            else:
                result = await client.copy_message(sender, chat_id, message_id)
        else:
            result = await client.copy_message(sender, chat_id, message_id)

        # Copy to log channel if available
        try:
            log_channel = os.environ.get("LOG_CHANNEL")
            if log_channel:
                await result.copy(log_channel)
        except:
            pass

        if msg.pinned_message:
            try:
                await result.pin(both_sides=True)
            except:
                await result.pin()

    except Exception as e:
        # If direct copy fails, try with userbot if available
        raise e

async def process_and_upload(client, userbot, sender, edit_id, msg, file, message):
    await client.edit_message_text(sender, edit_id, 'Trying to Upload...')

    if msg.media == MessageMediaType.VIDEO:
        try:
            await client.send_video(
                chat_id=sender,
                video=file,
                caption=clean_caption(msg.caption),
                progress=progress,
                progress_args=[message, "up"]
            )
        except:
            await client.edit_message_text(sender, edit_id, "The bot is not an admin in the specified chat...")

    elif msg.media == MessageMediaType.PHOTO:
        await client.send_photo(sender, file, caption=clean_caption(msg.caption))

    else:
        await client.send_document(
            chat_id=sender,
            document=file,
            caption=clean_caption(msg.caption),
            progress=progress,
            progress_args=[message, "up"]
        )

    # Cleanup
    if os.path.exists(file):
        os.remove(file)

    await client.delete_messages(sender, edit_id)

@Client.on_message(filters.private & filters.text & ~filters.regex("^/") & ~filters.create(lambda _, __, msg: msg.chat.id in user_queues))
async def save(client: Client, message: Message):
    try:
        logger.info(f"Received message from {message.from_user.id}: {message.text}")
        if "https://t.me/" in message.text:
            await message.reply("🔄 **Processing your link...**", parse_mode=enums.ParseMode.HTML)
        # Check if batch is already running
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text(
                "**__⚠️ One Task Is Already Processing. Wait For Complete It.\nIf You Want To Cancel This Task Then Use - /cancel__**",
                parse_mode=enums.ParseMode.HTML
            )

        # Initialize batch flag
        batch_temp.IS_BATCH[message.from_user.id] = False

        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        try:
            toID = int(temp[1].strip())
        except:
            toID = fromID

        is_private = "https://t.me/c/" in message.text
        is_batch = "https://t.me/b/" in message.text
        
        # Calculate total messages for progress
        total_msgs = toID - fromID + 1
        
        # Send batch start confirmation
        start_msg = await message.reply_text(
            f"**__📦 Batch Processing Started__**\n"
            f"**📋 Range:** {fromID} - {toID} ({total_msgs} messages)\n"
            f"**🔄 Status:** Processing...",
            parse_mode=enums.ParseMode.HTML
        )
        
        for msgid in range(fromID, toID + 1):
            if batch_temp.IS_BATCH.get(message.from_user.id):
                break
            
            # Update progress message
            current_num = msgid - fromID + 1
            percentage = (current_num / total_msgs) * 100 if total_msgs > 0 else 0
            try:
                await start_msg.edit(
                    f"**__📦 Batch Processing__**\n"
                    f"**📋 Progress:** {current_num}/{total_msgs} ({percentage:.1f}%)\n"
                    f"**🔄 Processing ID:** {msgid}",
                    parse_mode=enums.ParseMode.HTML
                )
            except:
                pass
            
            # 1. Try Public Copy (No Login Required)
            if not is_private and not is_batch:
                username = datas[3]
                try:
                    msg = await client.get_messages(username, msgid)
                    await client.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                    await asyncio.sleep(1)
                    continue
                except Exception as e:
                    logger.error(f"Public copy failed for {username}/{msgid}: {e}")
                    pass # Fallback to login method
            
            # 2. Login Check
            user_data = await db.get_session(message.from_user.id)
            if user_data is None:
                await message.reply("**__🚪 For Downloading Restricted Content You Have To /login First.__**")
                batch_temp.IS_BATCH[message.from_user.id] = True
                await start_msg.edit("**__❌ Batch Stopped: Not Logged In__**", parse_mode=enums.ParseMode.HTML)
                return

            # 3. Connect User Client
            try:
                acc = Client("saverestricted", session_string=user_data, api_hash=API_HASH, api_id=API_ID, in_memory=True)
                await acc.connect()
            except (AuthKeyUnregistered, UserDeactivated, UserDeactivatedBan) as e:
                batch_temp.IS_BATCH[message.from_user.id] = True
                await db.set_session(message.from_user.id, None)
                await message.reply(f"**__🚪 Your Login Session Invalid/Expired. Please /login again.__**\nError: {e}")
                await start_msg.edit("**__❌ Batch Stopped: Session Expired__**", parse_mode=enums.ParseMode.HTML)
                return
            except Exception:
                batch_temp.IS_BATCH[message.from_user.id] = True
                await message.reply("**__🚪 Your Login Session Error. So /logout First Then Login Again By - /login__**")
                await start_msg.edit("**__❌ Batch Stopped: Session Error__**", parse_mode=enums.ParseMode.HTML)
                return

            # 4. Handle Content
            if is_private:
                chatid = int("-100" + datas[4])
                try:
                    await handle_private(client, acc, message, chatid, msgid)
                except Exception as e:
                    logger.error(f"Error handling private chat: {e}")
                    if ERROR_MESSAGE:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            elif is_batch:
                username = datas[4]
                try:
                    await handle_private(client, acc, message, username, msgid)
                except Exception as e:
                    logger.error(f"Error handling batch channel: {e}")
                    if ERROR_MESSAGE:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            else:
                # Restricted Public Channel
                username = datas[3]
                try:
                    await handle_private(client, acc, message, username, msgid)
                except Exception as e:
                    logger.error(f"Error copy/handle private: {e}")
                    if ERROR_MESSAGE:
                         await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            await asyncio.sleep(2)

        batch_temp.IS_BATCH[message.from_user.id] = True
        
        # Send completion message
        if not batch_temp.IS_BATCH.get(message.from_user.id, True):
            await start_msg.edit("**__✅ Batch Processing Completed Successfully!__**", parse_mode=enums.ParseMode.HTML)
        else:
            await start_msg.edit("**__ℹ️ Batch Processing Ended__**", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error in save function: {e}")
        if ERROR_MESSAGE:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

# -------------------
# Handle private content
# -------------------

async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int) -> bool:
    try:
        msg: Message = await acc.get_messages(chatid, msgid)
    except (AuthKeyUnregistered, UserDeactivated, UserDeactivatedBan) as e:
        batch_temp.IS_BATCH[message.from_user.id] = True
        await db.set_session(message.from_user.id, None)
        await client.send_message(message.chat.id, f"Session Token Invalid/Expired. Please /login again.\nError: {e}")
        return False
    except Exception as e:
        # Handle PeerIdInvalid (which might come as generic Exception or RPCError)
        # We try to refresh dialogs to learn about the peer.
        logger.warning(f"Error fetching message: {e}. Refreshing dialogs...")
        try:
            async for dialog in acc.get_dialogs(limit=None):
                if dialog.chat.id == chatid:
                    break
            msg: Message = await acc.get_messages(chatid, msgid)
        except (AuthKeyUnregistered, UserDeactivated, UserDeactivatedBan) as e:
            batch_temp.IS_BATCH[message.from_user.id] = True
            await db.set_session(message.from_user.id, None)
            await client.send_message(message.chat.id, f"Session Token Invalid/Expired. Please /login again.\nError: {e}")
            return False
        except Exception as e2:
            logger.error(f"Retry failed: {e2}")
            return False
# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official

    if msg.empty:
        return False

    msg_type = get_message_type(msg)
    if not msg_type:
        return False

    chat = message.chat.id
    if batch_temp.IS_BATCH.get(message.from_user.id):
        return False

    if "Text" == msg_type:
        try:
            await client.send_message(chat, f"**__{msg.text}__**", entities=msg.entities, reply_to_message_id=message.id,
                                      parse_mode=enums.ParseMode.HTML)
            return True
        except Exception as e:
            logger.error(f"Error sending text message: {e}")
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id,
                                          parse_mode=enums.ParseMode.HTML)
            return False

    smsg = await client.send_message(
        message.chat.id,
        '╔══════════════════════════════╗\n║     🚀 **PROCESSING**          ║\n╠══════════════════════════════╣\n║  Preparing your file...       ║\n║  Please wait...               ║\n╚══════════════════════════════╝',
        reply_to_message_id=message.id,
        parse_mode=enums.ParseMode.HTML
    )
    
    # ----------------------------------------
    # Create unique temp directory for this task
    # ----------------------------------------
    temp_dir = f"downloads/{message.id}"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    try:
        asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, chat))
    except Exception as e:
        logger.error(f"Error creating download status task: {e}")
        
    try:
        # Download into unique directory (folder path must end with / for Pyrogram)
        file = await acc.download_media(msg, file_name=f"{temp_dir}/", progress=progress, progress_args=[message, "down"])
        if os.path.exists(f'{message.id}downstatus.txt'):
            os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        # Check if cancelled (flag is True) or exception message contains "Cancelled"
        if batch_temp.IS_BATCH.get(message.from_user.id) or "Cancelled" in str(e):
            if os.path.exists(f'{message.id}downstatus.txt'):
                try:
                    os.remove(f'{message.id}downstatus.txt')
                except:
                    pass
            
            # Robust Cleanup: Delete the entire temp directory
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
        
            return await smsg.edit("❌ **Task Cancelled**")
            
        logger.error(f"Error downloading media: {e}")
        
        # Cleanup on error
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
                
        if ERROR_MESSAGE:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id,
                                      parse_mode=enums.ParseMode.HTML)
        return await smsg.delete()

    if batch_temp.IS_BATCH.get(message.from_user.id):
        # Cleanup if cancelled during gap
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        return False

    try:
        asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, chat))
    except Exception as e:
        logger.error(f"Error creating upload status task: {e}")
    caption = clean_caption(msg.caption) if msg.caption else None
    
    if batch_temp.IS_BATCH.get(message.from_user.id):
         # Cleanup if cancelled during gap
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        return False

    try:
        if "Document" == msg_type:
            try:
                ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
            except:
                ph_path = None
            await client.send_document(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id,
                                       parse_mode=enums.ParseMode.HTML, progress=progress,
                                       progress_args=[message, "up"])
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)

        elif "Video" == msg_type:
            try:
                ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
            except:
                ph_path = None
            await client.send_video(chat, file, duration=msg.video.duration, width=msg.video.width,
                                    height=msg.video.height, thumb=ph_path, caption=caption,
                                    reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML,
                                    progress=progress, progress_args=[message, "up"])
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)

        elif "Animation" == msg_type:
            await client.send_animation(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

        elif "Sticker" == msg_type:
            await client.send_sticker(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

        elif "Voice" == msg_type:
            await client.send_voice(chat, file, caption=caption, caption_entities=msg.caption_entities,
                                    reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML,
                                    progress=progress, progress_args=[message, "up"])

        elif "Audio" == msg_type:
            try:
                ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
            except:
                ph_path = None
            await client.send_audio(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id,
                                    parse_mode=enums.ParseMode.HTML, progress=progress,
                                    progress_args=[message, "up"])
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)

        elif "Photo" == msg_type:
            await client.send_photo(chat, file, caption=caption, reply_to_message_id=message.id,
                                    parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        # Check if cancelled (flag is True) or exception message contains "Cancelled"
        if batch_temp.IS_BATCH.get(message.from_user.id) or "Cancelled" in str(e):
            if os.path.exists(f'{message.id}upstatus.txt'):
                try:
                    os.remove(f'{message.id}upstatus.txt')
                except:
                    pass
            
            # Robust Cleanup: Delete the entire temp directory
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            return await smsg.edit("❌ **Task Cancelled**")

        logger.error(f"Error sending media: {e}")
        if ERROR_MESSAGE:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id,
                                      parse_mode=enums.ParseMode.HTML)

    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
        
    # Final cleanup of temp directory
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

    await client.delete_messages(message.chat.id, [smsg.id])
    return True

#-------------------
# Get message type
# -------------------

def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass
    try:
        msg.video.file_id
        return "Video"
    except:
        pass
    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass
    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass
    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass
    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass
    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass
    try:
        msg.text
        return "Text"
    except:
        pass

# -------------------
# Inline button callback
# -------------------

@Client.on_callback_query()
async def button_callbacks(client: Client, callback_query):
    data = callback_query.data
    message = callback_query.message

    # Help button  
    if data == "help_btn":
        help_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Cʟᴏsᴇ ❌", callback_data="close_btn"),
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_btn")
            ]
        ])
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.id,
            text=HELP_TXT,
            reply_markup=help_buttons,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback_query.answer()

    # About button
    elif data == "about_btn":
        me = await client.get_me()
        about_text = (
            "<b><blockquote>‣ ℹ️ 𝐁𝐎𝐓 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍</blockquote>\n\n"
            "<i>• 🤖 𝐍𝐚𝐦𝐞 : 𝐒𝐚𝐯𝐞 𝐑𝐞𝐬𝐭𝐫𝐢𝐜𝐭𝐞𝐝 𝐂𝐨𝐧𝐭𝐞𝐧𝐭\n"
            "• 👨‍💻 𝐎𝐰𝐧𝐞𝐫 : <a href='https://t.me/RexBots_Official'>𝐑𝐞𝐱𝐁𝐨𝐭𝐬</a>\n"
            "• 📡 𝐔𝐩𝐝𝐚𝐭𝐞𝐬 : <a href='https://t.me/RexBots_Official'>𝐑𝐞𝐱𝐁𝐨𝐭𝐬 𝐎𝐟𝐟𝐢𝐜𝐢𝐚𝐥</a>\n"
            "• 🐍 𝐋𝐚𝐧𝐠𝐮𝐚𝐠𝐞 : <a href='https://www.python.org/'>𝐏𝐲𝐭𝐡𝐨𝐧 𝟑</a>\n"
            "• 📚 𝐋𝐢𝐛𝐫𝐚𝐫𝐲 : <a href='https://docs.pyrogram.org/'>𝐏𝐲𝐫𝐨𝐠𝐫𝐚𝐦</a>\n"
            "• 🗄 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 : <a href='#'>𝐉𝐒𝐎𝐍 𝐅𝐢𝐥𝐞</a>\n"
            "• 📊 𝐕𝐞𝐫𝐬𝐢𝐨𝐧 : 𝟐.𝟎.𝟏 [𝐒𝐭𝐚𝐛𝐥𝐞]</i></b>"
        )

        about_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📢 Join Channel", url="https://t.me/RexBots_Official")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close_btn"),
                InlineKeyboardButton("🔙 Back", callback_data="start_btn")
            ]
        ])

        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.id,
            text=about_text,
            reply_markup=about_buttons,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback_query.answer()

    # Home / Start button
    elif data == "start_btn":
        session = await db.get_session(callback_query.from_user.id)
        login_status = "✅ Logged In" if session else "❌ Not Logged In"

        start_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🆘 How To Use", callback_data="help_btn"),
                InlineKeyboardButton("ℹ️ About Bot", callback_data="about_btn")
            ],
            [
                InlineKeyboardButton('📢 Official Channel', url='https://t.me/RexBots_Official'),
                InlineKeyboardButton('👨‍💻 Developer', url='https://t.me/RexBots_Official')
            ]
        ])
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.id,
            text=(
                f"<blockquote><b>👋 Welcome {callback_query.from_user.mention}!</b></blockquote>\n\n"
                "<b>I am the Advanced Save Restricted Content Bot by RexBots.</b>\n\n"
                "<blockquote><b>🚀 What I Can Do:</b>\n"
                "<b>‣ Save Restricted Post (Text, Media, Files)</b>\n"
                "<b>‣ Support Private & Public Channels</b>\n"
                "<b>‣ Batch/Bulk Mode Supported</b></blockquote>\n\n"
                f"<blockquote><b>🔐 Status:</b> {login_status}</blockquote>\n\n"
                "<blockquote><b>⚠️ Note:</b> <i>You must <code>/login</code> to your account to use the downloading features.</i></blockquote>"
            ),
            reply_markup=start_buttons,
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()

    # Settings button (Command List)
    elif data == "settings_btn":
        settings_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ Close", callback_data="close_btn"),
                InlineKeyboardButton("🔙 Back", callback_data="start_btn")
            ]
        ])
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.id,
            text=COMMANDS_TXT,
            reply_markup=settings_buttons,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback_query.answer()

    # Close button
    elif data == "close_btn":
        await client.delete_messages(message.chat.id, [message.id])
        await callback_query.answer()


# Don't remove Credits
# Rexbots
# Developer Telegram @RexBots_Official
# Update channel - @RexBots_Official

# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official
