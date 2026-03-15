# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official



import os
import asyncio
import random
import time
import shutil
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
# Supported Telegram Reactions
# -------------------

REACTIONS = [
    "🤝", "😇", "🤗", "😍", "👍", "🎅", "😐", "🥰", "🤩",
    "😱", "🤣", "😘", "👏", "😛", "😈", "🎉", "⚡️", "🫡",
    "🤓", "😎", "🏆", "🔥", "🤭", "🌚", "🆒", "👻", "😁"
]

PROGRESS_BAR_DASHBOARD  = """\
<blockquote>
✦ <code>{bar}</code> • <b>{percentage:.1f}%</b><br>
››  <b>Speed</b> • <code>{speed}/s</code><br>
››  <b>Size</b> • <code>{current} / {total}</code><br>
››  <b>ETA</b> • <code>{eta}</code><br>
››  <b>Elapsed</b> • <code>{elapsed}</code>
</blockquote>
"""



# -------------------
# Download status
# -------------------

async def downstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r", encoding='utf-8') as downread:
                txt = downread.read()
            await client.edit_message_text(chat, message.id, f"📥 **Downloading...**\n\n{txt}")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)

# -------------------
# Upload status
# -------------------

async def upstatus(client, statusfile, message, chat):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r", encoding='utf-8') as upread:
                txt = upread.read()
            await client.edit_message_text(chat, message.id, f"📤 **Uploading...**\n\n{txt}")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)

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
    
    now = time.time()
    task_id = f"{message.id}{type}"
    last_time = progress.cache.get(task_id, 0)
    
    # Track start time for speed calc
    if not hasattr(progress, "start_time"):
        progress.start_time = {}
    if task_id not in progress.start_time:
        progress.start_time[task_id] = now
        
    # Update only every 3 seconds or if completed
    if (now - last_time) > 3 or current == total:
        try:
            percentage = current * 100 / total
            speed = current / (now - progress.start_time[task_id])
            eta = (total - current) / speed if speed > 0 else 0
            elapsed = now - progress.start_time[task_id]
            
            # Progress Bar
            filled_length = int(percentage / 10) # 10 blocks for 100%
            bar = '▰' * filled_length + '▱' * (10 - filled_length)
            
            status = PROGRESS_BAR_DASHBOARD.format(
                bar=bar,
                percentage=percentage,
                current=humanbytes(current),
                total=humanbytes(total),
                speed=humanbytes(speed),
                eta=TimeFormatter(eta * 1000),
                elapsed=TimeFormatter(elapsed * 1000)
            )
            
            with open(f'{message.id}{type}status.txt', "w", encoding='utf-8') as fileup:
                fileup.write(status)
                
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
            InlineKeyboardButton('📢 Official Channel', url='https://t.me/Hasjsgdkd_bot'),
            InlineKeyboardButton('👨‍💻 Developer', url='https://t.me/Hasjsgdkd_bot')
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
# Cancel command
# -------------------

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await message.reply_text("❌ Batch Process Cancelled Successfully.")

# -------------------
# Handle incoming messages
# -------------------

@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" in message.text:
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text(
                "One Task Is Already Processing. Wait For Complete It. If You Want To Cancel This Task Then Use - /cancel"
            )

        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        try:
            toID = int(temp[1].strip())
        except:
            toID = fromID

        batch_temp.IS_BATCH[message.from_user.id] = False

        is_private = "https://t.me/c/" in message.text
        is_batch = "https://t.me/b/" in message.text

        for msgid in range(fromID, toID + 1):
            if batch_temp.IS_BATCH.get(message.from_user.id):
                break
            
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
                await message.reply("**__For Downloading Restricted Content You Have To /login First.__**")
                batch_temp.IS_BATCH[message.from_user.id] = True
                return

            # 3. Connect User Client
            try:
                acc = Client("saverestricted", session_string=user_data, api_hash=API_HASH, api_id=API_ID, in_memory=True)
                await acc.connect()
            except (AuthKeyUnregistered, UserDeactivated, UserDeactivatedBan) as e:
                batch_temp.IS_BATCH[message.from_user.id] = True
                await db.set_session(message.from_user.id, None)
                return await message.reply(f"**__Your Login Session Invalid/Expired. Please /login again.__**\nError: {e}")
            except Exception:
                batch_temp.IS_BATCH[message.from_user.id] = True
                return await message.reply("**__Your Login Session Error. So /logout First Then Login Again By - /login__**")

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

            await asyncio.sleep(3)

        batch_temp.IS_BATCH[message.from_user.id] = True

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

    smsg = await client.send_message(message.chat.id, '**__Downloading 🚀__**', reply_to_message_id=message.id)
    
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
    caption = msg.caption if msg.caption else None
    
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
            "• 🗄 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 : <a href='https://www.mongodb.com/'>𝐌𝐨𝐧𝐠𝐨𝐃𝐁</a>\n"
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
