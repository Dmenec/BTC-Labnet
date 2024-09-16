import hashlib
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256, RIPEMD160
import base58

private_key = RSA.generate(2048)

def generate_address(counter):
    public_key = private_key.publickey()
    
    public_key_data = public_key.export_key() + str(counter).encode()

    sha256_hash = SHA256.new(public_key_data).digest()
    ripemd160_hash = RIPEMD160.new(sha256_hash).digest()

    network_byte = b'\x00' + ripemd160_hash

    checksum = hashlib.sha256(hashlib.sha256(network_byte).digest()).digest()[:4]
    
    address_bytes = network_byte + checksum
    address = base58.b58encode(address_bytes).decode('utf-8')
    
    return address

def find_address_with_text():
    desired_prefix = "1UAB"
    addresses_generated = 0
    counter = 0

    while True:
        address = generate_address(counter)
        addresses_generated += 1
        counter += 1

        if address.startswith(desired_prefix):
            print(f"Found address: {address} starting with {desired_prefix}")
            break  

if __name__ == "__main__":
    find_address_with_text()
