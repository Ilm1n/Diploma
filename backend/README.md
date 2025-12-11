1. Add a .env file to the root of the project. Fill it in using the template from
2. make dir /certs in project_dir 
3. in "certs" dir run this commands:
```shell
# Generate an RSA private key, of size 2048
openssl genrsa -out jwt-private.pem 2048
```

```shell
# Extract the public key from the key pair, which can be used in a certificate
openssl rsa -in jwt-private.pem -outform PEM -pubout -out jwt-public.pem
```