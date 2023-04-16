
# Django view functions that handle user requests

from django.shortcuts import render
import os
import ast
import time
from . import api_connection as api_conn

# Global variables containing the state of interfaces an controller
interface_created = 'no'
controller_started = 'no'

# Connection to the API of Controller
api = api_conn.APIConnection("localhost", 18861)


def index(request):
    """ Gets the latest state of servers and returns rendered GUI """

    # Get sessions Server A
    sessions_A = api.get_sessions_A()
    if len(sessions_A.keys()) != 0:
        sessions_A = sessions_A['pppoe_states']

    # Get sessions Server B
    sessions_B = api.get_sessions_B()
    if len(sessions_B.keys()) != 0:
        sessions_B = sessions_B['pppoe_states']

    context = {
        'api_online': api.online,
        'sessions_A': sessions_A,
        'sessions_B': sessions_B,
        'is_online_A': api.is_online_A(),
        'is_online_B': api.is_online_B(),
        'auto_migration': api.get_auto_migration(),
    }

    return render(request, 'index.html', context)


def create_interface(request):
    """ Creates virtual network environment including namespaces and interfaces """
    # ToDo: Change absolute path to relative path 
    os.chdir("/home/minhpham/labproject-t6-wise22-23-code-main/Accel-PPP-Modified")
    global interface_created
    if interface_created == 'no':
        interface_created = os.popen('./create_namespaces.sh').read()
        return index(request)
    else:
        return index(request)


def run_controller(request):
    """ Starts the controller """
    global controller_started
    # ToDo: Change absolute path to relative path 
    os.chdir("/home/minhpham/labproject-t6-wise22-23-code/Controller")
    if controller_started == 'no':
        controller_started = 'yes'
        os.popen("python3 Controller.py")
        return index(request)
    else:
        print('Controller already started!')
        return index(request)


def start_server_A(request):
    """ Starts server A """
    if api.is_online_A() == False:
        api.start_server_A()
    elif api.is_online_A == True:
        print('Server A is already online!')
    return index(request)


def start_server_B(request):
    """ Starts server B """
    if api.is_online_B() == False:
        api.start_server_B()
    elif api.is_online_B() == True:
        print('Server B is already online!')
    return index(request)


def stop_server_A(request):
    """ Stops server A """
    if api.is_online_A() == True:
        api.stop_server_A()
        time.sleep(1)
    elif api.is_online_A() == False:
        print('Server A is already offline!')
    return index(request)


def stop_server_B(request):
    """ Stops server B """
    if api.is_online_B() == True:
        api.stop_server_B()
        time.sleep(1)
    elif api.is_online_B() == False:
        print('Server B is already offline!')
    return index(request)


def start_client(request):
    """ Starts rp-pppoe client tying to connect to Server A """
    api.start_client()
    return index(request)


def stop_client(request):
    """ Stops PPPoE client """
    api.stop_client()
    return index(request)


def migrate_all_to_B(request):
    """ Migrates all sessions from Server A to Server B """
    sessions_A = api.get_sessions_A()

    if len(sessions_A.keys()) != 0:
        sessions_A = sessions_A['pppoe_states']

    api.migrate_all_to_B(sessions_A)
    return index(request)


def migrate_all_to_A(request):
    """ Migrates all sessions from Server B to Server A """
    sessions_B = api.get_sessions_B()

    if (len(sessions_B.keys()) != 0):
        sessions_B = sessions_B['pppoe_states']

    api.migrate_all_to_A(sessions_B)
    return index(request)


def migrate_to_A(request):
    """ Migrates selected session to Server A """
    session = request.POST['session']
    session_dict = ast.literal_eval(session)
    api.migrate_to_A(session_dict)
    return index(request)


def migrate_to_B(request):
    """ Migrates selected session to Server B """
    session = request.POST['session']
    session_dict = ast.literal_eval(session)
    api.migrate_to_B(session_dict)
    return index(request)


def set_auto_migration_on(request):
    """ Turns on the automatic migration of sessions form Server A to Server B """
    api.set_auto_migration(True)
    return index(request)


def set_auto_migration_off(request):
    """ Turns off the automatic migration of sessions form Server A to Server B """
    api.set_auto_migration(False)
    return index(request)


def write_dummy_sessions_A(request):
    """ Adds a dummy session to Server A """
    api.write_dummy_sessions_A()
    return index(request)


def write_dummy_sessions_B(request):
    """ Adds a dummy session to Server B """
    api.write_dummy_sessions_B()
    return index(request)
