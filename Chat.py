import re
import asyncio
from urllib.parse import urlparse
import operator
import discord
import sys
import time
from link import Link
import BinaryThree
import ImageLib

two_week = 12096000
# Pic used to post after a repost
repost_img = "repost.jpg"
# Name of the emoji to use under the repost
emoji_name = "nik"
# Default log length who will be used to scan or clean
log_len = sys.maxsize


class Chat:
    """
    class for a text channel on a discord sever, each channel is stored in a
    list to be used to know witch object to
    refer to a message.
    Each object have it own hash table for user number of repost and link, it
    own instance of emoji.
    <pre>:
    <post>:
    <inv>;
    """

    ChannelList = {}

    def __init__(self, message, client, ban_list, logger, pool):
        self.Data = {}
        self.Ban_list = ban_list
        self.User = {}
        self.Logger = logger
        self.Client = client
        self.Message = 0
        self.Tree = BinaryThree.Tree()
        self.Channel = message.channel
        self.Emoji = discord.utils.get(message.guild.emojis, name=emoji_name)
        Chat.ChannelList[message.channel] = self
        self.Logger.info("New channel : id = {} name = {} ".format(self.Channel.id, self.Channel.name))
        self.Pool = pool

    def user_in(self, user_id):
        """
        Return if the user with user_id for id is in the DataBase
        <pre>:
            user_id != None
        <post>:
            user_id in self.Data
        """
        return user_id in self.User

    def add_user_duplicate(self, user_id):
        """
        Ingress the repost counter of a user, if he is not int the dictionary,
        add it with 1 repost.
        <pre>:
            user_id != None
        <post>:
            user_in(user_id) -> self.Data{user_id} = old.self.Data{user_id} + 1
            Else self.Data{user_id} = 1
        :param user_id:
        :return: void
        """
        if user_id in self.User:
            self.User[user_id] = self.User[user_id] + 1
            self.Logger.debug("Channel {} : add duplicate for user = {} nb = {}".format(self.Channel, user_id,
                                                                                        self.User[user_id]))
        else:
            self.User[user_id] = 1
            self.Logger.debug("Channel {} : add duplicate for user"
                              " : {}".format(self.Channel, user_id))

    async def add_in_tree(self, image_hash, author):
        """
        Return True if found a same picture else return False
        <pre>:
            image_hash != None or author != None
        <post>:
            imageHash in Tree ->
                if self.User[author] exist then old.self.User[author] + 1 = self.User[author]
                Else self.User[author] = 1
        """
        if image_hash is None or author is None:
            return False
        self.Logger.debug("Channel {} new value in tree {}".format(self.Channel, image_hash))
        temp = ImageLib.add_in_tree(self.Tree, image_hash)
        if temp is not None:
            self.Logger.debug("Channel {} find duplicate {} from {} {}".format(self.Channel, image_hash.link(), author,
                                                                               temp.link()))
            self.add_user_duplicate(author)
            if temp.link() not in self.Data:
                self.Data[temp.link()] = Link(0, author, time.time())
            else:
                self.Data[temp.link()].add_one()
            return True
        return False

    async def send_message(self, text=None, embed_text=None):
        if text is None and embed_text is None:
            return None
        try:
            tmp = await self.Channel.send(content=text, embed=embed_text)
            self.Logger.debug("Channel {} : send message {} and embed {}".format(
                self.Channel, text, embed_text))
            return tmp
        except discord.HTTPException as e:
            self.Logger.error("Channel {} Send HTTPException : {}".format(self.Channel,
                                                                          e.args))
            return None
        except discord.InvalidArgument as e:
            self.Logger.error("Channel {} Send InvalidArgument : {}".format(self.Channel,
                                                                            e.args))
            return None

    async def edit_message(self, message, text=None, embed_text=None):
        if text is None and embed_text is None:
            return None
        try:
            await message.edit(content=text, embed=embed_text)
            self.Logger.debug("Channel {} : edit message {}".format(self.Channel, text))
            return message
        except discord.HTTPException as e:
            self.Logger.info("Channel {} Edit HTTPException : {}".format(self.Channel,
                                                                         e.args))
            await self.send_message(self, text)
        except discord.InvalidArgument as e:
            self.Logger.error("Channel {} Edit InvalidArgument : {}".format(self.Channel,
                                                                            e.args))
        except discord.DiscordException as e:
            self.Logger.warning("Channel {} : edit message {} fail {}".format(
                self.Channel, message, e))

    async def self_message(self, author, message_limit=log_len):
        """
        Count the number of message of a user in the last message_limit message
        in the channel.
        :param author:
        :param message_limit:
        :return: void
        """
        self.Logger.info("Channel {} : self_message author = {} limit = {}".format(self.Channel, author, message_limit))
        counter = 0
        tmp = await self.send_message(text='Calculating messages...')
        async for log in self.Channel.history(limit=message_limit):
            if log.author == author:
                counter += 1

        await self.edit_message(tmp, text='You have {} messages.'.format(counter))
        await asyncio.sleep(5)
        tmp.delete()

    async def count_old(self, message_limit=log_len):
        """
        Count the number of message in the channel in the limit of message_limit.
        :param message_limit:
        :return: void
        """
        self.Logger.info("Channel {} : count limit = {}".format(self.Channel, message_limit))
        tmp = await self.send_message(text='Calculating messages...')
        counter = len(await self.Channel.history(limit=message_limit).flatten())

        await self.edit_message(tmp, text='There is {} messages.'.format(counter))

    async def count(self):
        """
        Return the actual count of message for this channel.
        :return: void
        """
        self.Logger.info("Channel {} : count".format(self.Channel))
        tmp = await self.send_message(text='There is {} messages.'.format(self.Message))
        await asyncio.sleep(5)
        tmp.delete()

    async def clean(self, message_limit=log_len):
        """
        Delete all the message posted by the bot in the channel in the limit of
        the last message_limit message.
        :param message_limit:
        :return: void
        """
        self.Logger.info("Channel {} : clean limit = {}".format(self.Channel, message_limit))
        async for log in self.Channel.history(limit=message_limit):
            if log.author == self.Client.user:
                await log.delete()
        self.Logger.debug("Channel {} : end clean".format(self.Channel))

    async def user(self):
        """
        Tell the number of repost of each user in the dictionary.
        :return: void
        """
        self.Logger.info("Channel {} : user".format(self.Channel))
        sorted_x = sorted(self.User.items(), key=operator.itemgetter(1), reverse=True)
        text = "Top user by number of repost\n"
        for x in sorted_x:
            user_data = await self.Client.fetch_user(x[0])
            text += "{} have made {} repost\n".format(user_data.name, x[1])
        self.Logger.info(text)
        text = "```" + text + "```"
        await self.send_message(text=text)

    async def aff_ranking(self, top, dic):
        """
        Show the ranking of the first top element of the dictionary
        :return: void
        """
        self.Logger.info("Channel {} : ranking".format(self.Channel))
        sorted_x = sorted(dic.items(), key=operator.itemgetter(1), reverse=True)
        text = "Ranking :\n"
        k = 0
        while (k <= top or k >= len(sorted_x)) and sorted_x[k][1].nb_repost() > 0:
            # <> to prevent preview
            text += "<{}> have been reposted {} time\n".format(sorted_x[k][0], sorted_x[k][1].nb_repost())
            k += 1
        self.Logger.info(text)
        await self.send_message(text=text)

    async def link_ranking(self, top):
        """
        Show the ranking of the first 10 element the most reposted in the
        channel.
        :return: void
        """
        self.Logger.info("Channel {} : Link ranking".format(self.Channel))
        sorted_x = sorted(self.Data.items(), key=operator.itemgetter(1), reverse=True)
        text = "Link Ranking :\n"
        k = 0
        while (k <= top or k >= len(sorted_x)) and sorted_x[k][1].nb_repost() > 0:
            # <> to prevent preview
            text += "<{}> have been reposted {} time\n".format(sorted_x[k][0], sorted_x[k][1].nb_repost())
            k += 1
        self.Logger.info(text)
        await self.send_message(text="```" + text + "```")

    async def site_ranking(self, top):
        site = {}
        tmp = None
        for i in list(self.Data):
            tmp = urlparse(i).netloc
            if tmp in site:
                site[i] += 1
            else:
                site[i] = 0
        await self.aff_ranking(top, tmp)

    async def size(self):
        """
        Tell the size of the dictionary of link.
        :return: void
        """
        self.Logger.info("Channel {} : size".format(self.Channel))
        await self.send_message(text='Dictionary link size : {}\nDictionary user size : {}\nTree size: {}'.format(
            self.human_bytes(await self.get_size(self.Data)),
            self.human_bytes(await self.get_size(self.User)),
            self.human_bytes(await self.get_size(self.Tree))))

    async def scan(self, message_limit=log_len):
        """
        Scan the channel for the last message_limit, put all the link in the
        dictionary, count the repost and the number
        of link to tell it to after.
        :param message_limit:
        :return: void
        """
        self.Logger.info("Channel {} : scan limit = {}".format(self.Channel, message_limit))
        counter = 0
        number = 0
        img_list = []
        tmp = await self.send_message(text='Scanning the chat...')
        async for log in self.Channel.history(limit=message_limit):
            number += 1
            self.Logger.debug("Channel {} : message number {}".format(self.Channel, number))
            urls = []
            if self.test_start(log.content, self.Ban_list):
                urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                                  log.content)
            for link in urls:
                self.Logger.debug("Channel {} : Work on {}".format(self.Channel, link))
                if link in self.Data and self.Data[link].author() != log.author.id:
                    self.add_user_duplicate(log.author.id)
                    self.Data[link].add_one()
                    counter += 1
                else:
                    if re.search(r'(?:http:|https:)?//.*\.(?:png|jpg)', link) is not None:
                        img_list.append([link, log.author.id])
                    else:
                        self.Data[link] = Link(0, log.author.id, time.time())
        self.Message = number
        await tmp.edit(content="Image recognition... {} to scan".format(len(img_list)))
        for i in img_list:
            # try:
            self.Logger.debug("Channel {} hash image {} from author {}".format(self.Channel, i[0], i[1]))
            image_hash, author = await ImageLib.image_hash(i[0], i[1])
            if await self.add_in_tree(image_hash, author):
                counter += 1
            # except:
            #    self.Logger.warning("Channel {} : Link hash {} failed".format(self.Channel, i))
        await tmp.edit(content='You have {} message for {} link, {} images and {} duplicate.'.format(
            number, len(self.Data), len(img_list), counter))

    async def time(self):
        """
        Tell the date of creation of the server.
        <post>:
        self.send_message(time of the first message of self.Channel)
        :return: void
        """
        self.Logger.info("Channel {} : time".format(self.Channel))
        await self.send_message(text=discord.utils.snowflake_time(self.Channel.id))

    async def reaction_number(self, link):
        """
        Send a message in a channel to show the number of time that the link
        have been posted
        :param link: Number of re-post to send in the message
        :return:
        """
        nb_list = self.number_in_base(link.nb_repost(), 10)
        emoji_list = [':zero:', ':one:', ':two:', ':three:', ':four:', ':five:',
                      ':six:', ':seven:', ':eight:', ':nine:']
        text = "Number of re-post of this pic : "
        for i in nb_list:
            text += emoji_list[int(i)]
        text += "\n {}".format(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(link.first_post())))
        await self.send_message(text=text)

    async def new_message(self, message):
        """
        Test a message to find link, if there is link, add it to dictionary of
        increment the number of repost of the message author, post reaction and
        reaction image.
        :param message:
        :return: void
        """
        self.Logger.info("Channel {} : new message".format(self.Channel))
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                          message.content)
        self.Logger.debug("Channel {} : new message have {} link\n".format(self.Channel, len(urls)))
        for link in urls:
            if link in self.Data and self.Data[link].author() != message.author:
                self.Logger.debug("not same author {} {}\n".format(self.Data[link].author, message.author))
                self.add_user_duplicate(message.author.id)
                self.Data[link].add_one()
                await self.reaction_number(self.Data[link])
                if time.time() - self.Data[link].first_post() <= two_week:
                    await self.Channel.send(message.channel, file=repost_img)
                    await message.add_reaction(self.Emoji)  # \U0001F44D
            elif not (link in self.Data):
                self.Logger.debug("New link {} {}\n".format(link, message.author))
                self.Data[link] = Link(0, message.author, time.time())
            if re.search(r'(?:http:|https:)?//.*\.(?:png|jpg)', link) is not None:
                try:
                    self.Logger.debug("Channel {} hash image {}".format(self.Channel, link))
                    image_hash, author = await ImageLib.image_hash(link, message.author)
                    if await self.add_in_tree(image_hash, author):
                        await self.Channel.send(message.channel, repost_img)
                        await message.add_reaction(self.Emoji)
                except discord.DiscordException:
                    self.Logger.warning("Channel {} : Link {} is dead".format(self.Channel, link))

    async def on_message(self, message):
        """
        Try to find a option in the message, if cant use new_message else use
        the function linked to the option.
        :param message:
        :return: void
        """
        self.Message += 1
        if message.content.startswith('-mine'):
            await self.self_message(message.author, self.get_value(message.content, '-mine'))
        elif message.content.startswith('-count'):
            await self.count_old()
        elif message.content.startswith('-clean'):
            await self.clean(self.get_value(message.content, '-clean'))
        elif message.content.startswith('-user'):
            await self.user()
        elif message.content.startswith('-size'):
            await self.size()
        elif message.content.startswith('-scan'):
            await self.scan(self.get_value(message.content, '-scan'))
        elif message.content.startswith('-time'):
            await self.time()
        elif message.content.startswith('-help'):
            await self.help()
        elif message.content.startswith('-link'):
            await self.link_ranking(self.get_value(message.content, '-link'))
        else:
            await self.new_message(message)

    async def get_size(self, obj, seen=None):
        """
        Recursively finds size of objects in bytes.
        :param: the object to get the size
        :return: the size in bites of the object
        """
        size = sys.getsizeof(obj)
        if seen is None:
            seen = set()
        obj_id = id(obj)
        if obj_id in seen:
            return 0
        """
        Important mark as seen *before* entering recursion to gracefully handle
        self-referential objects
        """
        seen.add(obj_id)
        if isinstance(obj, dict):
            size += sum([await self.get_size(v, seen) for v in obj.values()])
            size += sum([await self.get_size(k, seen) for k in obj.keys()])
        elif hasattr(obj, '__dict__'):
            size += await self.get_size(obj.__dict__, seen)
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
            size += sum([await self.get_size(i, seen) for i in obj])
        return size

    async def help(self):
        """
        Show the help of the bot
        :return: void
        """
        text = "```DiscordRepost bot : help\n"
        text += "\t [] for optional information, all command start by - default except if you change it in conf\n"
        text += "\t -mine [max message log] count the number of message you send\n"
        text += "\t -count Return the actual count of message for this channel.\n"
        text += "\t -scan [max message log] search link in the channel, count them and duplicate, store them\n"
        text += "\t -size send the size of the data base\n"
        text += "\t -user send a ranking of the user by number of repost\n"
        text += "\t -time date of the creation of the server\n"
        text += "\t -link [number to show] top x link by number of repost\n"
        text += "\t -help aff this\n```"

        await self.send_message(text=text)

    @staticmethod
    def human_bytes(size):
        """
        Return the given bytes as a human friendly KB, MB, GB, or TB string
        :param size: the size in bytes
        :return: the size in bytes in a human readable format in a string
        """
        b = float(size)
        kib = float(1024)
        mib = float(kib ** 2)  # 1,048,576
        gib = float(kib ** 3)  # 1,073,741,824
        tib = float(kib ** 4)  # 1,099,511,627,776

        if b < kib:
            return '{0} {1}'.format(b, 'Bytes' if 0 == b > 1 else 'Byte')
        elif kib <= b < mib:
            return '{0:.2f} KiB'.format(b / kib)
        elif mib <= b < gib:
            return '{0:.2f} MiB'.format(b / mib)
        elif gib <= b < tib:
            return '{0:.2f} GiB'.format(b / gib)
        elif tib <= b:
            return '{0:.2fv} TiB'.format(b / tib)

    def get_value(self, word, init):
        """
        Try to find a value in the rest of a text, if cant return the default
        value.
        :param word: word to test
        :param init: start of the word to skip
        :return: The Number to use of the default value if nothing is found.
        """
        self.Logger.info("Channel {} : get_value : word = '{}' init = '{}'".format(
            self.Channel, word, init))
        try:
            temp = int(float(word[len(init):]))
            self.Logger.debug("get value {}".format(temp))
            return temp
        except IndexError:
            self.Logger.debug("Init is to long")
            return log_len
        except ValueError:
            self.Logger.debug("Not a number")
            return log_len

    @staticmethod
    def number_in_base(number, base):
        """
        Return a number in a list, every number represent base^x
        :param number: the number to convert
        :param base: the base to convert
        :return: the list of every base^x
        """
        number_list = []
        nb = base
        if number == 0:
            return [0]
        while number != 0:
            number_list.append((number % nb) / (nb // base))
            number -= number % nb
            nb = nb * base
        return number_list[::-1]

    @staticmethod
    def test_start(text, ban):
        for i in ban:
            if text.startswith(i):
                return False
        return True
