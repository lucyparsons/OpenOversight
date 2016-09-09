# Deployment

When this application is deployed you will need to do some setup. These instructions are for an Ubuntu server running an `nginx` reverse proxy  and `gunicorn`. 

# Dependencies

At minimum you will need to install the pip packages using pip:
 * flask
 * werkzeug
 * Flask-WTF
 * psycopg2
 * sqlalchemy
 * gunicorn

You may also need the `libpq-dev` package if psycopg2 fails to install.

# Webserver Configuration

The anonymity and security of your users is extremely important. Therefore we *highly* recommend using HTTPS on your entire application (you can use Let's Encrypt for free certificates) and you should test your application using the Tor Browser Bundle. Since nginx will run as a reverse proxy, you will need to add additional rules for the proxy headers to reach gunicorn. An example configuration is below but you should note that your relative paths will be different (especially the `snippets/` files).
```
server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name <local information>;
        return 301 https://$server_name$request_uri;
        # Required by Let's Encrypt
        location ~ /.well-known {
                allow all;
        }
	# Do not log visitor information
        access_log off;
}
server {
        # SSL configuration
        #
        listen 443 ssl http2 default_server;
        listen [::]:443 ssl http2 default_server;
        include snippets/<local information>.conf;
        include snippets/ssl-params.conf;
        root /var/www/html;
        access_log off;
        index index.html index.htm index.nginx-debian.html;

        location / {
                # Gunicorn proxy pass rule
                proxy_pass http://127.0.0.1:4000;
                proxy_redirect     off;
                proxy_set_header Host $host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
}
```
##  Gunicorn

You will want to run gunicorn in the background with multiple worker threads. You can instantiate gunicorn by running `gunicorn -w 4 -b 127.0.0.1:4000 app:app &` and then run ps -ef | grep gunicorn to see the running PIDs. Execute gunicorn out of the OpenOversight directory that has the `app/` directory in it.

##  Database Configuration

Your database credentials should be set in the `app/` folder in a file called dbcred.py. An example configuration is below (assuming an Amazon RDS).
```
user =""
password = ""
host = "infomarmationfromamazon.rds.amazonaws.com"
port = 6666
```

## CSRF attacks

Change the secret key used for generating tokens to prevent cross-site request forgery (CSRF) attacks in `config.py`:

```
WTF_CSRF_ENABLED = True
SECRET_KEY = 'changemeplzorelsehax'
```

# Systemd

You can write a simple systemd unit file to launch OpenOversight on boot. We defined ours in `/etc/systemd/system/openoversight.service`. You should create the proper usernames and groups that are defined in the unit file since this allows you to drop privileges on boot. This unit file was adopted from this [DigitalOcean guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-centos-7).
```
[Unit]
Description=Gunicorn instance to serve OpenOversight
After=network.target

[Service]
User=nginx
Group=nginx
WorkingDirectory= /home/nginx/oovirtenv/OpenOversight/OpenOversight
Environment="PATH=/home/nginx/oovirtenv/bin"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:4000 app:app &

[Install]
WantedBy=multi-user.target
```

# Contact

If you're running into installation problems, please open an issue or email us `info AT lucyparsonslabs DOT com`
