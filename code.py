
import logging
import random
import time
import os
from telegram import Update, InputMediaPhoto, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext
import json

BOT_TOKEN = "7748076089:AAGuiDwnRgDNvlcwQcegfaeyg-m0jQT6KzQ"  # Replace with your actual bot token
AUTHORIZED_USERS = "authorized_users.json"  # File to store authorized users
KEYS = "keys.json"
QR_DIR = "qr_codes" # Directory to store qr codes
DEFAULT_QR_NAME = "default_qr.png"
ADMIN_ID = 6830887977

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG #DEBUG level logging
)
logger = logging.getLogger(__name__)  # Create a logger object


def load_data():
    global authorized_users, keys
    try:
        with open(AUTHORIZED_USERS, "r") as f:
            authorized_users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        authorized_users = []

    try:
        with open(KEYS, "r") as f:
            keys = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        keys = {}

def save_data():
    with open(AUTHORIZED_USERS, "w") as f:
        json.dump(authorized_users, f)
    with open(KEYS, "w") as f:
        json.dump(keys, f)

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Invalid arguments. Use /genkey <amount> <hours/days>")
        return
    
    try:
        amount = int(context.args[0])
        duration_type = context.args[1].lower()
        if duration_type not in ["hours", "days"]:
            await update.message.reply_text("Invalid duration type. Use 'hours' or 'days'.")
            return
    except ValueError:
         await update.message.reply_text("Invalid amount. It should be a number.")
         return
     
    
    key = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(10))
    
    if duration_type == "hours":
       expiry = time.time() + (amount * 3600)
    elif duration_type == "days":
       expiry = time.time() + (amount * 86400)
    
    keys[key] = expiry
    save_data()
    await update.message.reply_text(f"Generated key: {key} with expiry timestamp: {expiry}")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Invalid arguments. Use /redeem <key>")
        return

    key = context.args[0]

    if key in keys and keys[key] > time.time():
      if update.effective_user.id not in authorized_users:
            authorized_users.append(update.effective_user.id)
            save_data()
            await update.message.reply_text("Key redeemed successfully. You are now authorized.",reply_markup=ReplyKeyboardRemove())
      else:
          await update.message.reply_text("You are already authorized.", reply_markup=ReplyKeyboardRemove())
      
      
    elif key in keys and keys[key] <= time.time():
        await update.message.reply_text("This key is expired")
    else:
        await update.message.reply_text("Invalid Key")

async def allusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if authorized_users:
       users_str = "\n".join(str(user_id) for user_id in authorized_users)
       await update.message.reply_text(f"Authorized users:\n{users_str}")
    else:
       await update.message.reply_text("No authorized user found.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if not context.args:
        await update.message.reply_text("Please provide a message to broadcast.")
        return

    message = " ".join(context.args)

    for user_id in authorized_users:
       try:
          await context.bot.send_message(chat_id=user_id, text=message)
       except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
    
    await update.message.reply_text("Message broadcasted successfully.")


async def bgmi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in authorized_users:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if len(context.args) != 3:
        await update.message.reply_text("Invalid arguments. Use /bgmi <target_ip> <port> <duration>")
        return
    target_ip = context.args[0]
    port = context.args[1]
    duration = context.args[2]

    await update.message.reply_text(f"Flooding parameters set: \n Target IP: {target_ip}\n Port: {port}\n Duration: {duration}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in authorized_users:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    await update.message.reply_text("Flooding process started.")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in authorized_users:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    await update.message.reply_text("Flooding process stopped.")

# New Upload command
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.photo:
        await update.message.reply_text("Please upload a photo.")
        return
    
    if not os.path.exists(QR_DIR):
      os.makedirs(QR_DIR)

    file_id = update.message.photo[-1].file_id
    new_file = await context.bot.get_file(file_id)
    file_path = os.path.join(QR_DIR, DEFAULT_QR_NAME)
    try:
      await new_file.download_to_drive(file_path)
      await update.message.reply_text(f"QR code uploaded successfully!\n Path: {file_path}")
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        await update.message.reply_text("Error while uploading QR code.")


# New Remove command
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Please provide the user ID to remove.")
        return

    try:
        user_id_to_remove = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID. It should be a number.")
        return
    
    if user_id_to_remove in authorized_users:
        authorized_users.remove(user_id_to_remove)
        save_data()
        await update.message.reply_text(f"User {user_id_to_remove} has been removed.")
    else:
        await update.message.reply_text(f"User {user_id_to_remove} not found in authorized users.")


#New buy command

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
  
    if not os.path.exists(os.path.join(QR_DIR, DEFAULT_QR_NAME)):
      await update.message.reply_text("QR code is not uploaded by Admin yet, please try again later.")
      return

    with open(os.path.join(QR_DIR, DEFAULT_QR_NAME), 'rb') as photo:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo,
            caption=(
                "Pay and Send SS (Screenshot).\n"
                "1 day = 100\n"
                "2 days = 160\n"
                "3 days = 210\n"
                "7 days = 500\n\n"
                "After payment send screenshot and wait some time owner see and give key"
            )
        )
    
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  
    keyboard = [
        ["/buy"]
    ]

    if update.effective_user.id in authorized_users:
        await update.message.reply_text("Welcome Back!", reply_markup=ReplyKeyboardRemove())
    else:
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Welcome to the Bot! Please /buy access.", reply_markup=reply_markup)
    
    

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "Admin Commands:\n"
        "/genkey <amount> <hours/days> - Generate a key with a specified validity period.\n"
        "/allusers - Show all authorized users.\n"
        "/broadcast <message> - Broadcast a message to all authorized users.\n"
        "/remove <user_id> - Remove an authorized user.\n"
        "/upload - Upload a new payment QR code\n\n"
        "User Commands:\n"
        "/redeem <key> - Redeem a key to gain access.\n"
         "/buy - Purchase access.\n"
        "/bgmi <target_ip> <port> <duration> - Set the flooding parameters.\n"
        "/start - Start the flooding process.\n"
        "/stop - Stop the flooding process.\n"
    )
    await update.message.reply_text(response)

def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("allusers", allusers))
    application.add_handler(CommandHandler("bgmi", bgmi))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("remove", remove))  # Added remove handler
    application.add_handler(CommandHandler("upload", upload)) # Added upload handler
    application.add_handler(CommandHandler("buy", buy)) # Added buy handler
    application.add_handler(CommandHandler("start", start_command)) # Modified start handler
    application.add_handler(CommandHandler("help", help_command))

    load_data()
    application.run_polling()

if __name__ == '__main__':
    main()
#zaher_ddos
