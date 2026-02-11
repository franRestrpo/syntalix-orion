import subprocess, sys

def cmd_exists(cmd: str):
    return subprocess.call(
        f"which {cmd}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ) == 0

def run(cmd: list):
    subprocess.run(cmd, check=True)
