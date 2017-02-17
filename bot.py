import discord
import logging
import sqlite3
import shlex
import re
import os
from time import sleep
from datetime import datetime, timedelta
from operator import itemgetter

# basic declarations and initializations
client    = discord.Client()

# variables to use
valid_dbs = list()

# begin constants for strings for error messages
#   command - usage
cmd_usage = dict()
cmd_usage['heading']      = "Usage:\n"
#   command - [us]age - [c]ode [bl]oc[k]
cmd_usage['code_block']   = "```"
#   command - [us]age - [a]rguments [bl]oc[k]
cmd_usage['back_tick']    = "`"
#   command - [us]age - [c]ode [arg]uments
cmd_usage['heading.arg']  = "Arguments:\n"
cmd_usage['debug']        = " Debug message. Something went wrong.\n"

#   begin $boss specific constants
cmd_usage['boss.arg.1']   = "BossName|\"Boss Name\""
cmd_usage['boss.prefix']  = ("$boss ","Vaivora, boss ")
cmd_usage['boss']         = ["***'Boss' commands***"]
cmd_usage['boss'].append(cmd_usage['heading'])
cmd_usage['boss'].append(cmd_usage['code_block'])
#   end of $boss specific constants
# end of constants for strings for error messages

# begin $boss usage string, in cmd_usage['boss'] : list
#     command - usage - [b]oss - [n]th command -- reuse after every append
#         boss arg [n] - cmd_usage['boss.args'][n]
cmd_usage['boss.args'] = list()
cmd_usage['boss.args'].append(cmd_usage['boss.arg.1'] + " died|anchored time [chN] [Map|\"Map\"]\n",)
cmd_usage['boss.args'].append(cmd_usage['boss.arg.1'] + " erase [chN]\n",)
cmd_usage['boss.args'].append(cmd_usage['boss.arg.1'] + " list [chN]\n",)
cmd_usage['boss.args'].append("all list",)

cmd_usage['boss'].append('\n'.join([("PREFIX " + boss_arg) for boss_arg in cmd_usage['boss.args']]))
cmd_usage['boss'].append(cmd_usage['code_block'])
cmd_usage['boss'].append("Valid " + cmd_usage['back_tick'] + "PREFIX" + cmd_usage['back_tick'] + "es: `" + \
                         '` & `'.join(cmd_usage['boss.prefix']) + "`\n")

# cmd_usage['boss'].append('\n'.join([(' '.join(t) for t in zip(cmd_usage['boss.prefix'], cmd_usage['boss.args'][1]*2))]))
# cmd_usage['boss'].append('\n'.join([(' '.join(t) for t in zip(cmd_usage['boss.prefix'], cmd_usage['boss.args'][2]*2))]))
# cmd_usage['boss'].append('\n'.join([(' '.join(t) for t in zip(cmd_usage['boss.prefix'], cmd_usage['boss.args'][3]*2))]))
#     command - usage - [b]oss - [a]rgument descriptors
#             n=5
cmd_usage['boss.arg'] = "`-` Boss Name or `all` **(required)**\n" + \
                "`- -` Either part of, or full name; if spaced, enclose in double-quotes (\")\n" + \
                "`- -` all when used with list will display all valid entries.\n" + \
                "`-` time **(required for** `died` **and** `anchored` **)**\n" + \
                "`-` Map *(optional)*\n" + \
                "`- -` Handy for field bosses only. World bosses don't move across maps. This is optional and if unlisted will be unassumed.\n" + \
                "Do note that Jackpot Bosses (clover buff) are 'world boss' variants of field bosses, " + \
                "and should not be recorded because they have unpredictable spawns.\n"
cmd_usage['boss'].append(cmd_usage['boss.arg'])
# end of $boss usage string, in cmd_usage['boss.args']

cmd_usage['boss.acknowledged'] = " Thank you! Your command has been acknowledged and recorded.\n"

# begin constants to use for error(**)
#     general command errors
cmd_usage['error.badsyntax']  = "Your command was malformed.\n"
cmd_usage['error.ambiguous']  = "Your command was ambiguous.\n"

#     specific command errors
#         command - usage - [b]oss - [m]ap
cmd_usage['boss.name']        = "Make sure to properly spell the boss name.\n"
cmd_usage['boss.map']         = "Make sure to properly record the map.\n"
cmd_usage['boss.status']      = "Make sure to properly record the status.\n"
# end of constants for error(**)

# constants
#   constant dictionary
con = dict()
con['BOSSCMD.ARG.COUNTMIN'] = 3
con['BOSSCMD.ARG.COUNTMAX'] = 5
con['STR.REASON']           = "Reason: "
con['TIME.OFFSET.EASTERN']  = timedelta(hours=3)
con['TIME.OFFSET.PACIFIC']  = timedelta(hours=-3)
con['TIME.WAIT.4H']         = timedelta(hours=4)
con['TIME.WAIT.ANCHOR']     = timedelta(hours=3)
con['LOGGER']               = "tos.wingsofvaivora"
con['LOGGER.FILE']          = "tos.wingsofvaivora.log"
con['STR.MESSAGE.WELCOME']  = "Thank you for inviting me to your server! " + \
                              "I am a representative bot for the Wings of Vaivora, here to help you record your journey.\n" + \
                              "Here are some useful commands:" + \
                              '\n'.join(cmd_usage['boss']) # + \
                              # '\n'.join(cmd_usage['talt']) # + \
                              # '\n'.join(cmd_usage['remi']) # + \
                              # '\n'.join(cmd_usage['perm'])
con['ERROR.BROAD']          = -1
con['ERROR.WRONG']          = -2
con['ERROR.SYNTAX']         = -127

#   regex dictionary
rx = dict()
# rx['format.numbers']        = re.compile(r'[0-9]+')
rx['format.letters']        = re.compile(r'[a-z -]+')
rx['format.time.pm']        = re.compile(r' ?[Pp][Mm]?')
rx['format.time.am']        = re.compile(r' ?[Aa][Mm]?')
rx['format.letters.inv']    = re.compile(r'[^A-Za-z0-9 :$"-]')
rx['format.time']           = re.compile(r'[0-2]?[0-9]:[0-5][0-9]([AaPp][Mm]?)?')
rx['format.quotes']         = re.compile(r'"')
rx['boss.status']           = re.compile(r'([Dd]ied|[Aa]nchored|[Ww]arn(ed)?)')
rx['boss.status.anchor']    = re.compile(r'([Aa]nchored)')
rx['boss.status.warning']   = re.compile(r'([Ww]arn(ed)?)')
rx['boss.channel']          = re.compile(r'(ch)?[1-4]')
rx['boss.floors']           = re.compile(r'[bf]?[0-9][bf]?$')
rx['boss.floors.format']    = re.compile(r'.+(?P<basement>b?)(?P<floor>f?)(?P<floornumber>[0-9])(?P=basement)(?P=floor)$')
# rx['boss.floors.arrange']   = re.compile(r'\g<floor>\g<floornumber>\g<basement>')
rx['vaivora.boss']          = re.compile(r'([Vv]a?i(v|b)ora, |\$)boss')
rx['boss.arg.all']          = re.compile(r'all')
rx['boss.arg.list']         = re.compile(r'li?st?')
rx['str.ext.db']            = re.compile(r'\.db$')
#   error(**) related constants
#     error(**) constants for "command" argument
cmd                         = dict()
cmd['boss']                 = "Command: Boss"
# cmd['talt']                 = "Command: Talt Tracker"
# cmd['reminders']            = "Command: Reminders"
#     error(**) constants for "reason" argument
#### TODO: Replace con['STR.REASON'] applied to each one? Priority: low
reason = dict()
reason['baddb'] = con['STR.REASON'] + "Bad Database"
reason['unkwn'] = con['STR.REASON'] + "Unknown"
reason['broad'] = con['STR.REASON'] + "Broad Command"
reason['argct'] = con['STR.REASON'] + "Argument Count"
reason['noanc'] = con['STR.REASON'] + "Cannot Anchor"
reason['unknb'] = con['STR.REASON'] + "Unknown Boss"
reason['syntx'] = con['STR.REASON'] + "Malformed Syntax"
reason['quote'] = con['STR.REASON'] + "Mismatched Quotes"
reason['bdmap'] = con['STR.REASON'] + "Bad Map"
reason['bdtme'] = con['STR.REASON'] + "Bad Time"
reason['fdbos'] = con['STR.REASON'] + "Field Boss Channel"

# database formats
prototype = dict()
prototype['time'] = ('year', 'month','day','hour','minute')
prototype['boss'] = ('name', 'channel','map','status','text_channel') + prototype['time']
prototype['remi'] = ('user', 'comment') + prototype['time']
prototype['talt'] = ('user', 'previous','current','valid') + prototype['time']
prototype['perm'] = ('user', 'role')

# and the database formats' types
prototype['time.types'] = ('real',)*5
prototype['boss.types'] = ('text',) + ('real',) + ('text',)*3 + prototype['time.types']
prototype['remi.types'] = ('text',)*2 + prototype['time.types']
prototype['talt.types'] = ('text',) + ('real',)*3 + prototype['time.types']
prototype['perm.types'] = ('text',)*2

# zip, create, concatenate into tuple
boss_tuple = tuple('{} {}'.format(*t) for t in 
                   zip(prototype['boss'], prototype['boss.types']))
remi_tuple = tuple('{} {}'.format(*t) for t in 
                   zip(prototype['remi'], prototype['remi.types']))
talt_tuple = tuple('{} {}'.format(*t) for t in 
                   zip(prototype['talt'], prototype['talt.types']))
perm_tuple = tuple('{} {}'.format(*t) for t in
                   zip(prototype['perm'], prototype['perm.types']))

# snippet from discord.py docs
logger = logging.getLogger(con['LOGGER'])
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(con['LOGGER.FILE'], encoding="utf-8")
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# @func:      create_discord_db(Discord.server.str, func, *)
# @arg:
#   discord_server: the discord server's name
#   db_func:        a database function
#   xargs:          extra arguments
# @return:
#   Relevant data if successful, False otherwise
async def func_discord_db(discord_server, db_func, xargs=None):
    discord_db  = discord_server + ".db"
    conn = sqlite3.connect(discord_db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if not os.path.isfile(discord_db):
        await create_discord_db(c)
        return False # not initialized
    elif not callable(db_func):
        return False
    # implicit else
    if xargs:
        dbif  = await db_func(c, xargs)
    else:
        dbif  = await db_func(c)
    conn.commit()
    return dbif

# @func:      create_discord_db(sqlite3.connect.cursor)
# @arg:
#   conn:           the sqlite3 connection
# @return:
#   None
async def create_discord_db(c):
    # delete tables if necessary since it may be invalid #### Maybe to ignore?
    c.execute('drop table if exists boss')
    c.execute('drop table if exists reminders')
    c.execute('drop table if exists talt')
    c.execute('drop table if exists permissions')
    # create boss table
    c.execute('create table boss({})'.format(','.join(boss_tuple)))
    
    # create reminders table
    c.execute('create table reminders({})'.format(','.join(remi_tuple)))
    

    # create talt tracking table
    c.execute('create table talt({})'.format(','.join(talt_tuple)))
    

    # create permissions hierarchy
    c.execute('create table permissions({})'.format(','.join(perm_tuple)))
    
    return

# @func:    validate_discord_db(sqlite3.connect.cursor)
# @arg:
#   c:              the sqlite3 connection cursor
# @return:
#   True if valid, False otherwise
async def validate_discord_db(c):
    # check boss table
    try:
        c.execute('select * from boss')
        r = c.fetchone()
        # check if boss table matches format
        if not tuple(r.keys()) is prototype['boss']:
            return False # invalid db
        #### TODO: Validate other tables when implemented, priority: medium
        return True
    except:
        return False

# @func:    check_boss_db(sqlite3.connect.cursor, list)
# @arg:
#   c:              the sqlite3 connection cursor
#   boss_list:      list containing bosses to check
# @return:
#   None if db is not prepared; otherwise, a list
async def check_boss_db(c, boss_list):
    for b in boss_list:
        c.execute("select * from boss where name=?", b)
        db_record.extend(c.fetchall())
    # return a list of records
    return db_record

# @func:    update_boss_db(sqlite3.connect.cursor, dict)
# @arg:
#   c:              the sqlite3 connection cursor
#   boss_dict:      message_args from on_message(*)
# @return:
#   True if successful, False otherwise
async def update_boss_db(c, boss_dict):
    # the following two bosses rotate per spawn
    if boss_dict['boss'] == 'Mirtis' or boss_dict['boss'] == 'Helgasercle':
        c.executemany("select * from boss where name=?", 'Mirtis')
        contents = c.fetchall()
        c.executemany("select * from boss where name=?", 'Helgasercle')
        contents += c.fetchall()
    elif boss_dict['boss'] == 'Demon Lord Marnox' or boss_dict['boss'] == 'Rexipher':
        c.executemany("select * from boss where name=?",'Demon Lord Marnox')
        contents = c.fetchall()
        c.executemany("select * from boss where name=?", 'Rexipher')
        contents += c.fetchall()
    else:
        c.executemany("select * from boss where name=? and channel=?", (boss_dict['boss'], boss_dict['channel']))
        contents = c.fetchall()

    # invalid case: more than one entry for this combination
    #### TODO: keep most recent time? 
    if len(contents) > 1 and boss_dict['boss'] not in bos16s:
        await rm_ent_boss_db(c, boss_dict)

    # if entry has newer data, discard previous
    if contents and (contents[4] < boss_dict['year'] or \
                     contents[5] < boss_dict['month'] or \
                     contents[6] < boss_dict['day'] or \
                     contents[7] < boss_dict['hour'] - 3):
        await rm_ent_boss_db(c, boss_dict)
    else:
        return False

    try: # boss database structure
        c.executemany("insert into boss values (?, ?,?,?,?,?,?,?,?)",
                      (boss_dict['name'],
                       boss_dict['channel'],
                       boss_dict['map'],
                       boss_dict['status'],
                       boss_dict['year'],
                       boss_dict['month'],
                       boss_dict['day'],
                       boss_dict['hour'],
                       boss_dict['mins'],
                       boss_dict['srvchn']))
    except:
        return False
    return True

# @func:    rm_ent_boss_db(sqlite3.connect.cursor, dict)
# @arg:
#   c:              the sqlite3 connection cursor
#   boss_dict:      message_args from on_message(*)
# @return:
#   True if successful, False otherwise
async def rm_ent_boss_db(c, boss_dict):
    try:
        c.executemany("delete from boss where name=? and channel=?", (boss_dict['boss'], boss_dict['channel']))
    except:
        return False
    return True

# @func:    on_ready()
# @return:
#   None
@client.event
async def on_ready():
    print("Logging in...")
    print('Successsfully logged in as: ' + client.user.name + '#' + \
          client.user.id + '. Ready!')

    with os.scandir() as items:
        for item in items:
            if item.is_file() and item.name.endswith(".db"):
                iname = rx['str.ext.db'].sub('',item.name)
                if await func_discord_db(iname, validate_discord_db):
                    valid_dbs.append(item.name)
                else:
                    await func_discord_db(iname, create_discord_db)
                    valid_dbs.append(item.name) # a fresh db is valid

# @func:    on_server_join(discord.Server)
# @return:
#   True if ready, False otherwise
@client.event
async def on_server_join(server):
    if server.unavailable:
        return False
    srvnm = server.name
    status = await func_discord_db(srvnm, validate_discord_db)
    if not status:
        # create if db doesn't already exist
        await func_discord_db(srvnm, create_discord_db)
    # send welcome message
    await send_message(server.owner, con['STR.MESSAGE.WELCOME'])
    return True

# begin boss related variables

# 'bosses'
#   list of boss names in full
bosses = ['Blasphemous Deathweaver',
          'Bleak Chapparition',
          'Hungry Velnia Monkey',
          'Abomination',
          'Earth Templeshooter',
          'Earth Canceril',
          'Earth Archon',
          'Violent Cerberus',
          'Necroventer',
          'Forest Keeper Ferret Marauder',
          'Kubas Event',
          'Noisy Mineloader',
          'Burning Fire Lord',
          'Wrathful Harpeia',
          'Glackuman',
          'Marionette',
          'Dullahan Event',
          'Starving Ellaganos',
          'Prison Manager Prison Cutter',
          'Mirtis',
          'Rexipher',
          'Helgasercle',
          'Demon Lord Marnox',
          'Demon Lord Nuaele',
          'Demon Lord Zaura',
          'Demon Lord Blut']
#   field bosses
bossfl = bosses[0:2] + list(bosses[7]) + list(bosses[11]) + list(bosses[13]) + list(bosses[25])
#   world bosses
bosswo = [b for b in bosses if b not in bossfl]

# 'boss'es that 'alt'ernate
bosalt = ['Mirtis',
          'Rexipher',
          'Helgasercle',
          'Demon Lord Marnox']

# 'boss' - N - 'special'
#   list of bosses with unusual spawn time of 2h
bos02s = ['Kubas Event',
          'Dullahan Event']
#   list of bosses with unusual spawn time of 16h
bos16s = ['Demon Lord Nuaele',
          'Demon Lord Zaura',
          'Demon Lord Blut']

# 'boss synonyms'
# - keys: boss names (var `bosses`)
# - values: list of synonyms of boss names
bossyn = {'Blasphemous Deathweaver':['dw','spider','deathweaver'],
          'Bleak Chapparition':['chap','chapparition'],
          'Hungry Velnia Monkey':['monkey','velnia','velniamonkey',
            'velnia monkey'],
          'Abomination':['abom','abomination'],
          'Earth Templeshooter':['temple shooter','TS','ETS','templeshooter'],
          'Earth Canceril':['canceril','crab','ec'],
          'Earth Archon':['archon'],
          'Violent Cerberus':['cerb','dog','doge','cerberus'],
          'Necroventer':['nv','necro','necroventer'],
          'Forest Keeper Ferret Marauder':['ferret','marauder'],
          'Kubas Event':['kubas'],
          'Noisy Mineloader':['ml','mineloader'],
          'Burning Fire Lord':['firelord','fl','fire lord'],
          'Wrathful Harpeia':['harp','harpy','harpie','harpeia'],
          'Glackuman':['glack','glackuman'],
          'Marionette':['mario','marionette'],
          'Dullahan Event':['dull','dulla','dullachan'],
          'Starving Ellaganos':['ella','ellaganos'],
          'Prison Manager Prison Cutter':['cutter','prison cutter',
            'prison manager','prison manager cutter'],
          'Mirtis':['mirtis'],
          'Rexipher':['rexipher','rexi','rexifer'],
          'Helgasercle':['helga','helgasercle'],
          'Demon Lord Marnox':['marnox','marn'],
          'Demon Lord Nuaele':['nuaele'],
          'Demon Lord Zaura':['zaura'],
          'Demon Lord Blut':['blut']}

# 'boss synonyms short'
# - list of synonyms of boss names
bossns = []
for l in list(bossyn.values()):
    bossns.extend(l)

# 'boss location'
# - keys: boss names (var `bosses`)
# - values: list of locations, full name
bosslo = {'Blasphemous Deathweaver':['Crystal Mine 2F',
                                     'Crystal Mine 3F',
                                     'Ashaq Underground Prison 1F',
                                     'Ashaq Underground Prison 2F',
                                     'Ashaq Underground Prison 3F'],
          'Bleak Chapparition':['Tenet Church B1',
                                'Tenet Church 1F'],
          'Hungry Velnia Monkey':['Novaha Assembly Hall',
                                  'Novaha Annex',
                                  'Novaha Institute'],
          'Abomination':['Guards\' Graveyard'],
          'Earth Templeshooter':['Royal Mausoleum Workers\' Lodge'],
          'Earth Canceril':['Royal Mausoleum Constructors\' Chapel'],
          'Earth Archon':['Royal Mausoleum Storage'],
          'Violent Cerberus':['Royal Mausoleum 4F',
                              'Royal Mausoleum 5F'],
          'Necroventer':['Residence of the Fallen Legwyn Family'],
          'Forest Keeper Ferret Marauder':['Bellai Rainforest',
                                           'Zeraha',
                                           'Seir Rainforest'],
          'Kubas Event':['Crystal Mine Lot 2 - 2F'],
          'Noisy Mineloader':['Mage Tower 4F','Mage Tower 5F'],
          'Burning Fire Lord':['Main Chamber','Sanctuary'],
          'Wrathful Harpeia':['Demon Prison District 1',
                              'Demon Prison District 2',
                              'Demon Prison District 5'],
          'Glackuman':['2nd Demon Prison'],
          'Marionette':['Roxona Reconstruction Agency East Building'],
          'Dullahan Event':['Roxona Reconstruction Agency West Building'],
          'Starving Ellaganos':['Mokusul Chamber',
                                'Videntis Shrine'],
          'Prison Manager Prison Cutter':['Drill Ground of Confliction',
                                          'Resident Quarter',
                                          'Storage Quarter',
                                          'Fortress Battlegrounds'],
          'Mirtis':['Kalejimas Visiting Room',
                    'Storage',
                    'Solitary Cells',
                    'Workshop',
                    'Investigation Room'],
          'Helgasercle':['Kalejimas Visiting Room',
                    'Storage',
                    'Solitary Cells',
                    'Workshop',
                    'Investigation Room'],
          'Rexipher':['Thaumas Trail',
                      'Salvia Forest',
                      'Sekta Forest',
                      'Rasvoy Lake',
                      'Oasseu Memorial'],
          'Demon Lord Marnox':['Thaumas Trail',
                      'Salvia Forest',
                      'Sekta Forest',
                      'Rasvoy Lake',
                      'Oasseu Memorial'],
          'Demon Lord Nuaele':['Yudejan Forest',
                               'Nobreer Forest',
                               'Emmet Forest',
                               'Pystis Forest',
                               'Syla Forest'],
          'Demon Lord Zaura':['Arcus Forest',
                              'Phamer Forest',
                              'Ghibulinas Forest',
                              'Mollogheo Forest'],
          'Demon Lord Blut':['Tevhrin Stalactite Cave Section 1',
                             'Tevhrin Stalactite Cave Section 2',
                             'Tevhrin Stalactite Cave Section 3',
                             'Tevhrin Stalactite Cave Section 4',
                             'Tevhrin Stalactite Cave Section 5']                          
         }

# 'boss location synonyms'
# - list of synonyms of boss locations
# -- grouping similar locations by line
bossls = ['crystal mine','ashaq',
          'tenet',
          'novaha',
          'guards','graveyard',
          'maus','mausoleum',
          'legwyn',
          'bellai','zeraha','seir',
          'mage tower','mt',
          'demon prison','dp',
          'main chamber','sanctuary','sanc',
          'roxona',
          'mokusul','videntis',
          'drill','quarter','battlegrounds',
          'kalejimas','storage','solitary','workshop','investigation',
          'thaumas','salvia','sekta','rasvoy','oasseu',
          'yudejan','nobreer','emmet','pystis','syla',
          'arcus','phamer','ghibulinas','mollogheo',
          'tevhrin']
# probably won't be using this, in hindsight.

# end of boss related variables

# begin code for message processing
# @func:    on_message(Discord.message)
# @arg:
#     message: Discord.message; includes message among sender (Discord.user) and server (Discord.server)
# @return:
#     None
@client.event
async def on_message(message):
    # 'boss' channel processing
    if "timer" in message.channel.name or "boss" in message.channel.name:
        # 'boss' channel command: $boss
        #     arg order:
        #         1. [0] req boss name
        #         2. [1] req status (killed, anchored)
        #         3. [2] req time
        #         4. [3] opt channel
        #         5. [4] opt map
        if message.content.startswith('$boss ') or \
           message.content.startswith('Vaivora, boss '):
            command_server  = message.server.name
            command_message = message.content
            command_message = rx['format.letters.inv'].sub('', command_message)   # sanitize
            command_message = command_message.lower()             # standardize
            command_message = rx['vaivora.boss'].sub('', command_message)     # strip leading command/arg
            message_args    = dict() # keys(): name, channel, map, time, 
            boss_channel    = 1
            maps_idx        = -1

            # command: list of arguments
            command = shlex.split(command_message)
            print(command)
            if command[0] == "help":
                await client.send_message(message.channel, message.author.mention + '\n'.join(cmd_usage['boss']))
                return True

            # if odd amount of quotes, drop
            if len(rx['format.quotes'].findall(command_message)) % 2:
                err_code = await error(message.author, message.channel, reason['quote'], cmd['boss'])
                return err_code

            # begin checking validity
            #     arg validity
            #         count: [3,5]
            if len(command) < con['BOSSCMD.ARG.COUNTMIN'] or len(command) > con['BOSSCMD.ARG.COUNTMAX']:
                err_code = await error(message.author, message.channel, reason['argct'], cmd['boss'], len(command))
                return err_code

            #         boss: letters
            #         status: anchored, died
            #         time: format
            if not (rx['format.letters'].match(command[0]) and rx['boss.status'].match(command[1]) and rx['format.time'].match(command[2])):
                err_code = await error(message.author, message.channel, reason['syntx'], cmd['boss'])
                return err_code

            #     boss validity
            #         all list
            if rx['boss.arg.all'].match(command[0]) and rx['boss.arg.list'].match(command[1]):
                bossrec = await func_discord_db(command_server, check_boss_db, bosses) # possible return
                if not bossrec: # empty
                    await client.send_message(message.channel, message.author.mention + " No results found! Try a different boss.")
                    return True
                await client.send_message(message.channel, message.author.mention + " Records: ```\n" + \
                                          '\n'.join(['\t'.join(brow) for brow in bossrec]) + "\n```")
                return True

            elif rx['boss.arg.all'].match(command[0]):
                err_code = await error(message.author, message.channel, reason['syntx'], cmd['boss'])
                return err_code
            
            boss_idx = await check_boss(command[0])
            if boss_idx < 0  or boss_idx >= len(bosses):
                err_code = await error(message.author, message.channel, reason['unknb'], cmd['boss'], command[0])
                return err_code

            #         boss list
            if rx['boss.arg.list'].match(command[1]):
                bossrec = await func_discord_db(command_server, check_boss_db, list(bosses[boss_idx])) # possible return
                if not bossrec: # empty
                    await client.send_message(message.channel, message.author.mention + " No results found! Try a different boss.")
                    return True
                await client.send_message(message.channel, message.author.mention + " Records: ```\n" + \
                                          '\n'.join(['\t'.join(brow) for brow in bossrec]) + "\n```")
                return True


            #     (opt) channel: reject if field boss & ch > 1 or if ch > 4
            #     (opt) map: validity
            ##### TODO: Make channel limit specific per boss
            if len(command) > 3:
                #     channel is set
                #     keep track of arg position in case we have 5
                argpos = 3
                print(len(command))
                if rx['boss.channel'].match(command[argpos]):
                    boss_channel = int(rx['format.letters'].sub('', command[argpos]))
                    argpos += 1
                
                #     specifically not an elif - sequential handling of args
                #     cases:
                #         4 args: 4th arg is channel
                #         4 args: 4th arg is map
                #         5 args: 4th and 5th arg are channel and map respectively
                try:
                    if not rx['boss.channel'].match(command[argpos]) or len(command) == 5:
                        maps_idx = await check_maps(command[argpos], command[1])
                        if maps_idx < 0 or maps_idx >= len(bosslo[boss]):
                            err_code = await error(message.author, message.channel, reason['bdmap'], cmd['boss'], command[1])
                            return err_code
                except:
                    pass

            #         check if boss is a field boss, and discard if boss channel is not 1
            if bosses[boss_idx] in bossfl and boss_channel != 1:
                err_code = await error(message.author, message.channel, reason['fdbos'], cmd['boss'], boss_channel, bosses[boss_idx])
                return err_code

            # everything looks good if the string passes through
            # begin compiling record in dict form 'message_args'
            message_args['name'] = bosses[boss_idx]
            message_args['channel'] = boss_channel
            if maps_idx >= 0:
                message_args['map'] = bosslo[message_args['name']][maps_idx]
            else:
                message_args['map'] = 'N/A'

            # process time
            #     antemeridian
            if rx['format.time.am'].search(command[2]):
                btime = rx['format.time.am'].sub('', command[2]).split(':')
                bhour = int(btime[0]) % 12
            #     postmeridian
            elif rx['format.time.pm'].search(command[2]):
                btime = rx['format.time.pm'].sub('', command[2]).split(':')
                bhour = (int(btime[0]) % 12) + 12
            #     24h time
            else:
                btime = command[2].split(':')
                bhour = int(btime[0])
            #     handle bad input
            if bhour > 24:
                err_code = await error(message.author, message.channel, reason['bdtme'], cmd['boss'], msg=command[2])
                return err_code
            bminu = int(btime[1])

            approx_server_time = datetime.today() + con['TIME.OFFSET.EASTERN']
            btday = approx_server_time.day
            btmon = approx_server_time.month
            byear = approx_server_time.year

            # late recorded time; correct with -1 day
            mdate = datetime(byear, btmon,btday,hour=bhour,minute=bminu)
            tdiff = mdate-approx_server_time
            if tdiff.days < 0:
                btday -= 1
            elif tdiff.days > 0 or tdiff.seconds > 119: # 2 minute leeway
                err_code = await error(message.author, message.channel, reason['bdtme'], cmd['boss'], msg=command[2])
                return err_code

            wait_time = con['TIME.WAIT.ANCHOR'] if rx['boss.status.anchor'].match(command[1]) else con['TIME.WAIT.4H']
            bhour = bhour + (int(wait_time + con['TIME.OFFSET.PACIFIC']).minutes * 60) # bhour in Pacific/local
            if message_args['name'] in bos02s and rx['boss.status.anchor'].match(command[1]): # you cannot anchor events
                err_code = await error(message.author, message.channel, reason['noanc'], cmd['boss'])
            elif message_args['name'] in bos02s:
                bhour -= 2
            elif message_args['name'] in bos16s:
                bhour += 12 # 12 + 4 = 16

            # add them to dict
            message_args['hour']      = bhour
            message_args['mins']      = bminu
            message_args['day']       = btday
            message_args['month']     = btmon
            message_args['year']      = byear
            message_args['status']    = command[1] # anchored or died
            message_args['srvchn']    = message.channel

            status  = await func_discord_db(command_server, validate_discord_db)
            if not status: # db is not valid
                err_code = await error(message.author, message.channel, reason['baddb'], cmd['boss'])
                await func_discord_db(command_server, create_discord_db) # (re)create db
                return err_code

            status = await func_discord_db(command_server, update_boss_db, message_args)
            if not status: # update_boss_db failed
                err_code = await error(message.author, message.channel, reason['unkwn'], cmd['boss'])
                return err_code

            await client.send_message(message.channel, message.author.mention + cmd_usage['boss.acknowledged'] + \
                                      message_args['name'] + " " + message_args['status'] + " at " + \
                                      message_args['hour'] + ":" + message_args['mins'] + ", CH" + message_args['channel'])

            await bot.process_commands(message)
            return True # command processed
                
    else:
        await bot.process_commands(message)
        return False

# @func:    check_databases()
async def check_databases():
    results = dict()
    while True:
        for valid_db in valid_dbs:
            # check all timers
            message_send = list()
            message_send.append("@here ")
            results[valid_db] = await func_discord_db(valid_db, check_boss_db, bosses)
            # sort by time
            results[valid_db].sort(key=itemgetter(4,5,6,7,8))
            for result in results[valid_db]:
                tupletime = tuple(result[4:9])
                rtime = datetime(tupletime)
                rtime_east = rtime + con['TIME.OFFSET.EASTERN']
                if rtime-datetime.now() < 0: # stale data; delete
                    await func_discord_db(valid_db, rm_ent_boss_db, result)
                elif (rtime-datetime.now()).seconds < 10800 and rx['boss.status.anchor'].match(result[3]):
                    message_send.append(format_message_boss(result[0], result[3], rtime_east, result[1]))
                elif (rtime-datetime.now()).seconds < 14400:
                    message_send.append(format_message_boss(result[0], result[3], rtime_east, result[1]))
        await bot.process_commands(message)
        sleep(60)

def format_message_boss(boss, status, time, bossmap, channel):
    if bossmap == 'N/A':
        bossmap = ['[Map Unknown]',]
    elif boss == "Blasphemous Deathweaver" and re.search("[Aa]shaq",bossmap):
        bossmap = [m for m in bosslo[boss][2:-1] if m != bossmap]
    elif boss == "Blasphemous Deathweaver":
        bossmap = [m for m in bosslo[boss][0:2] if m != bossmap]
    else:
        bossmap = [m for m in bosslo[boss] if m != bossmap]
    status_str  = " " + ("was anchored" if rx['boss.status.anchor'].match(status) else "died") + " at "

    expect_str  = (("between " + (time + con['TIME.WAIT.ANCHOR']).strftime("%Y/%m/%d %H:%M") + " and ") \
                   if rx['boss.status.anchor'].match(status) else "at ") + \
                  (time + con['TIME.WAIT.4H']).strftime("%Y/%m/%d %H:%M") + ", "
    map_str     = "in the following maps: " + '. '.join(bossmap)
    message     = boss + status_str + time.strftime("%Y/%m/%d %H:%M") + ", and should spawn " + \
                  expect_str + map_str
    return message

# @func:    check_boss(str): begin code for checking boss validity
# @arg:
#     boss: str; boss name from raw input
# @return:
#     boss index in list, or -1 if not found
async def check_boss(boss):
    if boss in bosses:
        return bosses.index(boss)
    else:
        # for b in bosses:
        #     if b in boss:
        #         return bosses.index(b)
        for b, syns in bossyn.items():
            if boss in syns or b in boss:
                return bosses.index(b)
    return -1
# end of check_boss

# @func:    check_maps(str): begin code for checking map validity
# @arg:
#     maps: str; map name from raw input
#     boss: str; the corresponding boss
# @return:
#     map index in list, or -1 if not found
async def check_maps(maps, boss):
    if rx['boss.floors'].match(maps):
        # rearrange letters, and remove map name
        mapnum = rx['boss.floors.format'].sub(r'\g<floor>\g<floornumber>\g<basement>', maps)
        mmatch = mapnum.search(maps)
        if not mmatch:
            return -1
        return bosslo[boss].index(mmatch)
    else:
        for m in bosslo[boss]:
            if m in maps:
                return bosslo[boss].index(m)
    return -1

# @func:  error(**): begin code for error message printing to user
# @arg:
#     user:     Discord.user
#     channel:  server channel
#     etype:    [e]rror type
#     ecmd:     [e]rror (invoked by) command
#     msg:      (optional) message for better error clarity
# @return:
#     -1:     BROAD:  the command was correctly formed but the argument is too broad
#     -2:     WRONG:  the command was correctly formed but could not validate arguments
#     -127:   SYNTAX: malformed command: quote mismatch, argument count
async def error(user, channel, etype, ecmd, msg='', xmsg=''):
    # get the user in mentionable string
    user_name = user.mention
    # convert args
    if msg:
        msg = str(msg)
    if xmsg:
        xmsg = str(xmsg)
    # prepare a list to send message
    ret_msg   = list()

    # boss command only
    if ecmd == cmd['boss']:
        # broad
        if etype == reason['broad']:
            ret_msg.append(user_name + the_following_argument('boss') + msg + \
                           ") for `$boss` has multiple matching spawn points:\n")
            ret_msg.append(cmd_usage['code_block'])
            ret_msg.append('\n'.join(bosslo[msg]))
            ret_msg.append(cmd_usage['code_block'])
            ret_msg.append(cmd_usage['error.ambiguous'])
            ret_msg.append(cmd_usage['boss.map'])
            ecode = con['ERROR.BROAD']
        elif etype == reason['unkwn']:
            ret_msg.append(user_name + " I'm sorry. Your command failed for unknown reasons.\n" + \
                           "This command failure has been recorded.\n" + \
                           "Please try again shortly.\n")
            with open('wings_of_vaivora-error.txt','a') as f:
                f.write(datetime.today() + " An error was detected when " + user_name + " sent a command.")
            ecode = con['ERROR.WRONG']
        # unknown boss
        elif etype == reason['unknb']:
            ret_msg.append(user_name + the_following_argument('boss') + msg + \
                           ") is invalid for `$boss`. This is a list of bosses you may use:\n")
            ret_msg.append(cmd_usage['code_block'])
            ret_msg.append('\n'.join(bosses))
            ret_msg.append(cmd_usage['code_block'])
            ret_msg.append(cmd_usage['boss.name'])
            ecode = con['ERROR.WRONG']
        elif etype == reason['noanc']:
            ret_msg.append(user_name + the_following_argument('status') + msg + \
                           ") is invalid for `$boss`. You may not select `anchored` for its status.\n")
            ret_msg.append(cmd_usage['boss'])
        elif etype == reason['bdmap']:
            try_msg = list()
            try_msg.append(user_name + the_following_argument('map') + msg + \
                           ") (number) is invalid for `$boss`. This is a list of maps you may use:\n")
            try: # make sure the data is valid by `try`ing
              try_msg.append(cmd_usage['code_block'])
              try_msg.append('\n'.join(bosslo[xmsg]))
              try_msg.append(cmd_usage['code_block'])
              try_msg.append(cmd_usage['boss.map'])
              # seems to have succeeded, so extend to original
              ret_msg.extend(try_msg)
              ecode = con['ERROR.WRONG']
            except: # boss not found! 
              ret_msg.append(user_name + cmd_usage['debug'])
              ret_msg.append(cmd_usage['error.badsyntax'])
              ecode = con['ERROR.SYNTAX']
              with open('wingsofvaivora.debug.log','a') as f:
                  f.write('boss not found\n')
        elif etype == reason['fdbos']:
            ret_msg.append(user_name + the_following_argument('channel') + msg + \
                           ") (number) is invalid for `$boss`. " + xmsg + " is a field boss, thus " + \
                           "variants that spawn on channels other than 1 (or other maps) are considered world bosses " + \
                           "with unpredictable spawns.\n")
            ecode = con['ERROR.WRONG']
        elif etype == reason['bdtme']:
            ret_msg.append(user_name + the_following_argument('time') + msg + \
                           ") is invalid for `$boss`.\n")
            ret_msg.append("Omit spaces; record in 12H (with AM/PM) or 24H time.\n")
            ret_msg.append(cmd_usage['error.badsyntax'])
            ecode = con['ERROR.WRONG']
        elif etype == reason['noanc']:
            ret_msg.append(user_name + the_following_argument('status') + 'anchored' + \
                           ") is invalid for `$boss`.\n" +
                           "You cannot anchor events or bosses of this kind.\n")
            ecode = con['ERROR.WRONG']
        elif etype == reason['argct']:
            ret_msg.append(user_name + " Your command for `$boss` had too few arguments.\n" +  
                           "Expected: 4 to 6; got: " + msg + ".\n")
            ret_msg.append(cmd_usage['error.badsyntax'])
            ecode = con['ERROR.SYNTAX']
        elif etype == reason['quote']:
            ret_msg.append(user_name + " Your command for `$boss` had misused quotes somewhere.\n")
            ret_msg.append(cmd_usage['error.badsyntax'])
            ecode = con['ERROR.SYNTAX']
        else:
            ret_msg.append(user_name + cmd_usage['debug'] + "\n" + etype)
            ret_msg.append(cmd_usage['error.badsyntax'])
            ecode = con['ERROR.SYNTAX']
            await client.send_message(channel, '\n'.join(ret_msg))
            return ecode
        # end of conditionals for cmd['boss']

        # begin common return for $boss
        ret_msg.extend(cmd_usage['boss'])
        await client.send_message(channel, '\n'.join(ret_msg))
        return ecode
        # end of common return for $boss

    # todo: reminders, Talt tracking, permissions
    else:
        # todo
        ret_msg.append(user_name + cmd_usage['debug'])
        ret_msg.append(cmd_usage['error.badsyntax'])
        ecode = con['ERROR.SYNTAX']
        await client.send_message(channel, '\n'.join(ret_msg))
        return ecode 
# end of error

# @func:  the_following_argument(str): begin concatenated string
# @arg:
#     arg: str; e.g. boss, map, time
# @return:
#     str, containing message
def the_following_argument(arg):
    return " The following argument `" + arg + "` ("
# end of the_following_argument

with open('discordtoken','r') as f:
    secret = f.read()
client.run(secret)