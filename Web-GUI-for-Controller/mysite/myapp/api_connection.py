import rpyc
import ast


class APIConnection:
    """ Class to connect to the API of the Controller. """

    def __init__(self, host: str, port: int):
        """
        Constructor to initialise connection to Controller API.
        
        Parameters
        ----------
            host : str
                ip address of host
            port : int
                port number
        """
        self.host = host
        self.port = port

        # Connect to Controller.py
        try:
            self.conn = rpyc.connect(self.host, self.port)
        except:
            print(f'RPyC: Unable to connect to {self.host}:{self.port} -> Controller.py is offline.')
            self.conn = None
            self.online = False
        else:
            print(f'RPyC: Successful connection to {self.host}:{self.port} -> Controller.py is online.')
            self.online = True

    def __str__(self):
        return f"RPyC API Connection to host={self.host} and port={self.port}"

    def restart_connection(self):
        try:
            self.conn = rpyc.connect(self.host, self.port)
        except:
            print(f'RPyC: Unable to connect to {self.host}:{self.port} -> Controller.py is offline.')
            self.online = False
            return False
        else:
            print(f'RPyC: Successful connection to {self.host}:{self.port} -> Controller.py is online.')
            self.online = True
            return True

    def start_server_A(self):
        """ Start accel-pppd Server A in Namespace A. """
        try:
            return self.conn.root.start_server_A()
        except Exception as error:
            print(error)
            print('error start serverA')

    def start_server_B(self):
        """ Start accel-pppd Server B in Namespace B. """
        try:
            return self.conn.root.start_server_B()
        except:
            print('error start serverB')

    def stop_server_A(self):
        """ Stop accel-pppd Server A."""
        try:
            return self.conn.root.stop_server_A()
        except Exception as error:
            print(error)

    def stop_server_B(self):
        """ Stop accel-pppd Server B. """
        try:
            return self.conn.root.stop_server_B()
        except Exception as error:
            print(error)

    def start_client(self):
        """ Start the PPPoE client that is tying to connect to a PPPoE Server via interface veth-A-Client."""
        try:
            return self.conn.root.start_client()
        except Exception as error:
            print(error)

    def stop_client(self):
        """ Stop the PPPoE client. """
        try:
            return self.conn.root.stop_client()
        except Exception as error:
            print(error)

    def get_sessions_A(self):
        """ Get sessions of Server A. """
        try:
            response = self.conn.root.get_sessions_A()
        except EOFError as error:
            print(error)
            result = self.restart_connection()
            if (result):
                response = self.conn.root.get_sessions_A()
            else:
                response = {}
        except Exception as error:
            print(error)
            self.restart_connection()
            response = {}
        return ast.literal_eval(str(response))

    def get_sessions_B(self):
        """ Get sessions of Server B. """
        try:
            response = self.conn.root.get_sessions_B()
        except EOFError as error:
            print(error)
            result = self.restart_connection()
            if (result):
                response = self.conn.root.get_sessions_B()
            else:
                response = {}
        except Exception as error:
            print(error)
            self.restart_connection()
            response = {}
        return ast.literal_eval(str(response))

    def migrate_to_A(self, session):
        """ Migrate [session] to server A."""
        try:
            return self.conn.root.migrate_to_A(session)
        except Exception as error:
            print(error)

    def migrate_to_B(self, session):
        """ Migrate [session] to server B."""
        try:
            return self.conn.root.migrate_to_B(session)
        except Exception as error:
            print(error)

    def migrate_all_to_A(self, sessions):
        """ Migrate all sessions of [sessions] to server A."""
        try:
            return self.conn.root.migrate_all_to_A(sessions)
        except Exception as error:
            print(error)

    def migrate_all_to_B(self, sessions):
        """ Migrate all sessions of [sessions] to server B."""
        try:
            return self.conn.root.migrate_all_to_B(sessions)
        except Exception as error:
            print(error)

    def is_online_A(self):
        """ Returns availability of Server A. """
        try:
            return self.conn.root.is_online_A()
        except Exception as error:
            print(error)
            return False

    def is_online_B(self):
        """ Returns availability of Server B. """
        try:
            return self.conn.root.is_online_B()
        except Exception as error:
            print(error)
            return False

    def get_auto_migration(self):
        """ Get setting for automatically migrating sessions form server A to server B. """
        try:
            return self.conn.root.get_auto_migration()
        except Exception as error:
            print(error)
            return False

    def set_auto_migration(self, auto_migrate: bool):
        """ Change setting for automatically migrating sessions form server A to server B. """
        try:
            return self.conn.root.set_auto_migration(auto_migrate)
        except Exception as error:
            print(error)

    def write_dummy_sessions_A(self):
        """ Write dummy session to server A. """
        try:
            print('write dummyA')
            self.conn.root.write_dummy_sessions_A()
        except Exception as error:
            print('write dummysession A error')
            print(error)

    def write_dummy_sessions_B(self):
        """ Write dummy session to server B. """
        try:
            self.conn.root.write_dummy_sessions_B()
            print('write dummyB')
        except Exception as error:
            print('write dummyB error')
            print(error)
