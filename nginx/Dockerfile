FROM nginx:alpine

# Generar certificado SSL auto-firmado al construir
RUN apk add --no-cache openssl && \
    mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -days 365 \
      -subj "/CN=uam-streamapps" \
      -newkey rsa:2048 \
      -keyout /etc/nginx/ssl/key.pem \
      -out /etc/nginx/ssl/cert.pem

COPY nginx.conf /etc/nginx/nginx.conf
