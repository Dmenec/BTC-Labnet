from typing import List, Dict

import hashlib
import base58
import json
import time
import struct
import socket
import json
import time
import random
import urllib.request
import base64
import argparse

SERVER_ADDRESS = ('localhost', 5000)

# Define parameters for the RPC.
parameters = {
    "host": "127.0.0.1",
    "port": "8332",
    "rpcuser": "bitcoin",
    "rpcpass": "password",
    "rpcurl": "http://127.0.0.1:8332", 
    "prev_hash": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f", # Genesis block
    "wallet_address": "1UABc9HYFdcpjKw5dLaBGk47DPuzo7QvU", # Define here the address that will receive the bitcoins
}

block_template = {
    "coinbasevalue": 5000000000,
    "height": 0,
    "transactions": [],
    "merkleroot": "",
    "nonce": 0, 
    "version": 536870912,
    "previousblockhash": parameters["prev_hash"],
    "curtime": int(time.time()),
    "bits": "1d00ffff",
}

state = {
    "last_block_hash": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
    "block_height": 0, 
    "difficulty": 1
}

### SERVER FUNCTIONS ### 

def get_blockchain_state():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(SERVER_ADDRESS)
    request = json.dumps({"action": "get_state"}).encode()
    client.send(request)
    response = client.recv(1024)
    client.close()
    return json.loads(response.decode())

def update_blockchain_state():
    submission_str = create_submission_str(block_template) 

    print(f"[---|+  BLOCK  +|---]\n{block_template}\n")

    # Build RPC data
    rpc_id = random.getrandbits(32)
    data = json.dumps({
        "id": rpc_id,
        "method": "submitblock",
        "params": [submission_str]
    }).encode()

    rpc_id2 = random.getrandbits(32)
    data2 = json.dumps({
        "id": rpc_id2, 
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

    request2 = urllib.request.Request(
        parameters["rpcurl"],
        data2,
        {"Authorization": b"Basic " + auth}
    )

    # Send RPC request and wait for the answer
    try:
        print("Sending block ...")
        with urllib.request.urlopen(request) as f:
            response = json.loads(f.read())

        with urllib.request.urlopen(request2) as f:
            response = json.loads(f.read())
            print("New Blockchain State")
            state["block_height"] = response["result"]["blocks"]
            print("Height: ", response["result"]["blocks"])
            state["last_block_hash"] = response["result"]["bestblockhash"]
            print("Last Hash: ", response["result"]["bestblockhash"])
            state["difficulty"] = response["result"]["difficulty"]
            print("Difficulty: ", response["result"]["difficulty"])

        if response.get("error") is None:
            print("Block sended!")
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(SERVER_ADDRESS)
            request = json.dumps({"action": "update_state", "state": state}).encode()
            client.send(request)
            response = client.recv(1024)
            client.close()
            return response.decode() == 'ACK'
        else:
            print("Error submitblock:", response["error"])
            return False
    except urllib.error.URLError as e:
        print("Error connecting with RPC server:", e)
        return False
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        return False


### AUXILIAR FUNCTIONS ###

def difficulty_to_target(difficulty):
    max_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
    adjusted_difficulty = 1 / difficulty
    target = int(max_target * adjusted_difficulty)
    return format(target, '064x')


def get_le_hex(value: int, width: int) -> str:
    return value.to_bytes(width, byteorder='little').hex()


def get_le_var_hex(value: int) -> str:
    if value < 0xfd:
        return get_le_hex(value, 1)
    if value <= 0xffff:
        return "fd" + get_le_hex(value, 2)
    if value <= 0xffffffff:
        return "fe" + get_le_hex(value, 4)
    return "ff" + get_le_hex(value, 8)

def encode_coinbase_height(height: int) -> str:
    width = (height.bit_length() + 7) // 8
    return bytes([width]).hex() + get_le_hex(height, width)

def calculate_nonce_range(arg):
    start_nonce = (arg - 1) * 25 + 1
    end_nonce = arg * 25
    return start_nonce, end_nonce

def sha256_double_hash(target: str) -> str:
    return hashlib.sha256(
        hashlib.sha256(target).digest()
    ).digest()[::-1]

def create_submission_str(block: Dict) -> str:
    submission = (
        calc_block_header(block).hex() 
        + get_le_var_hex(len(block['transactions']))
    )
    for tx in block['transactions']:
        submission += tx['data']
    return submission


### COINBASE CREATION ###

def create_coinbase(
    coinbase_value: int, 
    coinbase_text: str, 
    block_height: int,
    wallet_address: str
) -> str:
    op_return_script = "6a" + get_le_var_hex(len(coinbase_text)) + coinbase_text
    
    coinbase_script = encode_coinbase_height(block_height) + op_return_script
    pubkey_script = "76a914" + base58.b58decode_check(wallet_address)[1:].hex() + "88ac"
    return (
        "0100000001" + "0" * 64 + "ffffffff" 
        + get_le_var_hex(len(coinbase_script) // 2) 
        + coinbase_script + "ffffffff01" 
        + get_le_hex(coinbase_value, 8)
        + get_le_var_hex(len(pubkey_script) // 2)
        + pubkey_script
        + "00000000"
    )


### MODIFY BLOCK TEMPLATE ###

def process_block_template(block_template, parameters):
    
    coinbase_text: str = "4e6f772c20594f5520686176652074686520504f574552210d0a" 

    coinbase_data = create_coinbase(
        coinbase_value=block_template['coinbasevalue'],  
        coinbase_text=coinbase_text, 
        block_height=block_template['height'],
        wallet_address=parameters["wallet_address"], 
    )
    coinbase_hash = sha256_double_hash(bytes.fromhex(coinbase_data)).hex()
    
    block_template['transactions'] = [{
        'data': coinbase_data,
        'hash': coinbase_hash
    }]

    block_template['merkleroot'] = calc_merkle_root(
        [transaction['hash'] for transaction in block_template['transactions']]
    )

### AUXILIAR FUNCTIONS FOR BLOCK CREATION ###

def calc_merkle_root(transactions: List[str]) -> str:
    be_hashes = [
        bytes.fromhex(transaction)[::-1] 
        for transaction in transactions
    ]

    while len(be_hashes) > 1:

        if len(be_hashes) % 2 != 0:
            be_hashes.append(be_hashes[-1])

        for i in range(len(be_hashes) // 2):
            concat_hash = be_hashes[i * 2] + be_hashes[i * 2 + 1]
            be_hash = hashlib.sha256(hashlib.sha256(concat_hash).digest()).digest()
            be_hashes[i] = be_hash
        be_hashes = be_hashes[:len(be_hashes) // 2]
    return be_hashes[0][::-1].hex()

def calc_block_header(block: Dict) -> bytes:
    version_bytes = struct.pack("<L", block["version"])
    prev_block_hash_bytes = bytes.fromhex(block["previousblockhash"])[::-1]
    merkle_root_bytes = bytes.fromhex(block["merkleroot"])[::-1]
    timestamp_bytes = struct.pack("<L", block["curtime"])
    bits_bytes = bytes.fromhex(block["bits"])[::-1]
    nonce_bytes = struct.pack("<L", block["nonce"])

    block_header = (
        version_bytes 
        + prev_block_hash_bytes 
        + merkle_root_bytes 
        + timestamp_bytes 
        + bits_bytes 
        + nonce_bytes
    )

    return block_header


### MINER ###

def mine_blocks(start_nonce, end_nonce, rstart_nonce, rend_nonce, target, parameters, stop_on_block=False):
    nonce = start_nonce
    target = bytes.fromhex(target)
    
    state = get_blockchain_state()

    while True:
        state = get_blockchain_state()
        
        if state["last_block_hash"] != block_template["previousblockhash"]:
            print("New Block Detected! Updating block template ...")
            block_template["previousblockhash"] = state["last_block_hash"]
            block_template["height"] = state["block_height"]
            target = difficulty_to_target(state["difficulty"])
            target = bytes.fromhex(target)
            block_template["curtime"] = int(time.time())
            process_block_template(block_template, parameters)
            start_nonce = rstart_nonce
            nonce = start_nonce
            end_nonce = rend_nonce
            
        while nonce <= end_nonce:
            block_template['nonce'] = nonce
            block_header = calc_block_header(block_template)
            block_hash = sha256_double_hash(block_header)

            if block_hash.hex() < target.hex():
                print("¡Hash valid found!")
                print(f"Nonce: {nonce}")
                print(f"Block Hash: {block_hash.hex()}")
                print(f"Curtime: {block_template['curtime']}\n")
                
                if update_blockchain_state():
                    if stop_on_block:
                        print("Stopping mining as --stop-on-block was provided.")
                        return
                    break

            nonce += 1

            if nonce > 4294967190:
                print("No blocks found with current curtime, updating it ...")
                block_template['curtime'] = int(time.time())
                print(f"New Curtime: {block_template['curtime']}")
                process_block_template(block_template, parameters)
                start_nonce = rstart_nonce
                nonce = start_nonce
                end_nonce = rend_nonce

        start_nonce += 100
        nonce = start_nonce
        end_nonce += 100


#####################################
#               MAIN                #
#####################################

if __name__ == "__main__":

    # The nonce range refers to the range of numbers that each miner (or daemon) will use 
    # in their attempts to find a valid block hash. Each miner works on a specific subset 
    # of this range. For example, if the total nonce range is from 0 to 1,000,000 and 
    # there are four miners, each miner might be assigned a range such as 0-250,000, 
    # 250,001-500,000, 500,001-750,000, and 750,001-1,000,000. This distribution of work 
    # helps to ensure that the mining process is more efficient and that the workload is 
    # balanced among all miners.

    parser = argparse.ArgumentParser(description="Bitcoin Mining Script")
    parser.add_argument('range', type=int, choices=[1, 2, 3, 4], help="Nonce range to be used by the miner")
    parser.add_argument('--stop-on-block', action='store_true', help="Stop the script when a valid block is found")

    args = parser.parse_args()

    state = get_blockchain_state()

    # Define parameters for the block template.
    parameters["prev_hash"] = state["last_block_hash"]
    target = difficulty_to_target(state["difficulty"])
    block_template["height"] = state["block_height"]
    
    process_block_template(block_template, parameters)
    start_nonce, end_nonce = calculate_nonce_range(args.range)

    mine_blocks(start_nonce, end_nonce, start_nonce, end_nonce, target, parameters, stop_on_block=args.stop_on_block)




