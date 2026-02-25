# -*- coding: utf-8 -*-
"""
Professional Telegram Bot for Free Fire Emote Execution with Direct API Calls
No Queue System - Instant Responses
"""

import os
import logging
import re
import json
import time
import threading
from datetime import datetime, timedelta

import requests
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# ================== CONFIGURATION ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = '8319416683:AAHYb7p3NwCNr0Z8WOjwoO4B9VIOHar1mqs'
EMOTE_API_BASE = 'https://bigbullev.onrender.com'
OWNER_ID = 5895145916
ADMIN_USERNAME = "@bigbullabhi8809"
DISPLAY_NAME = "🐂 BIGBULL EMOTE BOT"
MINI_APP_URL = "http://t.me/emotebbcbot/bigbullemote"

# Channels for verification
CHANNELS = [
    {"link": "https://t.me/+B8Kp7JSR7bRlYjE1", "id": -1003025589345, "name": "BBC Channel 1"},
    {"link": "https://t.me/bbcheatsofc", "id": -1003830733827, "name": "BBC Channel 2"},
    {"link": "https://t.me/bigbullchats", "id": -1003783678225, "name": "BBC Channel 3"}
]

REQUEST_TIMEOUT = 8
LONG_POLLING_TIMEOUT = 15
RETRY_DELAY = 3
VERIFICATION_RESET_DAYS = 7  # Reset verification every 7 days

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ================== JSON DATABASE ==================
class JSONDatabase:
    def __init__(self, filename='verified_users.json'):
        self.filename = filename
        self.lock = threading.Lock()
        self.data = self._load_data()
        
    def _load_data(self) -> dict:
        """Load data from JSON file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    if 'users' not in data:
                        data['users'] = []
                    if 'last_reset' not in data:
                        data['last_reset'] = datetime.now().isoformat()
                    return data
            else:
                return {
                    'users': [],
                    'last_reset': datetime.now().isoformat(),
                    'total_verified': 0
                }
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            return {
                'users': [],
                'last_reset': datetime.now().isoformat(),
                'total_verified': 0
            }
    
    def _save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def check_reset_needed(self) -> bool:
        """Check if 7 days have passed since last reset"""
        last_reset = datetime.fromisoformat(self.data['last_reset'])
        days_passed = (datetime.now() - last_reset).days
        return days_passed >= VERIFICATION_RESET_DAYS
    
    def reset_verification(self):
        """Reset verification data"""
        with self.lock:
            self.data['users'] = []
            self.data['last_reset'] = datetime.now().isoformat()
            self.data['total_verified'] = 0
            self._save_data()
            logger.info(f"🔄 Verification reset after {VERIFICATION_RESET_DAYS} days")
    
    def add_user(self, user_id: int):
        """Add verified user"""
        with self.lock:
            if user_id not in self.data['users']:
                self.data['users'].append(user_id)
                self.data['total_verified'] = len(self.data['users'])
                self._save_data()
                return True
        return False
    
    def remove_user(self, user_id: int):
        """Remove verified user"""
        with self.lock:
            if user_id in self.data['users']:
                self.data['users'].remove(user_id)
                self.data['total_verified'] = len(self.data['users'])
                self._save_data()
                return True
        return False
    
    def is_verified(self, user_id: int) -> bool:
        """Check if user is verified"""
        if self.check_reset_needed():
            self.reset_verification()
        
        with self.lock:
            return user_id in self.data['users']
    
    def get_all_users(self) -> list:
        """Get all verified users"""
        with self.lock:
            return self.data['users'].copy()
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        with self.lock:
            return {
                'total_verified': len(self.data['users']),
                'last_reset': self.data['last_reset'],
                'days_until_reset': max(0, VERIFICATION_RESET_DAYS - (datetime.now() - datetime.fromisoformat(self.data['last_reset'])).days)
            }

# Initialize database
db = JSONDatabase()

# ================== UI ELEMENTS ==================
EMOJIS = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'stats': '📊',
    'fire': '🔥',
    'bull': '🐂',
    'gear': '⚙️',
    'check': '✅',
    'cross': '❌',
    'clock': '⏰',
    'speed': '⚡',
    'target': '🎯',
    'team': '👥',
    'user': '👤',
    'emote': '🎭',
    'admin': '👑',
    'channel': '📢',
    'link': '🔗',
    'web': '🌐',
    'support': '💬',
    'mini': '🎮',
    'group': '👥',
    'private': '🤫',
    'five': '5️⃣',
    'invite': '✉️'
}

def create_success_msg(title, content):
    return f"{EMOJIS['success']} *{title}*\n\n{content}"

def create_error_msg(title, content):
    return f"{EMOJIS['error']} *{title}*\n\n{content}"

def create_processing_msg(action):
    return f"""╔══════════════════════╗
║  {EMOJIS['speed']} *PROCESSING*  ║
╚══════════════════════╝

{action}

{EMOJIS['clock']} *Please wait...*"""

def create_success_result(team_code, uid, emote_code, api_response):
    # Extract message from API response
    api_message = api_response.get('message', 'Command executed successfully')
    
    return f"""╔══════════════════════╗
║  {EMOJIS['success']} *EMOTE SUCCESSFUL*  ║
╚══════════════════════╝

{EMOJIS['team']} *Team:* `{team_code}`
{EMOJIS['user']} *UID:* `{uid}`
{EMOJIS['emote']} *Emote:* `{emote_code}`

{EMOJIS['check']} *Status:* {api_message}

{EMOJIS['bull']} *BigBull Emote Bot*"""

def create_five_success_result(uid, api_response):
    # Extract message from API response
    api_message = api_response.get('message', '5-player group created successfully')
    
    return f"""╔══════════════════════╗
║  {EMOJIS['five']} *5-PLAYER GROUP*  ║
╚══════════════════════╝

{EMOJIS['user']} *UID:* `{uid}`

{EMOJIS['check']} *Status:* {api_message}

{EMOJIS['bull']} *BigBull Emote Bot*"""

def create_error_result(command, params, error):
    return f"""╔══════════════════════╗
║  {EMOJIS['error']} *COMMAND FAILED*  ║
╚══════════════════════╝

{EMOJIS['target']} *Command:* `{command}`
{EMOJIS['gear']} *Params:* `{params}`

{EMOJIS['warning']} *Error:* {error}

{EMOJIS['bull']} *BigBull Emote Bot*"""

def create_welcome_msg():
    return f"""╔══════════════════════════════╗
║  {EMOJIS['bull']} *BIGBULL EMOTE BOT* {EMOJIS['bull']}  ║
╚══════════════════════════════╝

{EMOJIS['fire']} *COMMANDS:*

{EMOJIS['emote']} `/emote <teamcode> <uid> <code>`
Example: `/emote 1234567 123456789 909042007`

{EMOJIS['five']} `/5 <uid>`
Example: `/5 123456789`

{EMOJIS['gear']} *FEATURES:*
• Instant execution - No waiting
• Auto team leave after emote
• 5-player group creator
• Real-time responses

{EMOJIS['admin']} *Owner:* {ADMIN_USERNAME}"""

def create_verification_msg(channels_text):
    return f"""╔══════════════════════════════╗
║  {EMOJIS['warning']} *VERIFICATION REQUIRED*  ║
╚══════════════════════════════╝

{EMOJIS['channel']} *Please join these channels:*
{channels_text}

{EMOJIS['check']} *After joining, click 'Verified' below*

Note: Verification resets every {VERIFICATION_RESET_DAYS} days."""

# ================== BOT INITIALIZATION ==================
bot = TeleBot(BOT_TOKEN)

# ================== VERIFICATION FUNCTIONS ==================
def check_user_channels(user_id):
    """Check if user has joined all required channels"""
    not_joined = []
    
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel["id"], user_id)
            if member.status in ['left', 'kicked']:
                not_joined.append(channel)
        except Exception as e:
            logger.error(f"Error checking channel {channel['name']}: {e}")
            not_joined.append(channel)
    
    return not_joined

def handle_unverified_user(message):
    """Handle unverified user - show channel join message"""
    user_id = message.from_user.id
    not_joined = check_user_channels(user_id)
    
    if not_joined:
        channels_text = "\n".join([f"• {ch['name']}" for ch in not_joined])
        bot.reply_to(
            message,
            create_verification_msg(channels_text),
            parse_mode='Markdown',
            reply_markup=get_channels_markup()
        )
    else:
        # User has joined all channels but not verified in DB
        db.add_user(user_id)
        
        bot.reply_to(
            message,
            create_welcome_msg() + f"\n\n{EMOJIS['check']} *Verification valid for {VERIFICATION_RESET_DAYS} days*",
            parse_mode='Markdown',
            reply_markup=get_main_markup()
        )

def verification_required(func):
    """Decorator to check verification before allowing command"""
    def wrapper(message: Message, *args, **kwargs):
        user_id = message.from_user.id
        
        if not db.is_verified(user_id):
            handle_unverified_user(message)
            return
        
        return func(message, *args, **kwargs)
    
    return wrapper

# ================== UTILITY FUNCTIONS ==================
def validate_bot_token():
    try:
        bot.get_me()
        logger.info("✅ Bot token validated")
        return True
    except Exception as e:
        logger.error(f"❌ Invalid bot token: {e}")
        return False

def get_channels_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    for channel in CHANNELS:
        markup.add(InlineKeyboardButton(
            f"{EMOJIS['channel']} Join {channel['name']}", 
            url=channel['link']
        ))
    markup.add(InlineKeyboardButton(
        f"{EMOJIS['check']} Verified", 
        callback_data="verify_channels"
    ))
    return markup

def get_main_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"{EMOJIS['web']} MAIN CHANNEL", url="https://t.me/+B8Kp7JSR7bRlYjE1"),
        InlineKeyboardButton(f"{EMOJIS['support']} TCP PANEL", url="https://t.me/bbcisbackbot")
    )
    markup.add(
        InlineKeyboardButton(f"{EMOJIS['admin']} Owner", url=f"tg://user?id={OWNER_ID}"),
        InlineKeyboardButton(f"{EMOJIS['mini']} EMOTE WEB", url=MINI_APP_URL)
    )
    return markup

# ================== API CALL FUNCTIONS ==================
def call_join_emote_api(team_code, uid, emote_code):
    """Call the join-emote-leave API endpoint"""
    try:
        url = f"{EMOTE_API_BASE}/join-emote-leave"
        params = {
            'teamcode': team_code,
            'uid': uid,
            'emote_code': emote_code
        }
        
        logger.info(f"📡 Calling API: {url} with params {params}")
        
        response = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        return response.json()
        
    except requests.Timeout:
        logger.error("API request timeout")
        return {'success': False, 'message': 'Request timeout'}
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        return {'success': False, 'message': f'API Error: {str(e)}'}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {'success': False, 'message': f'System Error: {str(e)}'}

def call_five_api(uid):
    """Call the /5 API endpoint"""
    try:
        url = f"{EMOTE_API_BASE}/5"
        params = {'uid': uid}
        
        logger.info(f"📡 Calling API: {url} with uid {uid}")
        
        response = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        return response.json()
        
    except requests.Timeout:
        logger.error("API request timeout")
        return {'success': False, 'message': 'Request timeout'}
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        return {'success': False, 'message': f'API Error: {str(e)}'}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {'success': False, 'message': f'System Error: {str(e)}'}

# ================== CALLBACK HANDLERS ==================
@bot.callback_query_handler(func=lambda call: call.data == "verify_channels")
def verify_channels_callback(call):
    user_id = call.from_user.id
    not_joined = check_user_channels(user_id)
    
    if not not_joined:
        db.add_user(user_id)
        
        bot.edit_message_text(
            create_success_msg("✅ VERIFICATION SUCCESSFUL", 
                f"You can now use the bot!\n\n"
                f"{EMOJIS['clock']} *Verification valid for {VERIFICATION_RESET_DAYS} days*"),
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=get_main_markup()
        )
    else:
        bot.answer_callback_query(call.id, "❌ Please join all channels first!", show_alert=True)

# ================== COMMAND HANDLERS ==================
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    
    if db.is_verified(user_id):
        stats = db.get_stats()
        days_left = stats['days_until_reset']
        
        welcome_with_reset = create_welcome_msg() + f"\n\n{EMOJIS['clock']} *Verification expires in {days_left} days*"
        
        bot.reply_to(
            message, 
            welcome_with_reset, 
            parse_mode='Markdown',
            reply_markup=get_main_markup()
        )
    else:
        not_joined = check_user_channels(user_id)
        
        if not_joined:
            channels_text = "\n".join([f"• {ch['name']}" for ch in not_joined])
            bot.reply_to(
                message, 
                create_verification_msg(channels_text), 
                parse_mode='Markdown',
                reply_markup=get_channels_markup()
            )
        else:
            db.add_user(user_id)
            stats = db.get_stats()
            days_left = stats['days_until_reset']
            
            welcome_with_reset = create_welcome_msg() + f"\n\n{EMOJIS['clock']} *Verification expires in {days_left} days*"
            
            bot.reply_to(
                message, 
                welcome_with_reset, 
                parse_mode='Markdown',
                reply_markup=get_main_markup()
            )

@bot.message_handler(commands=['help'])
def help_message(message):
    start_message(message)

@bot.message_handler(commands=['emote'])
@verification_required
def handle_emote(message):
    user_id = message.from_user.id
    
    try:
        args = message.text.split()
        if len(args) != 4:
            bot.reply_to(
                message, 
                create_error_msg(
                    "INVALID COMMAND", 
                    "Usage: `/emote <teamcode> <uid> <emote_code>`\nExample: `/emote 1234567 123456789 909042007`"
                ), 
                parse_mode='Markdown'
            )
            return
        
        team_code = args[1].strip()
        uid = args[2].strip()
        emote_code = args[3].strip()
        
        # Validations
        if not re.match(r'^\d{7}$', team_code):
            bot.reply_to(
                message, 
                create_error_msg("INVALID TEAM CODE", "Team code must be exactly 7 digits."), 
                parse_mode='Markdown'
            )
            return
        
        if not re.match(r'^\d+$', uid):
            bot.reply_to(
                message, 
                create_error_msg("INVALID UID", "UID must contain only numbers."), 
                parse_mode='Markdown'
            )
            return
        
        if not re.match(r'^\d+$', emote_code):
            bot.reply_to(
                message, 
                create_error_msg("INVALID EMOTE CODE", "Emote code must contain only numbers."), 
                parse_mode='Markdown'
            )
            return
        
        # Send processing message
        processing_msg = bot.reply_to(
            message,
            create_processing_msg(f"{EMOJIS['emote']} Sending emote to UID {uid}..."),
            parse_mode='Markdown'
        )
        
        # Call API directly
        api_response = call_join_emote_api(team_code, uid, emote_code)
        
        # Check response
        if api_response.get('success') == True:
            # Success
            bot.edit_message_text(
                create_success_result(team_code, uid, emote_code, api_response),
                processing_msg.chat.id,
                processing_msg.message_id,
                parse_mode='Markdown'
            )
            logger.info(f"✅ Emote success: User {user_id} | Team {team_code} | UID {uid}")
        else:
            # Failed
            error_msg = api_response.get('message', 'Unknown error')
            bot.edit_message_text(
                create_error_result("/emote", f"{team_code} {uid} {emote_code}", error_msg),
                processing_msg.chat.id,
                processing_msg.message_id,
                parse_mode='Markdown'
            )
            logger.info(f"❌ Emote failed: {error_msg}")
        
    except Exception as e:
        logger.error(f"Error in handle_emote: {e}")
        bot.reply_to(
            message, 
            create_error_msg("SYSTEM ERROR", "Something went wrong. Try again."), 
            parse_mode='Markdown'
        )

@bot.message_handler(commands=['5'])
@verification_required
def handle_five(message):
    user_id = message.from_user.id
    
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(
                message, 
                create_error_msg(
                    "INVALID COMMAND", 
                    "Usage: `/5 <uid>`\nExample: `/5 123456789`"
                ), 
                parse_mode='Markdown'
            )
            return
        
        uid = args[1].strip()
        
        # Validation
        if not re.match(r'^\d+$', uid):
            bot.reply_to(
                message, 
                create_error_msg("INVALID UID", "UID must contain only numbers."), 
                parse_mode='Markdown'
            )
            return
        
        # Send processing message
        processing_msg = bot.reply_to(
            message,
            create_processing_msg(f"{EMOJIS['five']} Creating 5-player group for UID {uid}..."),
            parse_mode='Markdown'
        )
        
        # Call API directly
        api_response = call_five_api(uid)
        
        # Check response
        if api_response.get('success') == True:
            # Success
            bot.edit_message_text(
                create_five_success_result(uid, api_response),
                processing_msg.chat.id,
                processing_msg.message_id,
                parse_mode='Markdown'
            )
            logger.info(f"✅ 5-player group success: User {user_id} | UID {uid}")
        else:
            # Failed
            error_msg = api_response.get('message', 'Unknown error')
            bot.edit_message_text(
                create_error_result("/5", uid, error_msg),
                processing_msg.chat.id,
                processing_msg.message_id,
                parse_mode='Markdown'
            )
            logger.info(f"❌ 5-player group failed: {error_msg}")
        
    except Exception as e:
        logger.error(f"Error in handle_five: {e}")
        bot.reply_to(
            message, 
            create_error_msg("SYSTEM ERROR", "Something went wrong. Try again."), 
            parse_mode='Markdown'
        )

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    if message.from_user.id != OWNER_ID:
        return
    
    db_stats = db.get_stats()
    
    stats_msg = f"""📊 *BOT STATISTICS*

👥 *Verified Users:* {db_stats['total_verified']}

📅 *Verification Reset:*
• Last Reset: {db_stats['last_reset'][:10]}
• Days Left: {db_stats['days_until_reset']}

⚡ *Direct API Mode - No Queue*
    """
    
    bot.reply_to(
        message, 
        stats_msg, 
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != OWNER_ID:
        return
    
    db_stats = db.get_stats()
    
    admin_msg = f"""👑 *ADMIN PANEL*

📊 *SYSTEM STATUS:*
• Verified Users: {db_stats['total_verified']}

📅 *Verification:*
• Reset Every: {VERIFICATION_RESET_DAYS} days
• Last Reset: {db_stats['last_reset'][:10]}
• Days Until Reset: {db_stats['days_until_reset']}

⚡ *Mode:* Direct API (No Queue)
🔗 *API Base:* {EMOTE_API_BASE}

🔧 *Commands:*
/stats - View stats
    """
    
    bot.reply_to(
        message, 
        admin_msg, 
        parse_mode='Markdown'
    )

# ================== MAIN ==================
if __name__ == '__main__':
    if not validate_bot_token():
        raise SystemExit(1)
    
    logger.info(f"🤖 Starting {DISPLAY_NAME}")
    logger.info(f"⚡ Mode: Direct API (No Queue)")
    logger.info(f"📡 API: {EMOTE_API_BASE}")
    logger.info(f"📢 Mini App: {MINI_APP_URL}")
    logger.info(f"📅 Verification Reset: Every {VERIFICATION_RESET_DAYS} days")
    logger.info(f"➕ New Command: /5 - Create 5-player group")
    
    # Check if reset needed on startup
    if db.check_reset_needed():
        db.reset_verification()
        logger.info(f"🔄 Initial verification reset completed")
    
    # Start verification reset checker
    def reset_check_loop():
        while True:
            time.sleep(3600)  # Check every hour
            if db.check_reset_needed():
                db.reset_verification()
                logger.info(f"🔄 Automatic verification reset completed")
    
    reset_thread = threading.Thread(target=reset_check_loop, daemon=True)
    reset_thread.start()
    
    # Start bot
    while True:
        try:
            bot.infinity_polling(timeout=LONG_POLLING_TIMEOUT)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(RETRY_DELAY)