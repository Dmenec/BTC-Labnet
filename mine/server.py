import socket
import threading
import json
import os
import random
import urllib.request
import base64
import urllib.error

STATE_FILE = "blockchain_state.json"
SERVER_ADDRESS = ('localhost', 5000)

state = {
    "last_block_hash": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
    "block_height": 0, 
    "difficulty": 1
}

# Define parameters for the RPC.
parameters = {
    "host": "127.0.0.1",
    "port": "8332",
    "rpcuser": "bitcoin",
    "rpcpass": "password",
    "rpcurl": "http://127.0.0.1:8332", 
    "prev_hash": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
    "wallet_address": "5361746F736869204E616B616D6F746F210A",
}

def load_first_blockchain_state(): 
    rpc_id = random.getrandbits(32)
    data = json.dumps({
        "id": rpc_id, 
        "method": "getblockchaininfo", 
        "params": []
    }).encode()

    auth = base64.b64encode(bytes(
        parameters["rpcuser"] + ":" + parameters["rpcpass"], 
        "utf8"
    ))

    request = urllib.request.Request(
        parameters["rpcurl"], 
        data, 
        {"Authorization": b"Basic " + auth}
    )

    try:
        with urllib.request.urlopen(request) as f:
            response = json.loads(f.read())
            print("Inital Blockchain State:")
            state["block_height"] = response["result"]["blocks"]
            print("Height: ", response["result"]["blocks"])
            state["last_block_hash"] = response["result"]["bestblockhash"]
            print("Last Hash: ", response["result"]["bestblockhash"])
            state["difficulty"] = response["result"]["difficulty"]
            print("Difficulty: ", response["result"]["difficulty"])
            save_blockchain_state()
            
    except urllib.error.URLError as e:
        print("Error al conectar con el servidor RPC:", e)
    except json.JSONDecodeError as e:
        print("Error al decodificar la respuesta JSON:", e)
    except KeyError as e:
        print("Error al encontrar el resultado en la respuesta:", e)
    
    return state

def load_blockchain_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return state

def save_blockchain_state():
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def handle_client_connection(client_socket):
    global state
    try:
        request = client_socket.recv(1024)
        data = json.loads(request.decode())

        if data['action'] == 'get_state':
            client_socket.send(json.dumps(state).encode())
        elif data['action'] == 'update_state':
            state = data['state']
            save_blockchain_state()
            client_socket.send(b'ACK')
    except Exception as e:
        print(f"Error handling client connection: {e}")
    finally:
        client_socket.close()

def start_server():
    global state
    state = load_first_blockchain_state()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(SERVER_ADDRESS)
    server.listen(5)
    print(f'Server listening on {SERVER_ADDRESS}')
    print("Blockchain State: ", state)

    while True:
        client_sock, _ = server.accept()
        client_handler = threading.Thread(
            target=handle_client_connection,
            args=(client_sock,)
        )
        client_handler.start()

def update_blockchain_state(new_state):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(SERVER_ADDRESS)
        request = json.dumps({"action": "update_state", "state": new_state}).encode()
        client.send(request)
        response = client.recv(1024)
    finally:
        client.close()
    return response.decode() == 'ACK'

if __name__ == "__main__":
    start_server()
