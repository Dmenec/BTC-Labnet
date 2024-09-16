FROM ubuntu:22.04 AS builder

LABEL maintainer="Domènec Madrid (@dmenec)"

ARG UID=101
ARG GID=101
ARG BITCOIN_VERSION=24.0.1

RUN groupadd --gid ${GID} bitcoin \
  && useradd --create-home --no-log-init -u ${UID} -g ${GID} bitcoin

RUN apt-get update -y && apt-get install -y \
    curl gnupg build-essential libtool autotools-dev automake pkg-config bsdmainutils \
    python3 python3-pip libevent-dev libboost-dev libboost-system-dev libboost-filesystem-dev \
    libboost-thread-dev libboost-chrono-dev libsqlite3-dev libssl-dev libzmq3-dev git \
    libdb-dev libdb++-dev libdb5.3 libdb5.3++-dev gosu \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip3 install essential_generators base58 bech32

RUN git clone -b v${BITCOIN_VERSION} https://github.com/bitcoin/bitcoin.git /opt/bitcoin-${BITCOIN_VERSION}

COPY chainparams.cpp /opt/bitcoin-${BITCOIN_VERSION}/src/chainparams.cpp

WORKDIR /opt/bitcoin-${BITCOIN_VERSION}

RUN ./autogen.sh \
  && ./configure --with-incompatible-bdb --with-sqlite --without-gui \
  && make -j$(nproc)

FROM ubuntu:22.04

ARG UID=101
ARG GID=101
ARG BITCOIN_VERSION=24.0.1

RUN groupadd --gid ${GID} bitcoin \
  && useradd --create-home --no-log-init -u ${UID} -g ${GID} bitcoin

RUN apt-get update -y && apt-get install -y \
    libevent-dev libboost-system-dev libboost-filesystem-dev libboost-thread-dev libssl-dev libzmq3-dev libsqlite3-dev \
    libdb5.3 libdb5.3++-dev python3 python3-pip gosu curl \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=builder /opt/bitcoin-${BITCOIN_VERSION}/ /opt/bitcoin-${BITCOIN_VERSION}/
ENV PATH=/opt/bitcoin-${BITCOIN_VERSION}/src:$PATH

RUN pip3 install essential_generators base58 bech32

COPY mine/mine.py /home/bitcoin/.bitcoin/mine.py
COPY mine/server.py /home/bitcoin/.bitcoin/server.py
COPY mine/start_mining.sh /home/bitcoin/.bitcoin/start_mining.sh
COPY bitcoin.conf /root/.bitcoin/bitcoin.conf
COPY bitcoin.conf /home/bitcoin/.bitcoin/bitcoin.conf
COPY docker-entrypoint.sh /entrypoint.sh

RUN chown -R bitcoin:bitcoin /home/bitcoin/.bitcoin

VOLUME ["/home/bitcoin/.bitcoin"]

EXPOSE 8333

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
