# FastAPIFileServer
Simple python fastapi file server.

# .env params

```
LOGIN="admin"               # set basic login
PASSWORD="admin"            # set basic password
HOST="localhost"            # set host
PORT=5000                   # set port
DOWNLOAD_DIR="./files/"     # set files dir
```

`DOWNLOAD_DIR` param must end with `/` for predictable usage

`swagger-ui-bundle.js` is downloaded because some time its is unreachable.