#!/bin/bash

docker network create -d bridge bitcoin_network

docker build -t bitcoin .


# Port forwarding to connect from external source to our private network
docker run -it -d --network bitcoin_network --name bc-node0 -p 8333:8333 bitcoin -printtoconsole -txindex=1 -reindex
docker run -it -d --network bitcoin_network --name bc-node1 bitcoin -printtoconsole -txindex=1 -reindex
docker run -it -d --network bitcoin_network --name bc-node2 bitcoin -printtoconsole -txindex=1 -reindex
