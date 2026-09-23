#!/bin/bash
# Builds the patched Bitcoin Core image and starts the Labnet node.
# Settings are read from .env (see .env.example).
set -e
cd "$(dirname "$0")"

set -a; . ./.env; set +a
: "${RPC_USER:?set RPC_USER in .env}" "${RPC_PASSWORD:?set RPC_PASSWORD in .env}"

# The services expect the node at 172.18.0.3, so the network needs this exact subnet.
# Containers without a fixed IP get one from 172.18.128.0/17, so they never take
# the fixed addresses at the start of the subnet.
if docker network inspect bitcoin_network >/dev/null 2>&1; then
  subnet=$(docker network inspect bitcoin_network --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
  if [ "$subnet" != "172.18.0.0/16" ]; then
    echo "bitcoin_network already exists with subnet $subnet, the Labnet needs 172.18.0.0/16." >&2
    echo "Remove it with 'docker network rm bitcoin_network' and run this script again." >&2
    exit 1
  fi
else
  docker network create -d bridge --subnet 172.18.0.0/16 --ip-range 172.18.128.0/17 --gateway 172.18.0.1 bitcoin_network
fi

docker build -t core-v30.0-v1 core

ARGS=(-rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD")
[ -n "$RPC_AUTH" ] && ARGS+=(-rpcauth="$RPC_AUTH")
[ -n "$LABNET_PEER" ] && ARGS+=(-addnode="$LABNET_PEER")
for ip in ${RPC_ALLOW_IPS//,/ }; do ARGS+=(-rpcallowip="$ip"); done

docker run -d --name core-v30.0-v1 --network bitcoin_network --ip 172.18.0.3 --restart unless-stopped \
  -v core_data:/home/bitcoin/.bitcoin -p 8332:8332 -p 8333:8333 core-v30.0-v1 \
  -printtoconsole -txindex=1 -dnsseed=0 -fixedseeds=0 "${ARGS[@]}"
