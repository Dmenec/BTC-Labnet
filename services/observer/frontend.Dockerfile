# ---------- BUILDER ----------
FROM hugomods/hugo:exts AS builder

WORKDIR /src
COPY . .

ENV HUGO_TITLE="Labnet Observer"
ENV HUGO_BASEURL="/"
ENV HUGO_PARAMS_HTMLTOPRIGHT="Labnet privada UAB"
ENV HUGO_PARAMS_HTMLBOTTOMRIGHT="Bitcoin Blockchain Statistics for Labnet"

RUN hugo --minify

# ---------- RUNTIME ----------
FROM nginx:alpine
COPY --from=builder /src/public /usr/share/nginx/html
EXPOSE 80
