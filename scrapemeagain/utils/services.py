"""Backbone services management."""


from getpass import getpass
import subprocess
import sys


SERVICES = ("privoxy", "tor")
COMMAND = ("sudo", "-S", "service")

password_manager = {"root_password": ""}


def toggle_backbone_services(action):
    """
    Start/stop backbone services required by the scraper.

    :argument action: 'start' or 'stop'
    :type string_ts: str
    """
    if not password_manager["root_password"]:
        password_manager["root_password"] = getpass().strip()

    for service in SERVICES:
        command = list(COMMAND)
        command.extend((service, action))

        service_action = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        service_action.communicate(
            (password_manager["root_password"] + "\n").encode()
        )
        service_action.wait()

        if service_action.returncode != 0:
            sys.exit("Failed to {0} service {1}".format(action, service))


def start_backbone_services():
    toggle_backbone_services("start")


def stop_backbone_services():
    toggle_backbone_services("stop")
