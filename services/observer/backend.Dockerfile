# ---------- BUILDER ----------
FROM rust:1.83-bookworm AS builder

WORKDIR /build
COPY . .
RUN cargo build --release

# ---------- RUNTIME ----------
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/target/release/mainnet-observer-backend /usr/local/bin/

WORKDIR /data
ENTRYPOINT ["mainnet-observer-backend"]
