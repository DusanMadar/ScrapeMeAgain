from random import randint

from scrapemeagain.dockerized.ipchanger import DockerizedTorIpChanger


class FakeDockerizedTorIpChanger(DockerizedTorIpChanger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._real_ip = "127.0.0.1"

    def get_current_ip(self):
        # Credits: https://stackoverflow.com/a/21014713/4183498.
        return ".".join(str(randint(0, 255)) for _ in range(4))

    def _obtain_new_ip(self):
        # We don't want to change IP address while testing.
        pass
