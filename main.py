import discord
import os
import re
from discord import client
import threading

from discord.ext import commands
from discord.flags import SystemChannelFlags
from dotenv import load_dotenv

import echomatch

load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = commands.Bot(command_prefix='!pencils ')
the_loop = bot.loop

main_channel = 0
# main_channel_name = "jhh"
main_channel_name = "coral-reef"
main_channel_id = 0

channels = {}

matches = {}

def get_ping():
    ping = "<@&786615126853812225>"
    # ping = "ABC"
    return ping

def get_ch():
    for x in bot.get_all_channels():
        # print(x)
        # print(x.id)
        channels[x] = x.id
        if x.name == main_channel_name:
            main_channel_id = x.id
            print(main_channel_id)

    main_channel = bot.get_channel(main_channel_id)
    print(main_channel)
    return main_channel

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    

# @bot.event
# async def on_message(message):
#     if (message.author == client.user):
#         return
#     m = message.content.lower() 

#     if ( m.startswith("!pencils") ):
#         commands.parse_cmd(message)
    
@bot.command(name="name")
async def name(ctx, args):
    await ctx.send("```hello {}```".format(args))


@bot.command(name="add", help="Add a match")
async def add(ctx, *args):
    print(args)
    print(" ".join(args))
    m = add_match(" ".join(args))
    ping = get_ping()
    ms = m.get_match_string()
    msgid = await get_ch().send(f"{ping}\n```{ms}```")
    m.messageid = msgid
    await msgid.pin()

@bot.command(name="remove", help="Remove a match")
async def remove(ctx, *args):
    print(args)
    print(" ".join(args))
    m = await remove_match(" ".join(args))
    if ( m != None):
        ping = get_ping()
        ms = m.get_match_string()
        await get_ch().send(f"{ping}\nRemoved\n> {ms}")
        await m.messageid.unpin()
    
@bot.command(name="show", help="show all matches")
async def show(ctx, *args):
    for m in matches:
        await get_ch().send("```{ms}```".format(ms=matches[m].get_match_string()))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Some error...')

async def myc(echomatch):
    if echomatch.fire != True:
        print("not firing callback - match was removed")
        return

    print("time to start match")
    ping = get_ping()
    ms = echomatch.get_match_string()
    await get_ch().send(f"{ping} Next Match \n```{ms}```")
    print("unpin message")
    await echomatch.messageid.unpin()

def get_match_details( s ):
    match_string = r"(?P<match_opponent>.+),(?P<match_date>.+)[,\s](?P<match_time>.+)"
    p = re.compile(match_string, re.IGNORECASE)
    m = p.match(s)
    print("Matched --")
    print(m)
    return m

def add_match(args):
    print("add_time")
    print(args)
    details = get_match_details(args)
    if ( details ):
        print("making match")
        m = echomatch.EchoMatch(details, myc, the_loop)
        print("made match")
        # add message ref to pin and unpin
        matches[str(m.id)] = m
        return m

def show_matches():
    print("show matches")
    for m in matches:
        print( m.get_match_string() )

async def remove_match(args):
    found = 0
    print("remove match")
    print(args)
    print("Matches ---")
    print(matches)
    print("--- Matches")
    the_match_id = re.search(r"(\d+)?", args).group()
    the_match = None
    for m in matches:
        print( "Match: " + str(m))
        if str(m) == str(the_match_id):
            found = 1
            print("found match to remove")
            matches[m].fire = False
            if matches[m].timer != None:
                print("cancel timer")
                matches[m].timer.cancel()
            print("unpin message")
            await matches[m].messageid.unpin()

    if found != 0:
        the_match = matches[the_match_id]
        del matches[the_match_id]

    return the_match

bot.run(TOKEN)
