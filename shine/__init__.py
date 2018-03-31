import yaml
import pty
import os
import json
import random
import shlex

from .iproute2 import addInterface, delInterface

CONFIG = {}


def debug(*args, **kwargs):
    print(*args, **kwargs)


# Load the configuration file
try:
    with open("/etc/moonshine/moonshine.yml") as fil:
        CONFIG = yaml.load(fil)
except Exception as E:
    pass


def parseCom(args):
    '''
    Convert an SSH command into user, pass, host, and commands
    '''
    r = {}
    if ' ' in args:
        r['host'], r['commands'] = args.split(" ", 1)
    else:
        r['host'] = args
    if "@" in r['host']:
        d = r['host']
        r['user'], r['host'] = d.split("@", 1)
        if ":" in r['user']:
            r['user'],\
                r['pass'] = r['user'].split(":", 1)
    if 'user' not in r:
        r['user'] = 'root'
    return r


def buildCom(r):
    '''
    Turn a dictionary of ssh settings into an ssh command
    '''
    command = r['host']
    if r.get('user', False):
        command = r['user'] + "@" + command
    if r.get('commands', False):
        command += ' ' + r['commands']
    if r.get('newip', False) and r.get('host') != "localhost":
        command = "-b " + r.get('newip') + " " + command
    command = 'ssh -tt -A -o StrictHostKeyChecking=no ' + command
    if r.get('pass', False):
        command = "sshpass -p "+r['pass'] + " " + command
    return command


def newProxy():
    '''
    Initialize a new proxy to connect to the remote box
    '''
    def badRemote(user):
        print("Pass the new connection information to moonshine. e.g.")
        print("ssh {}@moonshine root@remoteip".format(user))
        quit(1)

    i = {}
    i['user'] = os.environ['USER']
    i['ip'] = os.environ.get('SSH_CONNECTION', False)
    args = os.environ.get('SSH_ORIGINAL_COMMAND', "").strip()
    if args is "":
        badRemote(i['user'])
    i['remote'] = parseCom(args)

    # Make sure we are in an ssh session
    if not i['ip']:
        print("Moonshine must be run from within an SSH session!\nExiting...")
        quit(255)
    else:
        i['ip'] = i['ip'].split()[0]  # Get the actual IP from env var
    # Generate a new IP address
    newip = CONFIG["netmask"].split("/")[0]
    newip = newip.split(".")[:3]
    newip += [str(random.randint(100, 254))]
    newip = ".".join(newip)
    i['remote']['newip'] = newip
    # Print context
    print(json.dumps(i, indent=2))
    # Create the final SSH command to send
    # split the command into an array of arguments for spawn
    command = shlex.split(buildCom(i['remote']))
    print(command, flush=True)
    addInterface(newip)
    pty.spawn(command)
    delInterface(newip)
