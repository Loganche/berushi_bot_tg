import os
import time
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load environment variables from .env file
load_dotenv()

# Enter your Telegram bot token here
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'dummy_token_text')
CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_NAME', 'dummy_channel_name_with_@')

# Define the function for handling the /start command
async def start(update: Update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text=f"Привет! Я бот отложки канала {CHANNEL_ID}.")


async def get_scheduled_messages_count(update: Update, context):
    # Get the scheduled messages for the channel
    scheduled_messages = len(context.job_queue.jobs())

    # Send a message with the number of scheduled messages
    await context.bot.send_message(chat_id=update.message.chat_id, text=f"В канале {CHANNEL_ID} сейчас {scheduled_messages} отложенных сообщений.")


# Define the function for handling image messages
async def schedule_image(update: Update, context):
    # Get the file_id of the received image
    file_id = update.message.photo[-1].file_id
    
    messages = await context.bot.get_updates(limit=1)
    logging.info(messages)
    last_message_time = await messages[0].date.timestamp()
    
    # Schedule a message to send the image in 30 minutes
    logging.info("shedule_image()")
    context.job_queue.run_once(send_scheduled_image_after_last_message, 30*60, data=(file_id, last_message_time), chat_id=CHANNEL_ID)
    # context.job_queue.run_once(send_scheduled_image, interval=30*60)


# Define the function for sending the scheduled image after the last message sent to the channel
def send_scheduled_image_after_last_message(context):
    file_id, last_message_time = context.job.data
    
    # Get the current timestamp
    current_time = time.time()
    
    # Calculate the elapsed time since the last message was sent to the channel
    elapsed_time = current_time - last_message_time
    
    # If more than 30 minutes have elapsed since the last message was sent, send the image to the channel
    logging.info(f"elapsed_time = {elapsed_time}")
    if elapsed_time >= 30*60:
        context.bot.send_photo(chat_id=context.job.chat_id, photo=file_id)
    else:
        # If less than 30 minutes have elapsed since the last message was sent, schedule another message to send the image later
        logging.info(f"send_scheduled_image_after_last_message() in {(30*60 - elapsed_time)//60} minutes.")
        context.job_queue.run_once(send_scheduled_image_after_last_message, (30*60 - elapsed_time), data=(file_id, last_message_time), chat_id=context.job.chat_id)
        # context.job_queue.run_once(send_scheduled_image_after_last_message, interval=(30*60 - elapsed_time))


def main():
    # Create the ApplicationBuilder and pass in the bot's token
    dp = ApplicationBuilder().token(TOKEN).build()

    # Add handlers for commands and messages
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("queue", get_scheduled_messages_count))
    dp.add_handler(MessageHandler(filters.PHOTO, schedule_image))

    # Start the bot
    dp.run_polling()
    
if __name__ == '__main__':
    main()
