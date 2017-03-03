import re
from datetime import datetime, timedelta

# constants
#   constant dictionary
class TOS_CONSTANTS:
    def __init__(self):
        pass

    def con():
        def boss():
            def arg():
                def count():
                    min         = 3
                    max         = 5
        def files():
            def logger():
                name            = "wings.logger"
                file            = name + ".log"
            debug               = logger.name + "debug.log"
            valid_db            = "wings-valid_db"
            norepeat            = "wings-norepeat"
            welcomed            = "wings-welcomed"
        def time():
            def offset():
                eastern         = timedelta(hours=3)
                pacific         = timedelta(hours=-3)
                boss02s         = timedelta(hours=-2)
                boss04s         = timedelta(hours=-4)
                boss16s         = timedelta(hours=-16)
            def wait():
                _4hr            = timedelta(hours=4)
                anchor          = timedelta(hours=3)
            def seconds():
                in_day          = 24 * 60 * 60
        def words():
            def message():
                reason          = "Reason: "
                welcome         = "Thank you for inviting me to your server! " + \
                                    "I am a representative bot for the Wings of Vaivora, here to help you record your journey.\n" + \
                                    "\nHere are some useful commands: \n\n" + \
                                    '\n'.join(cmd_usage['name']) + \
                                    '\n'*2 + \
                                    "(To be implemented) Talt, Reminders, and Permissions. Check back soon!\n"
                                    # '\n'.join(cmd_usage['talt']) # + \
                                    # '\n'.join(cmd_usage['remi']) # + \
                                    # '\n'.join(cmd_usage['perm'])
        def error():
            broad               = -1
            wrong               = -2
            syntax              = -127

    def rx():
        def format():
            def time():
                full            = re.compile(r'[0-2]?[0-9][:.][0-5][0-9]([ap]m?)?', re.IGNORECASE)
                am              = re.compile(r' ?pm?', re.IGNORECASE)
                pm              = re.compile(r' ?am?', re.IGNORECASE)
                delim           = re.compile(r'[:.]')
            def letters():
                main            = re.compile(r'[a-z -]+', re.IGNORECASE)
                remove          = re.compile(r'[^a-z0-9 .:$",-]', re.IGNORECASE)
            numbers             = re.compile(r'^[0-9]{1}$')
            quotes              = re.compile(r'"')
            def boss():
                def status():
                    _all        = re.compile(r'(died|anchor(ed)?|warn(ed|ing)?)', re.IGNORECASE)
                    anchored    = re.compile(r'(anchor(ed)?', re.IGNORECASE)
                    warning     = re.compile(r'(warn(ed|ing)?)', re.IGNORECASE)
                def floors():
                    indicator   = re.compile(r'[bfd]?[0-9][bfd]?$', re.IGNORECASE)
                    fl_format   = re.compile(r'.*(?P<basement>b?)(?P<floor>f?)(?P<district>(d ?(ist(rict)?)?)?) ?(?P<floornumber>[0-9]) ?(?P=basement)?(?P=floor)?(?P=district)?$', re.IGNORECASE)
                channel         = re.compile(r'ch?[1-4]$', re.IGNORECASE)
        def vaivora():
            def cmd():
                def boss():
                    prefix      = re.compile(r'(va?i(v|b)ora, |\$)boss', re.IGNORECASE)
                    def arg():
                        _all    = re.compile(r'all', re.IGNORECASE)
                        _list   = re.compile(r'li?st?', re.IGNORECASE)
                        _erase  = re.compile(r'(erase|del(ete)?)', re.IGNORECASE)
                    def deathweaver():
                        _all    = re.compile(r'(ashaq|c(rystal)? ?m(ine)?)', re.IGNORECASE)
                        _cm     = re.compile(r'c(rystal)? ?m(ine)?', re.IGNORECASE)
                        _ashaq  = re.compile(r'ashaq[a-z ]*', re.IGNORECASE)
                    def harpeia():
                        _all    = re.compile(r'd(emon)? ?p(ris(on?))? ?', re.IGNORECASE)
                        _dist   = re.compile(r'(d ?(ist(rict)?)?)?[125]', re.IGNORECASE)
                        _distN  = re.compile(r'(d ?(ist(rict)?)?)?', re.IGNORECASE)
        def db():
            ext                 = re.compile(r'\.db$', re.IGNORECASE)
            filename            = re.compile(r'[0-9]{18,}')

    def reason():
        def invalid():
            database            = 
    #   regular constants
    con = dict()

    #   regex dictionary
    rx = dict()


    #   error(**) related constants
    #     error(**) constants for "command" argument
    cmd                         = dict()
    cmd['name']                 = "Command: Boss"
    # cmd['talt']                 = "Command: Talt Tracker" ####TODO
    # cmd['reminders']            = "Command: Reminders"    ####TODO
    #     error(**) constants for "reason" argument

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

