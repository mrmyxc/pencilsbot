import discord
import psycopg2
import os
import re
from discord import client
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
import signal
import sys

import echomatch

load_dotenv()
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
db_file = "db"

dbconnection = psycopg2.connect(DATABASE_URL, sslmode='require')
dbcursor = dbconnection.cursor()
print(dbconnection.get_dsn_parameters(), "\n")

# Executing a SQL query
dbcursor.execute("SELECT version();")

record = dbcursor.fetchone()
print("connected to - ", record, "\n")

bot = commands.Bot(command_prefix='!pencils ')
the_loop = bot.loop

main_channel = 0
# main_channel_name = "jhh"
main_channel_name = "coral-reef"
main_channel_id = 0

channels = {}

matches = {}

def get_ping():
    # ping = "<@&786615126853812225>"
    ping = "ABC"
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
    get_saved_matches()
    

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
    msg = await get_ch().send(f"{ping}\n```{ms}```")
    m.messageid = msg.id
    await msg.pin()
    save_matches()

@bot.command(name="remove", help="Remove a match")
async def remove(ctx, *args):
    print(args)
    print(" ".join(args))
    m = remove_match(" ".join(args))
    if ( m != None):
        ping = get_ping()
        ms = m.get_match_string()
        await get_ch().send(f"{ping}\nRemoved\n> {ms}")
        m.cancel()
        print("unpin message")
        message = await get_ch().fetch_message(m.messageid)
        await message.unpin()
    
@bot.command(name="show", help="show all matches")
async def show(ctx, *args):
    for m in matches:
        await get_ch().send("```{ms}```".format(ms=matches[m].get_match_string()))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Some error...')

async def mycc(echomatch):
    print("in mycc")
    print("unpin message")
    message = await get_ch().fetch_message(echomatch.messageid)
    await message.unpin()

    print("in mycc - save fire before removing and changing to false")
    fire = echomatch.fire
    
    remove_match("{}".format(echomatch.id))

    if fire != True:
        print("not firing callback - match was removed")
        return

    print("in mycc")
    print("time to start match")
    ping = get_ping()
    ms = echomatch.get_match_string()
    await get_ch().send(f"{ping} Next Match \n```{ms}```")

def myc(echomatch):
    asyncio.run_coroutine_threadsafe(mycc(echomatch), the_loop)

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
        matches[str(m.id)] = m
        return m

def show_matches():
    print("show matches")
    for m in matches:
        print( m.get_match_string() )

def remove_match(args):
    found = 0
    print("remove match")
    print(args)
    print(matches)
    the_match_id = re.search(r"(\d+)?", args).group()
    the_match = None
    # remove other matches that arent supposed to be there
    remove_ids = []
    for m in matches:
        print( "Match: " + str(m))
        if matches[m].is_cancelled() or str(m) == str(the_match_id):
            found = 1
            print("found match to remove")
            matches[m].cancel()
            remove_ids.append(m)

    if found != 0:
        the_match = matches[the_match_id]
        for x in remove_ids:
            del matches[x]

        ms = the_match.get_match_string()
        print(f"Removed a Match\n> {ms}")
    else:
        print("could not find match")
    
    save_matches()

    return the_match

def file_get_saved_matches():
    saved_match_string = r"\[(?P<match_id>\d+)\][,\s]+\[(?P<msg_id>\d+)\][,\s]+(?P<match_opponent>.+),(?P<match_date>.+)[,\s]+(?P<match_time>.+)"
    pa = re.compile(saved_match_string, re.IGNORECASE)
    try:
        file = open("matches.echo", "r")
        print("Checking all saved matches")
        for line in file.readlines():
            print(line.strip())
            matched_string_obj = pa.match(line.strip())
            if matched_string_obj != None:
                print("creating match from save file")
                x = echomatch.EchoMatch(matched_string_obj, myc, the_loop)
                matches[str(x.id)] = x
    except:
        print("failed to open file. may not exist")
        file = open("matches.echo", "w")
        
    file.close()

def file_save_matches():
    file = open("matches.echo", "w")
    match_lines = []
    for match in matches:
        match_lines.append( matches[match].get_match_conf() )
        match_lines.append( "\n" )
    
    file.writelines(match_lines)
    file.close()

def db_save_matches():
    print("Saving all current matches into database")
    dbinsert = "INSERT INTO echo_matches (id, details) "
    dbalternative = " ON CONFLICT DO NOTHING;"

    dbgetquery = "SELECT * FROM echo_matches;"
    dbcursor.execute(dbgetquery)
    records = dbcursor.fetchall()

    # ids to skip
    skips = []

    # add if in dictionary but not in database
    # remove if in database but not in dictionary
    for record in records:
        print("REC : ", record[0])
        print(matches.keys())
        if str(record[0]) not in matches.keys(): #id
            dbdelete = f"DELETE FROM echo_matches WHERE id = {record[0]};"
            print(dbdelete)
            dbcursor.execute(dbdelete)
        else:
            skips.append(str(record[0]))
    
    print("SKIP : ", skips)

    for echo_match_id in matches:
        if echo_match_id not in skips:
            print( echo_match_id, " not in skips")
            amatch = matches[echo_match_id]
            dbvalues = "VALUES({id}, '{details}')".format(id = amatch.id, details = amatch.get_match_conf())
            print(dbinsert + dbvalues + dbalternative)
            dbcursor.execute(dbinsert + dbvalues + dbalternative)

    dbconnection.commit()
    print(f"Number of records {dbcursor.rowcount}")

def db_get_saved_matches():
    saved_match_string = r"\[(?P<match_id>\d+)\][,\s]+\[(?P<msg_id>\d+)\][,\s]+(?P<match_opponent>.+),(?P<match_date>.+)[,\s]+(?P<match_time>.+)"
    pa = re.compile(saved_match_string, re.IGNORECASE)
    print("Checking all saved matches in database")
    dbquery = "SELECT * FROM echo_matches"
    dbcursor.execute(dbquery)
    records = dbcursor.fetchall()
    for record in records:
        print(record)
        matched_string_obj = pa.match(record[1])
        if matched_string_obj != None:
            print("creating match from save file")
            x = echomatch.EchoMatch(matched_string_obj, myc, the_loop)
            matches[str(x.id)] = x


def save_matches():
    if db_file == "file":
        file_save_matches()
    else:
        db_save_matches()

def get_saved_matches():
    if db_file == "file":
        file_get_saved_matches()
    else:
        db_get_saved_matches()


def signal_handler(sig, frame):
    try:
        print('closing database')
        dbcursor.close()
        dbconnection.close()
    except:
        print("error closing database")

    try:
        print('stopping bot')
        bot.close()
    except:
        print("error stopping bot")
    
    print("stop all match threads")
    for echo_match_id in matches:
        matches[echo_match_id].stop()

    print('exiting')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

bot.run(TOKEN)
