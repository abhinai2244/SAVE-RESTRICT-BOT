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
from config import API_ID, API_HASH, ERROR_MESSAGE
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

# -------------------
# Batch conversation state management
# -------------------
BATCH_STATE = {
    "WAITING_START_LINK": "waiting_start_link",
    "WAITING_END_LINK": "waiting_end_link",
    "IDLE": "idle"
}

batch_conversation_state = {}

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

# Modern animated progress bar with complete details - Enhanced Version
PROGRESS_BAR_DASHBOARD = """\
╔══════════════════════════════════════════╗
║  {spinner}  📊 {status}              ║
╠══════════════════════════════════════════╣
║  {bar}                           ║
║  ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░  {percentage:>5.1f}%     ║
╠══════════════════════════════════════════╣
║  📁 Size:    {current:>10} / {total:<10} ║
║  ⚡ Speed:   {speed:>10}/s            ║
║  ⏱️ ETA:     {eta:<15}         ║
║  ⏰ Elapsed: {elapsed:<15}         ║
║  📶 Progress:{progress:>15}      ║
╚══════════════════════════════════════════╝
Task ID: {task_id}
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
            
            status_formatted = PROGRESS_BAR_DASHBOARD.format(
                spinner=spinner,
                status=status,
                bar=bar,
                percentage=percentage,
                current=humanbytes(current),
                total=humanbytes(total),
                speed=humanbytes(speed),
                eta=TimeFormatter(eta * 1000),
                elapsed=TimeFormatter(elapsed * 1000),
                progress=progress_anim,
                task_id=task_id[:8]
            )
            
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
    """Handle /batch command to start interactive batch processing"""
    logger.info(f"Batch command received from user {message.from_user.id}")
    
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    
    # Check if user is logged in
    user_data = await db.get_session(message.from_user.id)
    if user_data is None:
        await message.reply_text(
            "**🚪 Please /login First To Use Batch Feature.**",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Check if batch is already running
    if batch_temp.IS_BATCH.get(message.from_user.id) == False:
        await message.reply_text(
            "**⚠️ One Batch Task Is Already Processing. Wait For Complete It.\nIf You Want To Cancel This Task Then Use - /cancel**",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Check if user is already in batch conversation
    if message.from_user.id in batch_conversation_state:
        await message.reply_text(
            "**⚠️ You already have an active batch conversation.\n"
            "Send /cancel to cancel and start fresh.**",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Set conversation state to waiting for start link
    batch_conversation_state[message.from_user.id] = {"state": BATCH_STATE["WAITING_START_LINK"]}
    
    # Send interactive batch instructions
    await message.reply_text(
        "**📦 Interactive Batch Mode Started!**\n\n"
        "**Step 1/2:** Send the START link\n"
        "(First message you want to download)\n\n"
        "Example:\n"
        "• Public: `https://t.me/username/10`\n"
        "• Private: `https://t.me/c/123456789/10`\n"
        "• Batch: `https://t.me/b/username/10`\n\n"
        "Send /cancel to cancel the batch process.",
        parse_mode=enums.ParseMode.HTML
    )

# -------------------
# Cancel command
# -------------------

@Client.on_message(filters.private & filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    logger.info(f"Cancel command received from user {message.from_user.id}")
    
    # Also cancel batch conversation state
    if message.from_user.id in batch_conversation_state:
        del batch_conversation_state[message.from_user.id]
    
    if batch_temp.IS_BATCH.get(message.from_user.id) == False:
        batch_temp.IS_BATCH[message.from_user.id] = True
        await message.reply_text("❌ **Batch Process Cancelled Successfully.**", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text("**⚠️ No Active Batch Process To Cancel.**", parse_mode=enums.ParseMode.HTML)

# -------------------
# Interactive Batch Conversation Handler
# -------------------

def extract_message_ids(link: str):
    """Extract message ID(s) from a Telegram link"""
    if "https://t.me/" in link:
        datas = link.split("/")
        temp = datas[-1].replace("?single", "")
        
        if "-" in temp:
            parts = temp.split("-")
            from_id = int(parts[0].strip())
            to_id = int(parts[1].strip())
            return from_id, to_id
        else:
            msg_id = int(temp.strip())
            return msg_id, msg_id
    return None, None

def get_channel_info(link: str):
    """Get channel username or ID from link"""
    if "https://t.me/c/" in link:
        datas = link.split("/")
        return "private", datas[4]
    elif "https://t.me/b/" in link:
        datas = link.split("/")
        return "batch", datas[4]
    elif "https://t.me/" in link:
        datas = link.split("/")
        return "public", datas[3]
    return None, None

@Client.on_message(filters.private & filters.text & ~filters.regex("^/"))
async def batch_conversation_handler(client: Client, message: Message):
    """Handle interactive batch conversation"""
    user_id = message.from_user.id
    
    # Check if user is in batch conversation state
    if user_id not in batch_conversation_state:
        return
    
    state = batch_conversation_state[user_id]
    link = message.text.strip()
    
    if "https://t.me/" not in link:
        await message.reply_text(
            "**⚠️ Please send a valid Telegram link.**\n"
            "Example: `https://t.me/c/123456789/10`",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    if state == BATCH_STATE["WAITING_START_LINK"]:
        # Store start link and ask for end link
        start_id, _ = extract_message_ids(link)
        channel_type, channel_id = get_channel_info(link)
        
        if start_id is None:
            await message.reply_text(
                "**⚠️ Could not extract message ID from link.**\n"
                "Please send a valid Telegram link.",
                parse_mode=enums.ParseMode.HTML
            )
            return
        
        # Store conversation state
        batch_conversation_state[user_id] = {
            "state": BATCH_STATE["WAITING_END_LINK"],
            "start_link": link,
            "start_id": start_id,
            "channel_type": channel_type,
            "channel_id": channel_id
        }
        
        await message.reply_text(
            f"**✅ Start Link Received!**\n\n"
            f"**📎 Start Message ID:** `{start_id}`\n\n"
            f"**Now send the END link** (last message you want to download):\n"
            f"Example: `https://t.me/c/123456789/100`\n\n"
            f"Send /cancel to cancel the batch process.",
            parse_mode=enums.ParseMode.HTML
        )
        
    elif state["state"] == BATCH_STATE["WAITING_END_LINK"]:
        # Process both links and start batch
        end_id, _ = extract_message_ids(link)
        
        if end_id is None:
            await message.reply_text(
                "**⚠️ Could not extract message ID from link.**\n"
                "Please send a valid Telegram link.",
                parse_mode=enums.ParseMode.HTML
            )
            return
        
        start_id = state["start_id"]
        
        # Validate range
        if end_id < start_id:
            await message.reply_text(
                f"**⚠️ End ID ({end_id}) is less than Start ID ({start_id})**\n"
                "Please send a valid end link.",
                parse_mode=enums.ParseMode.HTML
            )
            return
        
        # Clear conversation state and start batch
        del batch_conversation_state[user_id]
        
        # Start the batch process
        await start_batch_process(
            client, message, 
            state["channel_type"], 
            state["channel_id"], 
            start_id, 
            end_id
        )

async def start_batch_process(client, message, channel_type, channel_id, from_id, to_id):
    """Start the actual batch processing"""
    user_id = message.from_user.id
    
    # Check if batch is already running
    if batch_temp.IS_BATCH.get(user_id) == False:
        await message.reply_text(
            "**⚠️ One Task Is Already Processing. Wait For Complete It.\nIf You Want To Cancel This Task Then Use - /cancel**",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Check login
    user_data = await db.get_session(user_id)
    if user_data is None:
        await message.reply_text(
            "**🚪 For Downloading Restricted Content You Have To /login First.**",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Initialize batch
    batch_temp.IS_BATCH[user_id] = False
    total_msgs = to_id - from_id + 1
    
    # Send start confirmation
    start_msg = await message.reply_text(
        f"**📦 Interactive Batch Processing Started!**\n\n"
        f"**📋 Range:** {from_id} - {to_id} ({total_msgs} messages)\n"
        f"**🔄 Status:** Processing...",
        parse_mode=enums.ParseMode.HTML
    )
    
    # Connect to user client
    try:
        acc = Client("saverestricted", session_string=user_data, api_hash=API_HASH, api_id=API_ID, in_memory=True)
        await acc.connect()
    except (AuthKeyUnregistered, UserDeactivated, UserDeactivatedBan) as e:
        batch_temp.IS_BATCH[user_id] = True
        await db.set_session(user_id, None)
        await message.reply(f"**🚪 Your Login Session Invalid/Expired. Please /login again.**\nError: {e}")
        await start_msg.edit("**❌ Batch Stopped: Session Expired**", parse_mode=enums.ParseMode.HTML)
        return
    except Exception:
        batch_temp.IS_BATCH[user_id] = True
        await message.reply("**🚪 Your Login Session Error. So /logout First Then Login Again By - /login**")
        await start_msg.edit("**❌ Batch Stopped: Session Error**", parse_mode=enums.ParseMode.HTML)
        return
    
    # Process each message
    success_count = 0
    fail_count = 0
    
    for msgid in range(from_id, to_id + 1):
        if batch_temp.IS_BATCH.get(user_id):
            break
        
        # Update progress
        current_num = msgid - from_id + 1
        percentage = (current_num / total_msgs) * 100 if total_msgs > 0 else 0
        
        try:
            await start_msg.edit(
                f"**📦 Batch Processing**\n"
                f"**📋 Progress:** {current_num}/{total_msgs} ({percentage:.1f}%)\n"
                f"**✅ Success:** {success_count} | **❌ Failed:** {fail_count}\n"
                f"**🔄 Processing ID:** {msgid}",
                parse_mode=enums.ParseMode.HTML
            )
        except:
            pass
        
        # Handle content based on channel type
        try:
            if channel_type == "private":
                chatid = int("-100" + channel_id)
                await handle_private(client, acc, message, chatid, msgid)
            elif channel_type == "batch":
                await handle_private(client, acc, message, channel_id, msgid)
            else:  # public
                await handle_private(client, acc, message, channel_id, msgid)
            success_count += 1
        except Exception as e:
            logger.error(f"Error processing message {msgid}: {e}")
            fail_count += 1
        
        await asyncio.sleep(2)
    
    # Cleanup
    batch_temp.IS_BATCH[user_id] = True
    
    try:
        await acc.disconnect()
    except:
        pass
    
    # Send completion message
    await start_msg.edit(
        f"**✅ Batch Processing Completed!**\n\n"
        f"**📊 Summary:**\n"
        f"• **Total Messages:** {total_msgs}\n"
        f"• **Success:** {success_count}\n"
        f"• **Failed:** {fail_count}\n\n"
        f"**Use /batch to start a new batch process.**",
        parse_mode=enums.ParseMode.HTML
    )

# -------------------
# Handle incoming messages
# -------------------

@Client.on_message(filters.private & filters.text & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" in message.text:
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

# -------------------
# Handle private content
# -------------------

async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int):
    try:
        msg: Message = await acc.get_messages(chatid, msgid)
    except (AuthKeyUnregistered, UserDeactivated, UserDeactivatedBan) as e:
        batch_temp.IS_BATCH[message.from_user.id] = True
        await db.set_session(message.from_user.id, None)
        await client.send_message(message.chat.id, f"Session Token Invalid/Expired. Please /login again.\nError: {e}")
        return
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
            return
        except Exception as e2:
            logger.error(f"Retry failed: {e2}")
            return
# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official

    if msg.empty:
        return

    msg_type = get_message_type(msg)
    if not msg_type:
        return

    chat = message.chat.id
    if batch_temp.IS_BATCH.get(message.from_user.id):
        return

    if "Text" == msg_type:
        try:
            await client.send_message(chat, f"**__{msg.text}__**", entities=msg.entities, reply_to_message_id=message.id,
                                      parse_mode=enums.ParseMode.HTML)
            return
        except Exception as e:
            logger.error(f"Error sending text message: {e}")
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id,
                                          parse_mode=enums.ParseMode.HTML)
            return

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
        return

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
        return

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
