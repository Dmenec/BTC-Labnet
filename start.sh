#!/bin/bash

docker network create -d bridge bitcoin_network

docker build -t bitcoin .


# Port forwarding to connect from external source to our private network
docker run -it -d --network bitcoin_network --name bc-node1 -p 8332:8332 bitcoin -printtoconsole -txindex=1 -reindex
docker run -it -d --network bitcoin_network --name bc-node2 bitcoin -printtoconsole -txindex=1 -reindex
docker run -it -d --network bitcoin_network --name bc-node3 bitcoin -printtoconsole -txindex=1 -reindex
