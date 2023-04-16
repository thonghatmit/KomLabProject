from multiprocessing.sharedctypes import SynchronizedBase
from multiprocessing import Process, Value
import os
import json
import re
import time
import rpyc
import random


# Shared variable between multiple processes
auto_migrate = Value('b', False)


class PPPoE_Server:
    """ Class to read and write PPPoE sessions of an accel-ppp server. """

    def __init__(self, name: str, interface: str, ip: str, online: SynchronizedBase):
        self.name = name
        self.interface = interface
        self.ip = ip
        self.online = online

    def __str__(self):
        return f"{self.name}: interface={self.interface}, ip={self.ip}"

    def __mac_to_int(self, mac: str):
        """ Converts a mac address to int. Example: ff:ff:ff:ff:ff:ff to 255 255 255 255 255 255"""
        res = re.match('^((?:(?:[0-9a-f]{2}):){5}[0-9a-f]{2})$', mac.lower())
        if res is None:
            raise ValueError('invalid mac address')

        mac_list = [int(i, 16) for i in mac.split(":")]

        return " ".join(str(x) for x in mac_list)

    def is_json(self, data: str):
        """ Function to check if string is a valid json. """
        try:
            json.loads(data)
        except ValueError as e:
            return False
        return True

    def establish_connection(self):
        """ Establish a PPPoE Connection with the Server (Only discovery phase). """
        return os.popen(f"sudo pppoe -I {self.interface} -d").read()

    def is_available(self):
        """ Checks if server is available. """
        sessions = self.read_sessions()
        print(f"{self.name}: {sessions}")

        # Detect if server is working
        if(len(sessions.keys()) == 0):
            print(f"{self.name} is offline!")
            return False
        else:
            return True

    def read_sessions(self):
        """ Reads sessions of server and changes value of self.online according to the availability of the server. """
        response = os.popen(f"accel-cmd -H {self.ip} pppoe show states").read()
        if response.find("pppoe_states") > 0 and self.is_json(response):
            self.online.value = True
            print(f"{self.name}: online.value = True")
            return json.loads(response)
        else:
            self.online.value = False
            print(f"{self.name}: online.value = False")
            emtyDict = {}
            return emtyDict

    def write_session(self, username: str, ip: int, peer_ip: str, session_id: str, calling_station_id: str, called_station_id: str):
        """ Writes a session to server.
        Handels bug where a session can't be written if there are no sessions inside the server.
        """
        command = f"accel-cmd -H {self.ip} pppoe write states {username} {ip} {peer_ip} {session_id} {self.__mac_to_int(calling_station_id)} {self.__mac_to_int(called_station_id)}"
        if(len(self.read_sessions()["pppoe_states"]) == 0):
            print(
                f"No Sessions in {self.name}, establishing connection to avoid bug")
            self.establish_connection()
        return os.popen(command).read()

    def write_session_safe(self, session):
        """ A safer way to write a session to server.
        Checks if a session contains all the necessary values before writing it to server.
        """
        # Get existing sessions
        existing_sessions = self.read_sessions()

        # Check if session is already inside server
        if(session_in_array(session, existing_sessions)):
            return f"Session {session['sid']} already in {self.name}."

        # Check if session contains all the necessary values
        if("sid" in session) and ("username" in session) and ("ip" in session) and ("peer_ip" in session) and ("calling_station_id" in session) and ("called_station_id" in session):
            # Write Sessions to Server
            response = self.write_session(session['username'], session['ip'], session['peer_ip'],
                                          session['sid'], session['calling_station_id'], session['called_station_id'])
            return f"Writing Session {session['sid']} to {self.name}.", response
        else:
            return f"Session {session['sid']} does not contain all necessary values needed for migration:", session


class ApiService(rpyc.Service):
    """ Class with API functions that can be called to control the servers. """

    def on_connect(self, conn):
        # code that runs when a connection is created
        # (to init the service, if needed)
        pass

    def on_disconnect(self, conn):
        # code that runs after the connection has already closed
        # (to finalize the service, if needed)
        pass

    def exposed_start_server_A(self):
        """ Start accel-pppd Server A in Namespace A. """
        if (serverA.is_available()):
            return "Server A is already online."
        else:
            os.popen("sudo ip netns exec NamespaceA accel-pppd -d -c ../Accel-PPP-Modified/accel-pppd/accel-ppp_A.conf -p /var/run/accel-ppp-A.pid")
            return "Server A started"

    def exposed_start_server_B(self):
        """ Start accel-pppd Server B in Namespace B. """
        if (serverB.is_available()):
            return "Server B is already online."
        else:
            os.popen("sudo ip netns exec NamespaceB accel-pppd -d -c ../Accel-PPP-Modified/accel-pppd/accel-ppp_B.conf -p /var/run/accel-ppp-B.pid")
            return "Server B started"

    def exposed_stop_server_A(self):
        """ Stop accel-pppd Server A."""
        os.popen("accel-cmd -H 192.168.42.1 shutdown hard")
        return True

    def exposed_stop_server_B(self):
        """ Stop accel-pppd Server B. """
        os.popen("accel-cmd -H 192.168.43.1 shutdown hard")
        return True

    def exposed_start_client(self):
        """ Start the PPPoE client that is tying to connect to a PPPoE Server via interface veth-A-Client."""
        return os.popen("sudo pppoe-start").read()

    def exposed_stop_client(self):
        """ Stop the PPPoE client. """
        return os.popen("sudo pppoe-stop").read()

    def exposed_get_sessions_A(self):
        """ Get sessions of Server A. """
        return serverA.read_sessions()

    def exposed_get_sessions_B(self):
        """ Get sessions of Server B. """
        return serverB.read_sessions()

    def exposed_migrate_to_A(self, session: dict):
        """ Migrate [session] to server A."""
        serverA.write_session_safe(session)
        switch_route_session(session, serverA)

    def exposed_migrate_to_B(self, session: dict):
        """ Migrate [session] to server B."""
        serverB.write_session_safe(session)
        switch_route_session(session, serverB)

    def exposed_migrate_all_to_A(self, sessions: 'list[dict]'):
        """ Migrate all sessions of [sessions] to server A."""
        for session in sessions:
            serverA.write_session_safe(session)
            switch_route_session(session, serverA)

    def exposed_migrate_all_to_B(self, sessions: 'list[dict]'):
        """ Migrate all sessions of [sessions] to server B."""
        for session in sessions:
            serverB.write_session_safe(session)
            switch_route_session(session, serverB)

    def exposed_is_online_A(self):
        """ Returns availability of Server A. """
        if(serverA.online.value == 1):
            return True
        else:
            return False

    def exposed_is_online_B(self):
        """ Returns availability of Server B. """
        if(serverB.online.value == 1):
            return True
        else:
            return False

    def exposed_set_auto_migration(self, bool: bool):
        """ Change setting for automatically migrating sessions form server A to server B. """
        auto_migrate.value = bool

    def exposed_get_auto_migration(self):
        """ Get setting for automatically migrating sessions form server A to server B. """
        if(auto_migrate.value == 1):
            return True
        else:
            return False

    def exposed_write_dummy_sessions_A(self):
        """ Write dummy session to server A. """
        dummy_session = self.random_session()
        print()
        print("Writing dummy: ", dummy_session)
        print()
        return serverA.write_session_safe(dummy_session)

    def exposed_write_dummy_sessions_B(self):
        """ Write dummy session to server B. """
        dummy_session = self.random_session()
        return serverB.write_session_safe(dummy_session)

    def random_mac(self):
        """ Helper function to generate random mac address. Is not exposed via API. """
        return f"{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}"

    def random_ip(self):
        """ Helper function to generate random ip address. Is not exposed via API. """
        return f"{random.randint(1, 254)}.{random.randint(0, 254)}.{random.randint(0, 254)}.{random.randint(1, 254)}"

    def pseudo_random_ip(self):
        """ Helper function to generate a pseudo random ip address. Is not exposed via API. """
        return f"192.42.0.{random.randint(1, 254)}"

    def random_session(self):
        """ Helper function to generate random session. Is not exposed via API. """
        random_id = random.randint(1000, 10000)

        return {
            "sid": random_id,
            "username": f"dummy{random_id}",
            "ip": f"{self.random_ip()}",
            "peer_ip": f"{self.random_ip()}",
            "calling_station_id": f"{self.random_mac()}",   # PPPoE Client
            "called_station_id": f"{self.random_mac()}"     # PPPoE Server
        }


def session_in_array(session_A: dict, sessions_B: dict):
    """ Check if session_A is part of sessions_B. """
    # Go through all sessions in sessions_B (Server B) 
    for session_B in sessions_B["pppoe_states"]:
        # Check if session_A and session_B have session IDs
        if (("sid" not in session_A) or ("sid" not in session_B)):
            continue
        else:
            # Check if session_A already in Server B
            if(session_A['sid'] == session_B['sid']):
                #print(f"Session {session_A['sid']} already in {serverB.name}")
                return True
    else:
        False


def switch_route(server_A: PPPoE_Server, server_B: PPPoE_Server):
    """ ToDo: Function to reroute traffic if Server A fails. """
    print(f"Redirecting traffic from {server_A.name} to {server_B.name}")
    pass  # Add the switching of routes from Server A to Server B here.


def switch_route_session(session: dict, new_server: PPPoE_Server):
    """ ToDo: Function to reroute traffic of session to new server. """
    print(session)
    print(type(session))
    #print(f"Redirecting traffic of Session {session.username} to {new_server.name}")
    pass  # Add the switching of routes of session to new server.


def check_and_migrate(auto_migration: SynchronizedBase):
    """ Checks if servers are available and migrates Sessions from first server to the second. """

    sessions_A = serverA.read_sessions()
    sessions_B = serverB.read_sessions()

    print(f"{serverA.name}: {sessions_A}")
    print(f"{serverB.name}: {sessions_B}")

    # Detect if Server A is working
    if(len(sessions_A.keys()) == 0):
        switch_route(serverA, serverB)
        return False

    # Detect if Server B is working
    if(len(sessions_B.keys()) == 0):
        return False

    # Stop if auto_migration is False
    if(auto_migration.value == True):
        print(
            f"Automatically migrating sessions to {serverB.name} if necessary.")
    else:
        return False

    # Go through all sessions of server A
    for session_A in sessions_A["pppoe_states"]:
        response = serverB.write_session_safe(session_A)
        print(response)

    return True


def initial_setup():
    """ Initializes the servers. """
    print("Starting Setup.")

    global serverA
    global serverB

    # Config Server A
    serverA = PPPoE_Server("Server A", "veth-A-Client",
                           "192.168.42.1", Value('b', False))

    # Config Server B
    serverB = PPPoE_Server("Server B", "veth-B-Client",
                           "192.168.43.1", Value('b', False))

    print("Setup complete.")


def control_loop(auto_migrate: SynchronizedBase):
    """ Infinite loop to check the availability of the servers.
    If [auto_migrate] is True, then sessions are automatically copied from server A to server B.
    """
    print("Controller: Starting infinite loop.")
    while True:
        print("")
        try:
            check_and_migrate(auto_migrate)
        except ValueError as e:
            print(e)

        time.sleep(1)


if __name__ == "__main__":
    # Start initial setup
    initial_setup()

    # Start controller in separated process
    controller = Process(target=control_loop, args=(auto_migrate,))
    controller.start()

    # Start RPyC API. A thread is spawn for each connection.
    from rpyc.utils.server import ThreadedServer
    print("Starting RPyC API")
    t = ThreadedServer(ApiService, port=18861)
    t.start()
