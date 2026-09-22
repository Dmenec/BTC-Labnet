FROM python:3.8
LABEL maintainer="dmenec"

RUN apt-get update \
 && apt-get install -y build-essential git libssl-dev zlib1g-dev libsecp256k1-dev openssl \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools

# ElectrumX and the Electrum client need different aiorpcX versions,
# so each one gets its own virtualenv.

# ElectrumX server (1.16.0: master needs an aiorpcX that is not on PyPI)
RUN python -m venv /opt/electrumx-venv \
 && /opt/electrumx-venv/bin/pip install uvloop "aiorpcX[ws]>=0.23.0,<0.24" \
 && git clone --branch 1.16.0 --depth 1 https://github.com/spesmilo/electrumx.git /opt/electrumx \
 && /opt/electrumx-venv/bin/pip install /opt/electrumx \
 && ln -s /opt/electrumx-venv/bin/electrumx_server /usr/local/bin/electrumx_server

# Electrum client, runs as a daemon with RPC on port 7777
RUN python -m venv /opt/electrum-venv \
 && /opt/electrum-venv/bin/pip install cryptography \
 && /opt/electrum-venv/bin/pip install https://download.electrum.org/4.5.5/Electrum-4.5.5.tar.gz \
 && ln -s /opt/electrum-venv/bin/electrum /usr/local/bin/electrum

# Make the client accept the Labnet chain: no mainnet checkpoints, plus electrum.patch
ARG SITE=/opt/electrum-venv/lib/python3.8/site-packages
COPY electrum.patch /tmp/
RUN echo "[]" > $SITE/electrum/checkpoints.json \
 && cd $SITE && git apply /tmp/electrum.patch

COPY bin/init /usr/local/bin/init
RUN chmod +x /usr/local/bin/init

ENV HOME=/data \
    DB_DIRECTORY=/data \
    ALLOW_ROOT=1 \
    EVENT_LOOP_POLICY=uvloop \
    SERVICES=tcp://:50001,ssl://:50002,wss://:50004,rpc://0.0.0.0:8000 \
    SSL_CERTFILE=/data/electrumx.crt \
    SSL_KEYFILE=/data/electrumx.key \
    HOST=""

VOLUME ["/data"]
WORKDIR /data
EXPOSE 50001 50002 50004 8000 7777
CMD ["/usr/local/bin/init"]
