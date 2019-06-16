from datetime import datetime
import json
import os

from requests import get
from bs4 import BeautifulSoup

from scrapemeagain.utils.alnum import DATE_FORMAT, get_current_date


USER_AGENTS_URL = (
    "https://techblog.willshouse.com/2012/01/03/most-common-user-agents/"
)


def _scrape_user_agents():
    response = get(USER_AGENTS_URL)
    soup = BeautifulSoup(response.content, "html.parser")

    user_agents = soup.findAll("td", {"class": "useragent"})
    user_agents = [user_agent.text for user_agent in user_agents]

    if not user_agents:
        raise ValueError("No user agents found!")

    return user_agents


def _save_user_agents(user_agents, user_agents_file):
    data = {"date": get_current_date(), "useragents": user_agents}

    with open(user_agents_file, "w") as f:
        json.dump(data, f, indent=2)


def _scrape_and_save_user_agents(user_agents_file):
    user_agents = _scrape_user_agents()
    _save_user_agents(user_agents, user_agents_file)

    return user_agents


def _user_agents_are_old(user_agents):
    scrape_date = datetime.strptime(user_agents.get("date"), DATE_FORMAT)
    today = datetime.now()

    delta = today - scrape_date

    return delta.days > 30


def get_user_agents(main__file__):
    mains_dir = os.path.dirname(os.path.abspath(main__file__))
    user_agents_file = os.path.join(mains_dir, "useragents.json")

    if not os.path.exists(user_agents_file):
        return _scrape_and_save_user_agents(user_agents_file)

    with open(user_agents_file, "r") as f:
        user_agents = json.load(f)

    if _user_agents_are_old(user_agents):
        return _scrape_and_save_user_agents(user_agents_file)

    return set(user_agents["useragents"])
