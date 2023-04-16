from multiprocessing.sharedctypes import SynchronizedBase
from multiprocessing import Process
from rpyc.utils.server import ThreadedServer
import sys
import time


import Controller
from Controller import switch_route, initial_setup, auto_migrate

"""
Script used to evaluate Controller.py by measuring the duration 
X number of sessions need to be migrated from A to B.

How to use it?
1. Make sure two accel-ppp servers are running in two separate Namespace as described in README.md.
2. Make sure the two accel-ppp servers currently do not have any sessions.
3. Start the web GUI
4. Start this script 'python3 Evaluation.py X' where X is the number of sessions to be migrated.
5. In the web GUI you will see X Sessions in Server A.
6. Turn on automatic migration to start the measurements and migrate the sessions.
7. The script will migrate the sessions and stop after returning the duration.
8. (The API will continue to work, because its running in a separat process)
"""

def control_loop_for_evaluation(auto_migrate: SynchronizedBase, nb_session: int):
    """ Infinite loop to check the availability of the servers.
    If [auto_migrate] is True, then sessions are automatically copied from server A to server B.
    """
    print("Controller: Starting infinite loop.")
    while True:
        print("")
        try:
            check_and_migrate_for_evaluation(auto_migrate, nb_session)
        except ValueError as e:
            print(e)

        time.sleep(1)

def check_and_migrate_for_evaluation(auto_migration: SynchronizedBase, nb_session: int):
    """ Checks if servers are available and migrates Sessions from first server to the second. """

    sessions_A = Controller.serverA.read_sessions()
    sessions_B = Controller.serverB.read_sessions()

    print(f"{Controller.serverA.name}: {sessions_A}")
    print(f"{Controller.serverB.name}: {sessions_B}")

    # Detect if Server A is working
    if(len(sessions_A.keys())==0):
        switch_route(Controller.serverA, Controller.serverB)
        return False

    # Detect if Server B is working
    if(len(sessions_B.keys())==0):
        return False

    # Stop if auto_migration is False
    if(auto_migration.value == True):
        print(
            f"Automatically migrating sessions to {Controller.serverB.name} if necessary.")
    else:
        return False

    # Start measuring time
    start_time = time.time()

    # Go through all sessions of server A
    for session_A in sessions_A["pppoe_states"]:
        response = Controller.serverB.write_session_safe(session_A)
        print(response)

    # Stop measuring time and print the duration
    end_time = time.time() # Note: The time to call time.time() is approximately 2.384185791015625e-07 sec. It can be ignored.
    duration = end_time - start_time
    print(f"\n\033[1;32m Duration {duration} seconds to migrate {nb_session} sessions\n")
    quit()


def test_setup(nb_session: int):
    """ Setup test by creating [nb_session] dummy sessions on Server A."""

    for i in range(nb_session):
        test = Controller.ApiService()
        test.exposed_write_dummy_sessions_A()


if __name__ == "__main__":

    # Try to set the number of sessions to be migrated with argument, else it will be 1.
    try:
        nb_session = int(sys.argv[1:].pop())
        if (nb_session > 4) or (nb_session < 1):
            print('Argument can only be an integer between: 1 < argument < 5')
            quit()
    except:
        nb_session = 1   

    # Start initial setup
    initial_setup()

    # Create dummy sessions for test case
    test_setup(nb_session)

    # Start controller in separated process
    controller = Process(target=control_loop_for_evaluation, args=(auto_migrate, nb_session,))
    controller.start()

    # Start RPyC API. A thread is spawn for each connection.
    print("Starting RPyC API")
    t = ThreadedServer(Controller.ApiService, port=18861)
    t.start()