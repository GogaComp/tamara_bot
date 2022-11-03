import datetime
import time
import asyncio
import configparser
from telethon import TelegramClient
from telethon.tl import functions, types
from aiogram import Bot, types

TIMEZONE = datetime.timezone.utc

class SourceMessage:
    def __init__(self, message, source):
        self.message = message
        self.source = source

# config uses spaces as dividers
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
username = config['Telegram']['username']

token = config["Bot"]["token"]
channel_id = config["Bot"]["channel_id"]

channels = config["Channels"]["channel_list"].split(" ")
message_limit = config["Channels"]["message_limit"]

keywords = config["Keywords"]["keyword_list"].split(" ")

client = TelegramClient(username, api_id, api_hash)
client.start()

async def get_messages():
    channel = 0
    message_list = []
    for channel_name in channels:
        channel = await client.get_entity(channel_name)
        messages = await client.get_messages(channel, limit=int(message_limit)) #pass your own args

        for x in messages:
            message_list.append(SourceMessage(x, channel_name))
        time.sleep(5)

    return message_list


def filter_messages(message_list):
    filtered_messages = []
    
    for message in message_list:
        now = datetime.datetime.now(TIMEZONE)
        seconds_passed = now.timestamp() - message.message.date.timestamp()

        if int(seconds_passed) > 300:
            continue

        for keyword in keywords:
            # if keyword in message.message.text:
            if message not in filtered_messages:
                filtered_messages.append(message)
            
    return filtered_messages


def main():
    with open("posted.txt", "r", encoding="utf-8") as f:
        posted_messages = f.readlines()

    loop = asyncio.get_event_loop()
    bot = Bot(token=token, parse_mode=types.ParseMode.HTML)
    while True:
        messages = loop.run_until_complete(get_messages())
        filtered = filter_messages(messages)

        for message in filtered:
            if message.message.text not in posted_messages:
                formatted = "{}\n\nИсточник: {}".format(
                    message.message.text,
                    f"https://t.me/{message.source}"
                )
                loop.run_until_complete(bot.send_message(channel_id, formatted, parse_mode=types.ParseMode.MARKDOWN))
                posted_messages.append(message.message.text)
                
        with open("posted.txt", "w", encoding="utf-8") as f:
            for i in posted_messages:
                f.write(f"{i}\n")

        time.sleep(5)


main()
