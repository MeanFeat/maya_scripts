import sys
from maya import cmds


def fail_exit(msg='the script has failed'):
    print(msg)
    cmds.headsUpMessage(msg, time=2.0)
    sys.exit()
