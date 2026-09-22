import express from "express";
import cors from "cors";
import rateLimit from "express-rate-limit";
import axios from "axios";
import * as bitcoin from "bitcoinjs-lib";

const PORT = 3000;
const MAX_AMOUNT = 50;

const env = process.env;
const rpcUrl = `http://${env.RPC_HOST || "172.18.0.3"}:${env.RPC_PORT || 8332}/wallet/${env.FAUCET_WALLET || "faucet"}`;
const rpcAuth = { username: env.RPC_USER, password: env.RPC_PASSWORD };

const app = express();
app.use(cors({ origin: env.CORS_ORIGIN || true, methods: ["GET", "POST"] }));
app.use(express.json());

// At most REQUESTS_PER_HOUR payouts per IP
const sendLimit = rateLimit({
  windowMs: 60 * 60 * 1000,
  limit: Number(env.REQUESTS_PER_HOUR || 10),
  message: { error: "Too many requests, try again later." },
});

app.post("/send_to_address", sendLimit, async (req, res) => {
  const { address, amount } = req.body;

  if (!isValidAddress(address)) {
    return res.status(400).json({ error: "Bitcoin address not valid!" });
  }
  if (typeof amount !== "number" || !(amount > 0) || amount > MAX_AMOUNT) {
    return res.status(400).json({ error: `Amount should be greater than 0 and at most ${MAX_AMOUNT}!` });
  }

  try {
    const txId = await rpc("sendtoaddress", [address, amount]);
    res.json({ txId });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Current status of a transaction; the page polls this until it confirms
app.get("/tx/:txId", async (req, res) => {
  const { txId } = req.params;
  if (!/^[0-9a-f]{64}$/i.test(txId)) {
    return res.status(400).json({ error: "Invalid transaction ID" });
  }

  try {
    const tx = await rpc("getrawtransaction", [txId, true]);
    if (!tx.blockhash) {
      return res.json({ confirmations: 0 });
    }
    const block = await rpc("getblockheader", [tx.blockhash]);
    res.json({ confirmations: tx.confirmations, blockHeight: block.height });
  } catch (error) {
    res.status(404).json({ error: error.message });
  }
});

function isValidAddress(address) {
  try {
    bitcoin.address.toOutputScript(address);
    return true;
  } catch {
    return false;
  }
}

async function rpc(method, params = []) {
  try {
    const { data } = await axios.post(rpcUrl, { jsonrpc: "1.0", id: Date.now(), method, params }, { auth: rpcAuth });
    return data.result;
  } catch (error) {
    const message = error.response?.data?.error?.message || "Error connecting to the Bitcoin node";
    console.error(`RPC ${method} failed: ${message}`);
    throw new Error(message);
  }
}

app.listen(PORT, () => console.log(`Faucet API listening on port ${PORT}`));
