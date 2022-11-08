import datetime
import time
import json
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

posted_messages_file = config["Files"]["posted_messages_file"]

client = TelegramClient(username, api_id, api_hash)
client.start()


def load_json():
    read = ""
    with open(posted_messages_file, "r") as f:
        read = f.read()
    return json.loads(read)


def save_json(message_arr):
    with open(posted_messages_file, "w") as f:
        f.write(json.dumps(message_arr))


async def get_messages():
    channel = 0
    message_list = []
    for channel_name in channels:
        channel = await client.get_entity(channel_name)
        messages = await client.get_messages(channel, limit=int(message_limit)) #pass your own args

        for x in messages:
            message_list.append(SourceMessage(x, channel_name))
        time.sleep(30)

    return message_list


def filter_messages(message_list):
    filtered_messages = []
    
    for message in message_list:
        if message == None or message == "None":
            continue

        now = datetime.datetime.now(TIMEZONE)
        seconds_passed = now.timestamp() - message.message.date.timestamp()

        if int(seconds_passed) > 2000:
            continue

        for keyword in keywords:
            if keyword in message.message.text:
                if message not in filtered_messages:
                    filtered_messages.append(message)
            
    return filtered_messages


def main():
    posted_messages = load_json()

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
                
        save_json(posted_messages)

        time.sleep(20 * 60)


main()
