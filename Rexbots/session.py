# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait
)
from config import API_ID, API_HASH
from database.db import db

SESSION_STRING_SIZE = 351

# State Dictionary
# Structure: {user_id: {"step": "WAITING_PHONE" | "WAITING_CODE" | "WAITING_PASSWORD", "data": {...}}}
LOGIN_STATE = {}

@Client.on_message(filters.private & filters.command("login"))
async def login_start(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await db.get_session(user_id)
    if user_data is not None:
        await message.reply("**__You Are Already Logged In 🤓\n\nFirst /logout Your Old Session. Then Do /login Again !!__ 🔑**")
        return 

    # Init State
    LOGIN_STATE[user_id] = {"step": "WAITING_PHONE", "data": {}}
    await message.reply_text(
        "<b>__Please Send Your Phone Number Which Includes Country Code__ 📊</b>\n\n<b>__Example:__</b> <code>+91987654321</code>\n\nSend /cancel to cancel."
    )

@Client.on_message(filters.private & filters.command("logout"))
async def logout(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in LOGIN_STATE:
        del LOGIN_STATE[user_id]
    
    await db.set_session(user_id, session=None)
    await message.reply("**__Logout Successfully__ 🚪**")

# Custom Filter to check if user is in login state
async def check_login_state(_, __, message):
    return message.from_user.id in LOGIN_STATE

login_state_filter = filters.create(check_login_state)

@Client.on_message(filters.private & filters.text & login_state_filter & ~filters.regex("^/"))
async def login_handler(bot: Client, message: Message):
    user_id = message.from_user.id
    # No need to check "if user_id not in LOGIN_STATE" again, filter did it.

    state = LOGIN_STATE[user_id]
    step = state["step"]
    text = message.text

    if step == "WAITING_PHONE":
        phone_number = text.replace(" ", "")
        temp_client = Client(f"session_{user_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await temp_client.connect()
        
        await message.reply("**📩 __Sending OTP...__**")
        try:
            code = await temp_client.send_code(phone_number)
            state["data"]["client"] = temp_client
            state["data"]["phone"] = phone_number
            state["data"]["hash"] = code.phone_code_hash
            state["step"] = "WAITING_CODE"
            
            await message.reply(
                "**__Please Check for an OTP in Official Telegram Account. \n\n"
                "If OTP Is 12345, Please Send It As '12 345' (with space) or '12345'.__**\n\n"
                "Send /cancellogin to Cancel."
            )
            
            # Show success message after OTP is sent
            await message.reply("**✅ OTP Sent Successfully! Please check your Telegram app and enter the code.**")
# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official
            
        except PhoneNumberInvalid:
            await message.reply('**❌ __PHONE_NUMBER Is Invalid.__**')
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]
        except FloodWait as fw:
            wait_time = min(fw.x, 300)  # Cap wait time at 5 minutes
            await message.reply(f'**⏳ FloodWait detected! Please try again after {wait_time} seconds.**')
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]
        except FloodWait as fw:
            wait_time = min(fw.x, 300)  # Cap wait time at 5 minutes
            await message.reply(f'**⏳ FloodWait detected! Please try again after {wait_time} seconds.**')
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]
        except Exception as e:
            await message.reply(f'**❌ __Error: {e}__**')
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]

    elif step == "WAITING_CODE":
        phone_code = text.replace(" ", "")
        temp_client = state["data"]["client"]
        phone_number = state["data"]["phone"]
        phone_hash = state["data"]["hash"]

        try:
            await temp_client.sign_in(phone_number, phone_hash, phone_code)
            # Login Success!
            await finalize_login(bot, message, temp_client, user_id)
            
        except PhoneCodeInvalid:
            await message.reply('**❌ __OTP Is Invalid. Try Again.__**')
            # Don't delete state, let them try again
        except PhoneCodeExpired:
            await message.reply('**❌ __OTP Is Expired. Login Again.__**')
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]
        except SessionPasswordNeeded:
            state["step"] = "WAITING_PASSWORD"
            await message.reply('**__Two-step Verification Enabled. Please Provide the Password.__**\n\nSend /cancel to Cancel.')
        except Exception as e:
            await message.reply(f'**❌ __Error: {e}__**')
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]

    elif step == "WAITING_PASSWORD":
        password = text
        temp_client = state["data"]["client"]
        try:
            await temp_client.check_password(password=password)
            await finalize_login(bot, message, temp_client, user_id)
        except PasswordHashInvalid:
            await message.reply('**❌ __Invalid Password. Try Again.__**')
        except Exception as e:
            await message.reply(f'**❌ __Error: {e}__**')
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]

async def finalize_login(bot, message, temp_client, user_id):
    try:
        string_session = await temp_client.export_session_string()
        await temp_client.disconnect()
        
        await db.set_session(user_id, session=string_session)
        del LOGIN_STATE[user_id]
        
        await message.reply("<b>__Account Login Successfully ✅\n\nIf You Get Any Error Related To AUTH KEY Then /logout first and /login again.__</b>")
    except FloodWait as fw:
        wait_time = min(fw.x, 300)  # Cap wait time at 5 minutes
        await message.reply(f'<b>⏳ FloodWait detected during login finalization! Please try again after {wait_time} seconds.</b>')
        if user_id in LOGIN_STATE:
             del LOGIN_STATE[user_id]
    except Exception as e:
        await message.reply(f"<b>❌ __ERROR IN FINALIZING LOGIN: `{e}`__</b>")
        if user_id in LOGIN_STATE:
             del LOGIN_STATE[user_id]

@Client.on_message(filters.private & filters.command("cancellogin"))
async def cancel_login(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in LOGIN_STATE:
        state = LOGIN_STATE[user_id]
        if "data" in state and "client" in state["data"]:
             try:
                 await state["data"]["client"].disconnect()
             except:
                 pass
        del LOGIN_STATE[user_id]
        await message.reply('<b>❌ __Process Cancelled !!__</b>')
    # Let start.py handle /cancel for batch if appropriate, 
    # but filters shouldn't overlap too much if we check state.
    # The batch cancel in start.py doesn't check state, it just sets a flag.
    # That's fine, they can coexist.

# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official
