# Sitemon Bot

## Requirements
- Python >= 3.6
- [Pipenv](https://pipenv.readthedocs.io/en/latest/)

## Setup
```bash
# install packages
pipenv install
# drop into virtualenv
pipenv shell
# train model
make train-all
# run the action server in vm/docker and set the ip in endpoints.yml
python3 -m rasa_core_sdk.endpoint --actions main.actions
# test model
make run-cmdline
```
### Telegram Setup
1. Create credentials.yml. Token can be generated by messaging @BotFather on telegram.
```yaml
telegram:
  access_token: "<TOKEN>"
  verify: "<bot username>"
  webhook_url: "<FQDN>/webhooks/telegram/webhook"
```
2. Setup nginx as a proxy for the webhook. Telegram requires https to be used for the webhook.
```
upstream rasacore {
    server localhost:6000;
}
server{
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/ssl/origin.icu.pem;
    ssl_certificate_key /etc/ssl/priv.icu.key;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers EECDH+CHACHA20:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1h;
    add_header Strict-Transport-Security "max-age=31536000; includeSubdomains;";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "origin";

    server_name example.com;
    location / {
            proxy_pass            http://rasacore;
            proxy_set_header      Host $host;
    }
}
server {
    if ($host = example.com) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name example.com;
    return 404;
}
```
3. Run both the action server and rasa core. Using [pm2](https://github.com/Unitech/pm2) here as the process manager.
```bash
# in the sitemon directory
pm2 start 'make run-action'
pm2 start 'make run-tele'
pm2 start 'make run-monitor'
```
4. Setup the webhook
```bash
curl 'https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://example.com/webhooks/telegram/webhook'
```
#### Misc
Curl command to send a message
```bash
curl -X POST \
       -H 'Content-Type: application/json' \
       -d '{"chat_id": "<Chat ID>", "text": "This is a test from curl"}' \
       https://api.telegram.org/bot<TOKEN>/sendMessage
```