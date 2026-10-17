# The Electrum client alone, as an RPC daemon, connected to the Labnet's
# ElectrumX (../electrum/). Each client version gets its own image and its own
# data volume, so a newer one never opens (and upgrades) an older one's wallets,
# and ElectrumX, which other services use, is not rebuilt for a client update.
FROM python:3.12.7-bookworm

ARG ELECTRUM_VERSION=4.8.2
# SHA-256 of https://download.electrum.org/4.8.2/Electrum-4.8.2.tar.gz, taken on
# 17/10/2026; its blockchain.py and interface.py match the 4.8.2 tag on GitHub
ARG ELECTRUM_SHA256=f38cee333c866986cdfb304428fa7487affc429c3853fc80e9822bd420bbc229

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential automake autoconf libtool git libsecp256k1-dev \
 && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/electrum-venv \
 && curl -fsSL -o /tmp/electrum.tar.gz https://download.electrum.org/${ELECTRUM_VERSION}/Electrum-${ELECTRUM_VERSION}.tar.gz \
 && echo "${ELECTRUM_SHA256}  /tmp/electrum.tar.gz" | sha256sum -c - \
 && /opt/electrum-venv/bin/pip install cryptography /tmp/electrum.tar.gz \
 && ln -s /opt/electrum-venv/bin/electrum /usr/local/bin/electrum \
 && rm /tmp/electrum.tar.gz

# Labnet changes: no mainnet checkpoints (otherwise it disconnects with
# "server tip below max checkpoint"), and electrum.patch
ARG SITE=/opt/electrum-venv/lib/python3.12/site-packages
COPY electrum.patch /tmp/
RUN echo "[]" > $SITE/electrum/chains/mainnet/checkpoints.json \
 && cd $SITE && git apply /tmp/electrum.patch

COPY bin/init /usr/local/bin/init
RUN chmod +x /usr/local/bin/init

ENV HOME=/data
VOLUME ["/data"]
WORKDIR /data
EXPOSE 7777
CMD ["/usr/local/bin/init"]
