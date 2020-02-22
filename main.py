from multiprocessing import Pool
import discord
import logging
import Chat
# import asyncio
"""
Todo:
Image similaire
Banir certains site
Image aléatoire
Sauvegarder donnée
"""

# Process pool for the different object to use.
pool = Pool(processes=4)

# Token of the discord bot, needed to be able to connect to the discord server
token = ''

# Banned start of message, for other bot
banned_start = ['!']

# Configure
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

Client = discord.Client()


@Client.event
async def on_ready():
    print('Logged in as')
    print(Client.user.name)
    print(Client.user.id)
    print('------')


@Client.event
async def on_message(message):
    for i in banned_start:
        if message.content.startswith(i):
            return
    if message.channel in Chat.Chat.ChannelList and message.author != Client.user:
        await Chat.Chat.ChannelList[message.channel].on_message(message)
    elif message.author != Client.user:
        channel = Chat.Chat(message, Client, banned_start, logger, pool)
        await channel.on_message(message)

Client.run(token)
