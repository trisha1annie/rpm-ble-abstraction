import subprocess
import time
from pathlib import Path


class Simulator:

    def __init__(self, simulator_dir):
        self.simulator_dir = Path(simulator_dir)
        self.process = None

    def start_simulator(self, config):
        self.process = subprocess.Popen(
            ["npm", "start", config],
            cwd=self.simulator_dir,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        time.sleep(2)

    def send_command(self, command, characteristic, values=None):

        if self.process is None or self.process.stdin is None:
            raise RuntimeError("Simulator is not running")

        values = values or []

        command_string = (
            f"{command} {characteristic} {' '.join(map(str, values))}\n"
        )

        self.process.stdin.write(command_string)
        self.process.stdin.flush()
        if self.process.stdout:
            response = self.process.stdout.readline()
            print("[SIMULATOR]", response)

        return command_string.strip()

    def stop_simulator(self):

        if self.process and self.process.stdin:
            self.process.stdin.write("exit\n")
            self.process.stdin.flush()
            self.process.terminate()


if __name__ == "__main__":

    client = Simulator(
        "/Users/trishakuruvilla/Desktop/uni/thesis/rpm-ble-abstraction/testing/ble-simulator"
    )

    client.start_simulator("./configs/oxi.yaml")

    time.sleep(2)
    client.send_command("notify", "oxi", [98, 72])

    time.sleep(5)
    client.send_command("switch", "3")

    time.sleep(2)
    client.send_command("notify", "weight", [75.5, "kg"])

    time.sleep(5)
    client.send_command("switch", "1")

    time.sleep(2)
    client.send_command("notify", "bp", [120, 80, 72])

    time.sleep(5)
    client.stop_simulator()