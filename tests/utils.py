import imp
import os

from tests import REPO_DIR


def import_docker_compose():
    module_name = "scrapemeagain-compose"
    module_path = os.path.join(REPO_DIR, "scripts")
    f, filename, description = imp.find_module(module_name, [module_path])

    return imp.load_module(module_name, f, filename, description)
