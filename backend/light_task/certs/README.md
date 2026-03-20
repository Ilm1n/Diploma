# `certs/` (development)

Папка для JWT ключей в локальной разработке:
- `jwt-private.pem`
- `jwt-public.pem`

Как сгенерировать ключи:
- см. [../src/auth/README.md](../src/auth/README.md)

Важно:
- не коммить реальные приватные ключи
- права доступа к private key должны быть ограничены (`chmod 600`)
