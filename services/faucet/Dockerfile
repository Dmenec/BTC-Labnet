FROM node:22

# nginx serves the page on port 80, the Node API listens on port 3000
RUN apt-get update \
 && apt-get install -y nginx \
 && rm -rf /var/lib/apt/lists/* /etc/nginx/sites-enabled/default

COPY default.conf /etc/nginx/conf.d/default.conf
COPY html /usr/share/nginx/html

WORKDIR /node
COPY node/package.json node/package-lock.json ./
RUN npm ci --omit=dev
COPY node/server.js ./

EXPOSE 80 3000
CMD ["sh", "-c", "service nginx start && node server.js"]
