FROM node:24.0.0-alpine3.19 AS builder
WORKDIR /app

RUN npm install -g pnpm@9.1.0

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

FROM caddy:2.7.6-alpine

COPY --from=builder /app/dist /usr/share/caddy/html

