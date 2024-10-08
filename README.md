# BTC Labnet: Creating a Parallel Bitcoin Mainnet for Controlled Testing

## Introduction

BTC Labnet is a project developed by the Blockchain and Cryptocurrency Research Group at the Autonomous University of Barcelona. This project allows for controlled testing of the Bitcoin network by creating a parallel mainnet using Docker containers. 

The main goal is to provide a safe environment for testing without connecting to the real Bitcoin network.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Setup Process](#setup-process)
- [Configuration](#configuration)
- [Mining Blocks](#mining-blocks)
- [Contributing](#contributing)
  
## Features

- Run multiple Bitcoin nodes in an isolated Docker network.
- Custom consensus rules, including SegWit and Taproot support from block 0.
- Easy setup and management using shell scripts.
- Integration with a Stratum mining pool for efficient mining.

## Getting Started

To get started, you'll need to have [Docker](https://www.docker.com/) installed on your machine. 

### Prerequisites

- Docker (v20.10 or higher recommended)
- Basic knowledge of Bitcoin Core and Docker

## Installation

### Method 1: Download the Image from GitHub Container Registry

You can directly pull the pre-built Docker image and run the setup script without building the image from source. Follow these steps:

1. Pull the image from the GitHub Container Registry:

   ```bash
   docker pull ghcr.io/dmenec/btc-labnet:1.0
   ```

2. Clone the repository:

   ```bash
   git clone https://github.com/Dmenec/BTC-Labnet.git
   cd BTC-Labnet
   ```
3. Run the script to set up Docker containers (commenting out the build step):

  ```bash
  ./start.sh
  ```

### Method 2: Build from Source

Follow these steps to build the image from source:

1. Clone the repository:

  ```bash
  git clone https://github.com/Dmenec/BTC-Labnet.git
  cd BTC-Labnet
  ```

2. Run the script to set up Docker containers:

  ```bash
  ./start.sh
  ```

After execution, three interconnected Bitcoin nodes (bc-node1, bc-node2, and bc-node3) will be created.

## Setup Process

### Building a Customized Docker Image for Bitcoin-Core

1. **Modify Bitcoin-Core:** Adjust the Bitcoin-Core code to enable SegWit and Taproot.
2. **Create a Dockerfile:** Use your own `Dockerfile` to build your custom Bitcoin-Core image.
3. **Build the Docker Image:** Run the following command:

   ```bash
   docker build -t isolated-bitcoin:1.0 .
   ```

### Setting Up the Docker Network

Create a Docker bridge network:

```bash
docker network create -d bridge bitcoin-network
```

### Running Bitcoin Nodes

Start your Bitcoin node:

```bash
docker run -it -d --network bitcoin-network --name bitcoin-node1 isolated-bitcoin:1.0 -printtoconsole
```

### Configuring Node Connectivity

Ensure all nodes can connect properly by updating the `bitcoin.conf` file of each node with the IP address of the router node.

## Configuration

The `bitcoin.conf` file is crucial for customizing your node properties. Key settings include:

- `addnode=<IP_ADDRESS>`: Add the router node's IP.
- `rpcbind=0.0.0.0`: Listen on all available network interfaces.
- `rpcport=8332`: Default RPC port.
- `rpcuser=<username>` and `rpcpassword=<password>`: Set up RPC authentication.
- `server=1`: Enable RPC commands.

## Mining Blocks

To mine blocks, you can use this command inside one of the nodes. 

```bash
cd home/bitcoin/.bitcoin
./start_mining.sh
```

For a more efficient mining process, integrate with a Stratum mining pool using the [Bitaxe miner](https://bitaxe.org/).

## Contributing

Contributions are more than welcome! :) 
Please open an issue or submit a pull request for any enhancements or bug fixes.
