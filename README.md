# BTC Labnet: a private Bitcoin mainnet for controlled testing

BTC Labnet is a private Bitcoin network developed by the Blockchain and Cryptocurrency Research Group at the Universitat Autònoma de Barcelona. Its node is a patched Bitcoin Core v30.0 that keeps the **mainnet** parameters (genesis block, address formats, ports), so real wallets and tools can be used against a chain nobody else is mining.

This repository contains the node. Optional services that run next to it (Knots, Electrum, mempool, mainnet-observer, faucet) are in [services/](services/).

## Consensus patches

The node is Bitcoin Core **v30.0** with two source files patched at build time: [core/Dockerfile](core/Dockerfile) clones the upstream tag and applies the diffs in [core/patches/30.0/](core/patches/30.0/). The same Dockerfile builds other versions with their own diffs ([core/patches/32.0/](core/patches/32.0/), for a separate wallet node; see the top of the Dockerfile).

**`src/kernel/chainparams.cpp`** (mainnet section):

| Parameter | Upstream | Labnet | Why |
|---|---|---|---|
| `SegwitHeight` | 481824 | 0 | SegWit active from the genesis block |
| Taproot `min_activation_height` | 709632 | 0 | Taproot active from the genesis block |
| `fPowNoRetargeting` | false | true | No automatic retargeting: the chain has a single small miner |
| `nMinimumChainWork` | mainnet value | 0 | The private chain has very little work |
| `defaultAssumeValid` | mainnet block | none | No mainnet block exists on this chain |

`powLimit` stays at the **mainnet** value. Together with `fPowNoRetargeting`, this keeps the difficulty from ever going below 1. Do not replace it with the regtest `powLimit` (`7fff…`): that allows blocks with difficulty below 1, which nodes built from this repository reject (`high-hash`), and the network splits.

**`src/validation.cpp`**:

- `IsInitialBlockDownload()` no longer returns `true` when the tip is older than `max_tip_age`. Without this, the node stays in IBD whenever nobody has mined for a while, `getblocktemplate` fails, and the pool cannot give work to the miner.
- `ContextualCheckBlockHeader()` skips the `bad-diffbits` check when `fPowNoRetargeting` is set. Upstream then requires every block to repeat the previous block's `nBits`; with the patch, any `nBits` within `powLimit` is accepted.

[services/knots/](services/knots/) applies the same patches to Bitcoin Knots (`v29.4.knots20260508`, and `v29.2.knots20251110` before it), except for the IBD change (Knots does not serve block templates).

## Running a node

Requirements: Docker 20.10 or later.

1. Copy [.env.example](.env.example) to `.env` and fill it in: RPC credentials, an optional `rpcauth` line for extra users (mempool), the peer to sync from, and the hosts outside the Docker network that may use RPC (mining pool, wallet clients, services on another machine).
2. Build the image and start the node:

   ```bash
   ./start.sh
   ```

   With `LABNET_PEER` set, the node joins that Labnet and syncs its chain. Without it, the node starts a new chain from the genesis block.
3. Check it:

   ```bash
   docker exec core-v30.0-v1 bitcoin-cli -rpcuser=<user> -rpcpassword='<password>' getblockchaininfo
   ```

Use single quotes around the password if it contains `!`, otherwise bash expands it.

The node gets the fixed IP `172.18.0.3` on the Docker network `bitcoin_network` (`172.18.0.0/16`), which the services expect.

## Mining

The node is mined through [public-pool](https://github.com/benjamin-wilson/public-pool), which fetches block templates over RPC, and a [Bitaxe](https://bitaxe.org/) connected to the pool over Stratum. Bitcoin Core 30 rejects the numeric `jsonrpc` field sent by public-pool's RPC library, so its Dockerfile needs this after `npm i`:

```bash
sed -i 's/jsonrpc: 1.0/jsonrpc: "1.0"/' node_modules/rpc-bitcoin/build/src/rpc.js
```

At difficulty 1, `generatetoaddress` and CPU miners do not find blocks in practice.

## Operational notes

- Always recreate the container with its fixed `--ip`. The services reference the node by IP.
- The `bitcoin.conf` baked into the image is only copied to the data volume the first time. After that, edit the copy inside the volume.
- Changes made with `docker exec` are lost when the container is recreated. Permanent changes go into [core/](core/).
- A `peers.dat` restored from a backup can make an "isolated" node connect to the real Bitcoin network. Use `-connect=` and delete `peers.dat` and `anchors.dat`.

## Contributing

Contributions are welcome. Please open an issue or a pull request.
