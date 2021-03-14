# Deployment

When this application is deployed you will need to do some setup. These instructions are for an Ubuntu server running an `nginx` reverse proxy  and `gunicorn`.

# Dependencies

We distribute a `requirements.txt` file listing the things the application depends upon. `pip install -r requirements.txt` will install prerequisites.

You will also need the `libpq-dev` and `python3-dev` packages (required to build `psycopg2`).

# S3 Image Hosting

We host images on S3, which allows for easy, access-controlled programmatic uploading.

You'll need to create an AWS account, if you don't already have one. Then, you'll need to create an S3 bucket, and remember its name. Finally, you'll need to create an IAM user, and create access credentials (an IAM access key and its corresponding secret) that you'll populate in the .env file on the server. Finally, you'll need to create an IAM policy and attach it to the IAM user, giving it permission to upload to that S3 bucket:
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1486969693000",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::bucketname",
                "arn:aws:s3:::bucketname/*"
            ]
        }
    ]
}
```

For the officer identification UI to work, you'll need to create a CORS policy for the S3 bucket used with OpenOversight. In the AWS UI, this is done by navigating to the listing of buckets, clicking on the name of your bucket, and choosing the Permissions tab, and then "CORS configuration". Since we're not doing anything fancier than making a web browser GET it, we can just use the default policy:

```
[
    {
        "AllowedOrigins": [
            "*"
        ],
        "AllowedMethods": [
            "GET"
        ],
        "MaxAgeSeconds": 3000,
        "AllowedHeaders": [
            "Authorizations"
        ]
    }
]
```

If you don't click "Save" on that policy, however, the policy will not actually be applied.

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
                proxy_connect_timeout 300s;
                proxy_read_timeout 300s;
                client_max_body_size 20M;
        }
}
```
##  Gunicorn

You will want to run gunicorn in the background with multiple worker threads. You can instantiate gunicorn by running `gunicorn -w 4 -b 127.0.0.1:4000 app:app &` and then `run ps -ef | grep gunicorn` to see the running PIDs. Execute gunicorn out of the OpenOversight directory that has the `app/` directory in it to test that the app comes up.

##  Application Configuration

We configure the database by setting a .env file in the OpenOversight directory of the repository. A sample .env is:
```
SQLALCHEMY_DATABASE_URI="postgresql://openoversight:terriblepassword@localhost/openoversight-dev"
SECRET_KEY=terriblecsrftoken
S3_BUCKET_NAME=bucketname-in-the-account-you-created
AWS_ACCESS_KEY_ID=<access key from AWS>
AWS_SECRET_ACCESS_KEY=<secret key from AWS>
```
The parts of the database URI are the user, password, server, and database respectively used to connect to the application.
The CSRF token should be a random string of reasonable length. 'terriblecsrftoken' is, of course, a terrible CSRF token.
For more details about the S3 and AWS settings, see above. Please raise an issue on Github if you have any questions about the process.

# Systemd

You can write a simple systemd unit file to launch OpenOversight on boot. We defined ours in `/etc/systemd/system/openoversight.service`. You should create the proper usernames and groups that are defined in the unit file since this allows you to drop privileges on boot. This unit file was adopted from this [DigitalOcean guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-centos-7). More details can be found in [CONTRIB.md](/CONTRIB.md).

```
[Unit]
Description=Gunicorn instance to serve OpenOversight
After=network.target

[Service]
User=nginx
Group=nginx
WorkingDirectory=/home/nginx/oovirtenv/OpenOversight/OpenOversight
Environment="PATH=/home/nginx/oovirtenv/bin"
ExecStart=/home/nginx/oovirtenv/bin/gunicorn -w 4 -b 127.0.0.1:4000 --timeout 90 app:app

[Install]
WantedBy=multi-user.target
```
# Python Fabric

We use [Python Fabric](http://www.fabfile.org/) to manage our deployments and database backups. A sample fabric file is found in `fabric.py`. The usage is `fab host command`, so for example `fab staging deploy` would deploy our latest commits to the staging server.

# Contact

If you're running into installation problems, please open an issue or email us `info AT lucyparsonslabs DOT com`.
