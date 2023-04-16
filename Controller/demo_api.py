# Script with a demo on how to use the API
# First run controller with "python3 Controller.py"

import rpyc

# Connect to Controller.py
conn = rpyc.connect("localhost", 18861)

def start_server_A():
    """ Start accel-pppd Server A in Namespace A. """
    return  conn.root.start_server_A()

def start_server_B():
    """ Start accel-pppd Server B in Namespace B. """
    return  conn.root.start_server_B()

def stop_server_A():
    """ Stop accel-pppd Server A."""
    return  conn.root.stop_server_A()

def stop_server_B():
    """ Stop accel-pppd Server B. """
    return  conn.root.stop_server_B()

def start_client():
    """ Start the PPPoE client that is tying to connect to a PPPoE Server via interface veth-A-Client."""
    return  conn.root.start_client()

def stop_client():
    """ Stop the PPPoE client. """
    return  conn.root.stop_client()

def get_sessions_A():
    """ Get sessions of Server A. """
    return  conn.root.get_sessions_A()

def get_sessions_B():
    """ Get sessions of Server B. """
    return  conn.root.get_sessions_B()

def migrate_to_A(session):
    """ Migrate [session] to server A."""
    return  conn.root.migrate_to_A(session)

def migrate_to_B(session):
    """ Migrate [session] to server B."""
    return  conn.root.migrate_to_B(session)

def migrate_all_to_A(sessions):
    """ Migrate all sessions of [sessions] to server A."""
    return conn.root.migrate_all_to_A(sessions)

def migrate_all_to_B(sessions):
    """ Migrate all sessions of [sessions] to server B."""
    return  conn.root.migrate_all_to_B(sessions)

def is_online_A():
    """ Returns availability of Server A. """
    return conn.root.is_online_A()

def is_online_B():
    """ Returns availability of Server B. """
    return conn.root.is_online_B()

def set_auto_migration(auto_migrate: bool):
    """ Change setting for automatically migrating sessions form server A to server B. """
    return conn.root.set_auto_migration(auto_migrate)

def write_dummy_sessions_A():
    """ Write dummy session to server A. """
    return conn.root.write_dummy_sessions_A()

def write_dummy_sessions_B():
    """ Write dummy session to server B. """
    return  conn.root.write_dummy_sessions_B()

set_auto_migration(True)