import random
from .tools import execute

DEFAULT_ROUTE = None

CONFIG = {}


def addInterface(ip, label=None, dev=None):
    '''
    add a virtual interface with the specified IP address
    Returns: label - the label of the new interface
    '''
    if not dev:
        dev = CONFIG.get("interface", "eth0")
    # Generate a label for the virtual interface
    label = "{}:shine{}".format(dev, random.randint(1, 1000))
    while label in getInterfaceLabels(dev):
        label = "{}:shine{}".format(dev, random.randint(1, 1000))

    # Add the interface
    command = "ip addr add {}/24 brd + dev {} label {}"
    command = command.format(ip, dev, label)
    res = execute(command)
    if res.get('status', 255) != 0:
        raise Exception("Cannot add interface: {}\n{}".format(
                        res.get('stderr', ''), command))
    return {'label': label, 'ip': ip}


def delInterface(ip=None, label=None, dev=None):
    '''
    delete a virtual interface with the specified IP address
    '''
    if not dev:
        dev = CONFIG.get("interface", "eth0")
    if ip is None and label is not None:
        try:
            ip = getLabelAddress(label)[0]
        except Exception as E:
            raise Exception("Cannot find interface for {}".format(label))
    res = execute("ip addr del {}/24 dev {}:*".format(ip, dev))
    if res.get('status', 255) != 0:
        raise Exception("Cannot delete interface: {}".format(
                        res.get('stderr', '')))
    return True


def addRoute(ip, dev):
    '''
    Add a route for a specific interface through a label
    ip  - string    - The ip to route for
    dev - string    - The device to route through
    '''
    # make sure the ip has a subnet mask, default to 32 if not
    if "/" not in ip:
        ip += "/32"
    # We should only get the default route once
    global DEFAULT_ROUTE
    if DEFAULT_ROUTE is None:
        DEFAULT_ROUTE = getDefault()
    # Add the route with the ip command
    com = "ip route add {} dev {} via {}".format(ip, dev, DEFAULT_ROUTE)
    res = execute(com)
    if res.get('status', 255) != 0:
        raise Exception("Cannot add route: {}".format(
                        res.get('stderr', '')))
    return True


def delRoute(ip):
    '''
    Delete routes for specific ip addresses
    ip  - string    - The ip to delete the route for
    '''
    com = "ip route del {}".format(ip)
    res = execute(com)
    if res.get('status', 255) != 0:
        raise Exception("Cannot delete route: {}".format(
                        res.get('stderr', '')))
    return True


def getInterfaceLabels(dev=None):
    '''
    return the labels of all virtual interfaces for a dev
    '''
    # If the device is not specified, use the device in the config
    if not dev:
        dev = CONFIG.get("interface", "eth0")
    # The command to list all the labels assigned to an interface
    command = "".join(("ip a show dev {0} | grep -Eo '{0}:[a-zA-Z0-9:]+'",
                       " | cut -d':' -f2-"))
    # command = "ip a show dev {0}"
    command = command.format(dev)
    res = execute(command)
    try:
        labels = res['stdout'].strip().split()
        return labels
    except Exception as E:
        raise Exception("Cannot get labels: {}".format(res.get('stderr', '')))


def getLabelAddress(label):
    '''
    Get the IP address for a label
    label  - string - the label to search for
    return - list   - the ip address(es) for the given label
    '''
    command = ("ip addr show label {} | grep -Eo 'inet [0-9.]+'"
               " | cut -d' ' -f2")
    command = "".join(command).format(label)
    res = execute(command)
    try:
        return res['stdout'].strip().split()
    except Exception as E:
        raise Exception("Cannot get ip: {}".format(res.get('stderr', '')))


def getDefault():
    '''
    Find and return the default route
    '''
    com = "ip route show | grep -oE 'default via [0-9.]+' | cut -d' ' -f3"
    res = execute(com)
    try:
        default = res['stdout'].strip()
        if default != "" and res['status'] == 0:
            return default
        raise
    except Exception as E:
        error = res.get('stderr', '')
        raise Exception("Cannot find default route: {}".format(error))
