import subprocess

class CloudflareTunnel:
    def __init__(self, name="vynx-lite", port=7860):
        self.name = name
        self.port = port
        self.proc = None

    def start(self):
        if self.proc and self.proc.poll() is None:
            return True
        self.proc = subprocess.Popen(["cloudflared", "tunnel", "--url", f"http://localhost:{self.port}"])
        return True

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc = None
