# JWT Keys (`jwt-private.pem` / `jwt-public.pem`)

Backend подписывает JWT через RSA key pair.

## 1. Обязательные имена файлов
- `jwt-private.pem`
- `jwt-public.pem`

## 2. Генерация ключей
```bash
# 1) приватный ключ (RSA 2048)
openssl genrsa -out jwt-private.pem 2048

# 2) публичный ключ
openssl rsa -in jwt-private.pem -outform PEM -pubout -out jwt-public.pem
```

## 3. Куда класть ключи
### Development (`docker-compose.dev.yml`)
Сложи ключи в:
- `backend/light_task/certs/`

Почему: compose монтирует
- `./backend/light_task/certs:/app/certs`

### Production (`docker-compose.prod.yml`)
Сложи ключи в:
- `./certs/` (рядом с `docker-compose.prod.yml`)

Почему: compose монтирует
- `./certs:/app/certs:ro`

## 4. Проверка ключей
```bash
openssl rsa -in jwt-private.pem -check -noout
openssl rsa -in jwt-private.pem -pubout -outform PEM | diff - jwt-public.pem
```

## 5. Security notes
- приватный ключ не хранится в git
- ротация делается парой (private + public)
- после ротации все старые токены станут невалидными, потребуется re-login
