# Build Bitcoin Knots from the upstream tag with the Labnet patches. Each
# version has its own patches in patches/<version>/; an older one is built with
#   docker build --build-arg BITCOIN_VERSION=29.2.knots20251110 -t knots-v29.2 knots
FROM ubuntu:22.04 AS builder

ARG UID=101
ARG GID=101
ARG BITCOIN_VERSION="29.4.knots20260508"

RUN groupadd --gid ${GID} bitcoin \
 && useradd --create-home --no-log-init -u ${UID} -g ${GID} bitcoin

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential libtool autotools-dev automake pkg-config \
    cmake ninja-build \
    git python3 \
    libevent-dev \
    libboost-system-dev libboost-filesystem-dev libboost-thread-dev \
    libsqlite3-dev \
    libzmq3-dev \
    capnproto libcapnp-dev \
 && update-ca-certificates \
 && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# GitHub clones sometimes fail halfway, so keep retrying
RUN until git clone --branch v${BITCOIN_VERSION} --depth 1 \
          https://github.com/bitcoinknots/bitcoin.git /opt/bitcoin-${BITCOIN_VERSION}; do \
        echo "Retrying clone..."; sleep 5; \
    done

# Labnet consensus changes, explained at the top of each patch
COPY patches/${BITCOIN_VERSION}/ /tmp/patches/
RUN cd /opt/bitcoin-${BITCOIN_VERSION} && git apply /tmp/patches/*.patch

WORKDIR /opt/bitcoin-${BITCOIN_VERSION}

# Since 29.3.knots20260508 the build has to choose how the node treats the
# BIP110 (RDTS) soft fork. UNSUPPORTED_UNSAFE_NO_ENFORCEMENT leaves it never
# active, so the node follows the same rules as the Core node (it logs a
# warning every hour). Earlier versions ignore the option.
RUN cmake -S . -B build -G Ninja \
      -DBUILD_GUI=OFF \
      -DRDTS_CONSENT=UNSUPPORTED_UNSAFE_NO_ENFORCEMENT \
      -DENABLE_ZMQ=ON \
      -DENABLE_IPC=OFF \
  && cmake --build build -- -j"$(nproc --all)" \
  && cmake --install build

# Runtime image
FROM ubuntu:22.04

ARG UID=101
ARG GID=101
ARG BITCOIN_VERSION="29.4.knots20260508"

RUN groupadd --gid ${GID} bitcoin \
  && useradd --create-home --no-log-init -u ${UID} -g ${GID} bitcoin

RUN apt-get update -y && apt-get install -y \
    libevent-dev libboost-system-dev libboost-filesystem-dev libboost-thread-dev libssl-dev libzmq3-dev libsqlite3-dev \
    libdb5.3 libdb5.3++-dev python3 python3-pip gosu curl \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# The sources come along with the binaries, so you can always check what a
# running node was built from
COPY --from=builder /opt/bitcoin-${BITCOIN_VERSION}/ /opt/bitcoin-${BITCOIN_VERSION}/
ENV PATH=/opt/bitcoin-${BITCOIN_VERSION}/build/bin/:$PATH

# Docker only copies this config into the data volume the first time the volume
# is used. After that, edit the copy inside the volume.
COPY bitcoin-build/bitcoin.conf /root/.bitcoin/bitcoin.conf
COPY bitcoin-build/bitcoin.conf /home/bitcoin/.bitcoin/bitcoin.conf
COPY bitcoin-build/docker-entrypoint.sh /entrypoint.sh

RUN chown -R bitcoin:bitcoin /home/bitcoin/.bitcoin

VOLUME ["/home/bitcoin/.bitcoin"]

EXPOSE 8333

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
