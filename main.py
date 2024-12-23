# server.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import uuid
import datetime
import logging

app = Flask(__name__)
CORS(app)

clients = {}
commands = {}
command_results = {}


available_commands = {
    'system_info': {
        'name': 'System Information',
        'command': 'systeminfo',
        'description': 'Get system information'
    },
    'process_list': {
        'name': 'Process List',
        'command': 'tasklist',
        'description': 'List running processes'
    },
    'network_connections': {
        'name': 'Network Connections',
        'command': 'netstat -an',
        'description': 'Show network connections'
    },
    'disk_space': {
        'name': 'Disk Space',
        'command': 'dir',
        'description': 'Show disk space usage'
    },
    'memory_info': {
        'name': 'Memory Information',
        'command': 'wmic OS get FreePhysicalMemory',
        'description': 'Show memory usage'
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
        
    command = available_commands[command_data['command_type']]['command']
    
    commands[command_id] = {
        'client_id': command_data['client_id'],
        'command': command,
        'command_type': command_data['command_type'],
        'timestamp': datetime.datetime.now().isoformat(),
        'executed': False
    }
    
    logging.info(f"New command added: {command_id}")
    return jsonify({'command_id': command_id})

@app.route('/result/<command_id>', methods=['POST'])
def submit_result(command_id):
    if command_id in commands:
        result_data = request.get_json()
        command_results[command_id] = {
            'output': result_data['output'],
            'timestamp': datetime.datetime.now().isoformat()
        }
        commands[command_id]['executed'] = True
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