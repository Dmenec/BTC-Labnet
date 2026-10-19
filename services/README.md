# Labnet services

Optional services that run next to the Labnet node. None of them is needed for the node itself.

All of them join the node's Docker network `bitcoin_network` (`172.18.0.0/16`) with fixed IPs, because they reference each other and the node by IP:

| Service | Container | IP | Host ports | Directory |
|---|---|---|---|---|
| Bitcoin Knots v29.4 | `knots-v29.4` | 172.18.0.8 | 9342 (RPC, localhost only) | [knots/](knots/) |
| Bitcoin Knots v29.2 (previous version, kept) | `knots-v29.2` | 172.18.0.2 | 9332 (RPC) | [knots/](knots/) |
| ElectrumX + Electrum daemon | `electrum_server_container` | 172.18.0.5 | 50001, 50002, 7777 | [electrum/](electrum/) |
| Electrum 4.8.2 client (daemon only) | `electrum-client-4.8.2` | 172.18.0.9 | 7778 (RPC) | [electrum-client/](electrum-client/) |
| mempool DB / API / web | `mempool-db-1`, `mempool-api-1`, `mempool-web-1` | .4 / .7 / .6 | 8888 (web) | [mempool/](mempool/) |
| mainnet-observer | `mainnet-observer-frontend` | default bridge | 8889 | [observer/](observer/) |
| Faucet | `faucet` | default bridge | 80, 3000 | [faucet/](faucet/) |

Containers without a fixed IP, like the faucet, get one from `172.18.128.0/17`, so they never take these addresses. The node is `172.18.0.3`. If a service runs on a different host than the node, replace that IP with the node host's address and add the service host to `RPC_ALLOW_IPS` in the node's `.env`.

Commands below are run from this directory.

## Knots ([knots/](knots/))

Bitcoin Knots `v29.4.knots20260508` with the same consensus patches as the node (see the main [README](../README.md#consensus-patches)), except for the IBD change: Knots does not serve block templates. Each version has its own diffs against its upstream tag, in [knots/patches/](knots/patches/)`<version>/`.

Two versions run side by side, each with its own data volume, so the wallets of one never open in the other (a newer Knots upgrades a wallet file when it loads it):

- **29.4** is the current one. Later releases are not used: 29.4.1 is a hard fork (BLAKE2b proof of work, and wallets sign with a new sighash that this chain rejects). The build disables BIP110 (RDTS), see the [Dockerfile](knots/Dockerfile).
- **29.2** is the previous one, kept so wallet fingerprints can be compared across versions.

It uses the same RPC credentials as the node, from the root `.env`:

```bash
set -a; . ../.env; set +a
docker build -t knots-v29.4 knots
docker run -d --name knots-v29.4 --network bitcoin_network --ip 172.18.0.8 --restart unless-stopped \
  -v knots_29_4_data:/home/bitcoin/.bitcoin -p 127.0.0.1:9342:8332 knots-v29.4 \
  -printtoconsole -txindex=1 -dnsseed=0 -fixedseeds=0 -addnode=core-v30.0-v1:8333 \
  -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD"
```

To compare the two versions, both must run with the same settings, and the
image only brings a default `bitcoin.conf`. The running 29.2 node's copy was
edited inside its volume (mempool ancestor and descendant limits, `maxmempool`,
RPC access), and those limits decide which unconfirmed coins the wallet may
spend. So the new volume gets an exact copy of it, then the node restarts:

```bash
umask 077; T=$(mktemp)
docker cp knots-v29.2:/home/bitcoin/.bitcoin/bitcoin.conf "$T"
docker cp "$T" knots-v29.4:/home/bitcoin/.bitcoin/bitcoin.conf
docker exec knots-v29.4 chown bitcoin:bitcoin /home/bitcoin/.bitcoin/bitcoin.conf
rm -f "$T"; docker restart knots-v29.4
```

The orchestrator uses the new node when `BITCOIN_KNOTS_RPC_URL` points at
`http://127.0.0.1:9342` (set in the environment of the run, or in its `.env`).

The previous version is built and run the same way, with
`--build-arg BITCOIN_VERSION=29.2.knots20251110`, the name `knots-v29.2`, the IP
`172.18.0.2`, the volume `knots_data` and the port `9332`.

## Electrum ([electrum/](electrum/))

One image runs both **ElectrumX 1.16.0** (indexer) and the **Electrum 4.5.5** client as an RPC daemon on port 7777, so wallets can be created, signed and broadcast on the private chain. The two live in separate virtualenvs because their `aiorpcX` requirements conflict.

The Electrum client is patched at build time to accept a chain that is not the public mainnet. The first change is made in the Dockerfile, the rest are in [electrum/electrum.patch](electrum/electrum.patch):

1. `checkpoints.json` emptied. Otherwise it disconnects with `server tip below max checkpoint`.
2. `blockchain.py` `verify_header()` checks the proof of work against the header's own `nBits`. Electrum expects the mainnet retarget schedule, and the Labnet never retargets.
3. `interface.py` `_process_header_at_tip()` syncs from height 0 when the local chain is empty.

A header must still be the next height and link to the previous block. An earlier version of the patch accepted any header and appended it to the end of the headers file. When two blocks arrived within the same second the client stored the second one in the first one's place, then failed every merkle proof for that block and reconnected in a loop, so its wallets stopped seeing confirmations. A client that ran with that version needs its `blockchain_headers` file rebuilt from the node.

[electrum/bin/init](electrum/bin/init) generates the SSL certificate, configures the client to use only the local ElectrumX, and supervises the Electrum daemon (it restarts it only if `electrum getinfo` fails).

Copy [electrum/.env.example](electrum/.env.example) to `electrum/.env` and set the node credentials in `DAEMON_URL`. The cost limits in it are disabled on purpose (see the comments).

```bash
docker build -t electrum_server electrum
docker run -d --name electrum_server_container --network bitcoin_network --ip 172.18.0.5 --restart unless-stopped \
  -v electrumx_data:/data -p 50001:50001 -p 50002:50002 -p 7777:7777 \
  --env-file electrum/.env electrum_server
```

- The `electrumx_data` volume holds the wallets in `/data/.electrum/wallets/`. Do not delete it. The ElectrumX index (`/data/{hist,utxo,meta}`) can be deleted to force a reindex.
- If `electrum getinfo` shows the public mainnet height or `connected: false`, stop the daemon, delete `/data/.electrum/blockchain_headers` and `/data/.electrum/forks`, and start it again.

## Electrum client ([electrum-client/](electrum-client/))

The **Electrum 4.8.2** client alone, as an RPC daemon, connected to the ElectrumX above. Client updates go in an image of their own, so ElectrumX, which other services use, is not rebuilt, and the 4.5.5 client inside `electrum_server_container` stays as the previous version. Each client has its own data volume: a newer client upgrades a wallet file when it opens it, and the older one can no longer read it.

The changes are the same as for 4.5.5, on the 4.8.2 code: `electrum/chains/mainnet/checkpoints.json` emptied (it moved in 4.6) and [electrum-client/electrum.patch](electrum-client/electrum.patch). The Dockerfile checks the SHA-256 of the release tarball.

It takes the same RPC credentials as the client in `electrum/.env` (`ELECTRUM_RPC_USER`, `ELECTRUM_RPC_PASSWORD`):

```bash
docker build -t electrum-client-4.8.2 electrum-client
docker run -d --name electrum-client-4.8.2 --network bitcoin_network --ip 172.18.0.9 --restart unless-stopped \
  -v electrum_client_4_8_2_data:/data -p 7778:7777 \
  -e ELECTRUM_RPC_USER -e ELECTRUM_RPC_PASSWORD electrum-client-4.8.2
```

## mempool ([mempool/](mempool/))

The official `mempool/frontend` and `mempool/backend` images, configured to use ElectrumX as backend and the main node for RPC. Copy [mempool/.env.example](mempool/.env.example) to `mempool/.env` and set the passwords, then:

```bash
cd mempool && docker compose up -d
```

The images are pinned to the versions running in production. The database and the cache live in the Docker volumes `mempool_mempool_db` and `mempool_mempool_cache`. With empty volumes mempool indexes the blocks again from the node, but the history of the mempool statistics charts is lost.

A `401` in `docker logs mempool-api-1` means wrong RPC credentials or node IP. `ECONNREFUSED ...:50001` means ElectrumX is down or its IP is wrong.

## mainnet-observer ([observer/](observer/))

Charts from [0xB10C/mainnet-observer](https://github.com/0xB10C/mainnet-observer). This directory only holds the files added to that repository:

1. Clone it into `~/observer/mainnet-observer`, then copy `backend.Dockerfile` to `backend/Dockerfile` and `frontend.Dockerfile` to `frontend/Dockerfile`.
2. Build the backend: `docker build -t mainnet-observer-backend ~/observer/mainnet-observer/backend`.
3. Run [observer/refresh.sh](observer/refresh.sh) whenever the charts need updating. It reads the node's REST API (`rest=1`), regenerates the CSVs and rebuilds the frontend on port 8889.

`--start-height 1` excludes the genesis block, which dates from 2009.

## Faucet ([faucet/](faucet/))

Web page (nginx, port 80) plus an Express API (port 3000) that sends coins from a wallet on the node with `sendtoaddress`.

Copy [faucet/.env.example](faucet/.env.example) to `faucet/.env` and fill it in (RPC credentials, wallet, payouts per IP and hour), then:

```bash
cd faucet && docker compose up -d --build
```

The container joins `bitcoin_network` and reaches the node at `172.18.0.3`. The page calls the API on port 3000 of the host it was loaded from.

API:
- `POST /send_to_address` with `{"address": "...", "amount": 1.5}` (at most 50 BTC). Returns `{"txId": "..."}`.
- `GET /tx/<txid>` returns `{"confirmations": n, "blockHeight": h}`. The page polls it every 5 s for up to 4 minutes.

Every payout puts a transaction in the mempool. If the miner is powered on when the mempool is not empty, or other tools spend from the same wallet, a payout can interfere with them: use a dedicated wallet, or stop the faucet while running experiments.
