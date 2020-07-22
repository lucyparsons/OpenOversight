# Contributing Guide

First, thanks for being interested in helping us out! If you find an issue you're interested in, feel free to make a comment about how you're thinking of approaching implementing it in the issue and we can give you feedback.  Please also read our [code of conduct](/CODE_OF_CONDUCT.md) before getting started.

## Submitting a PR

When you come to implement your new feature, you should branch off `develop` and add commits to implement your feature. If your git history is not so clean, please do rewrite before you submit your PR - if you're not sure if you need to do this, go ahead and submit and we can let you know when you submit.

Use [PULL_REQUEST_TEMPLATE.md](/PULL_REQUEST_TEMPLATE.md) to create the description for your PR! (The template should populate automatically when you go to open the pull request.)

### Linting / Style Checks

 `flake8` is a tool for automated linting and style checks. Be sure to run `flake8` and fix any errors before submitting a PR.

 You can run it with `make lint` to execute flake8 from the docker containers.

## Development Environment

You can use our Docker-compose environment to stand up a development OpenOversight.

You will need to have Docker installed in order to use the Docker development environment.

To build and run the development environment, simply `make dev`. Whenever you want to rebuild the containers, `make build` (you should need to do this rarely).

Tests are executed via `make test`. If you're switching between the Docker and Vagrant/VirtualBox environments and having trouble getting tests running, make sure to delete any remaining `.pyc` files and `__pycache__` directories.

To hop into the postgres container, you can do the following:

```
$ docker exec -it openoversight_postgres_1 /bin/bash
# psql -d openoversight-dev -U openoversight
```

or run `make attach`.

Similarly to hop into the web container:

```
$ docker exec -it openoversight_web_1 /bin/bash
```

Once you're done, `make stop` and `make clean` to stop and remove the containers respectively.

## Testing S3 Functionality

We use an S3 bucket for image uploads. If you are working on functionality involving image uploads,
then you should follow the "S3 Image Hosting" section in [DEPLOY.md](/DEPLOY.md) to make a test S3 bucket
on Amazon Web Services.

Once you have done this, you can put your AWS credentials in the following environmental variables:

```sh
$ export S3_BUCKET_NAME=openoversight-test
$ export AWS_ACCESS_KEY_ID=testtest
$ export AWS_SECRET_ACCESS_KEY=testtest
$ export AWS_DEFAULT_REGION=us-east-1
```

Now when you run `make dev` as usual in the same session, you will be able to submit images to
your test bucket.

## Database commands

Running `make dev` will create the database and persist it into your local filesystem.

You can access your PostgreSQL development database via psql using:

```sh
psql  -h localhost -d openoversight-dev -U openoversight --password
```

with the password `terriblepassword`.

In the event that you need to create or delete the test data, you can do that with
`$ python test_data.py --populate` to create the data
or
`$ python test_data.py --cleanup` to delete the data

### Migrating the Database

If you e.g. add a new column or table, you'll need to migrate the database using the Flask CLI. First we need to 'stamp' the current version of the database:

```sh
$ cd OpenOversight/  # change directory to source dir
$ flask db stamp head
```

(Hint: If you get errors when running `flask` commands, e.g. because of differing Python versions, you may need to run the commands in the docker container by prefacing them as so: `docker exec -it openoversight_web_1 flask db stamp head`)

Next make your changes to the database models in `models.py`. You'll then generate the migrations:

```sh
$ flask db migrate
```

And then you should inspect/edit the migrations. You can then apply the migrations:

```sh
$ flask db upgrade
```

You can also downgrade the database using `flask db downgrade`.

## Using a Virtual Environment
One way to avoid hitting version incompatibility errors when running `flask` commands is to use a virtualenv.  See [Python Packaging user guidelines](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/) for instructions on installing virtualenv.  After installing virtualenv, you can create a virtual environment by navigating to the OpenOversight directory and running the below

```bash
python3 -m virtualenv env
```

Confirm you're in the virtualenv by running 

```bash
which python  
```

The response should point to your `env` directory.  
If you want to exit the virtualenv, run 

```bash
deactivate
```

To reactivate the virtualenv, run

```bash
source env/bin/activate
```

While in the virtualenv, you can install project dependencies by running 

```bash
pip install -r requirements.txt
```

and

```bash
pip install -r dev-requirements.txt
```

## OpenOversight Management Interface

In addition to generating database migrations, the Flask CLI can be used to run additional commands:

```sh
$ flask --help
Usage: flask [OPTIONS] COMMAND [ARGS]...

  A general utility script for Flask applications.

  Provides commands from Flask, extensions, and the application. Loads the
  application defined in the FLASK_APP environment variable, or from a
  wsgi.py file. Setting the FLASK_ENV environment variable to 'development'
  will enable debug mode.

    $ export FLASK_APP=hello.py
    $ export FLASK_ENV=development
    $ flask run

Options:
  --version  Show the flask version
  --help     Show this message and exit.

Commands:
  bulk-add-officers            Bulk adds officers.
  db                           Perform database migrations.
  link-images-to-department    Link existing images to first department
  link-officers-to-department  Links officers and units to first department
  make-admin-user              Add confirmed administrator account
  routes                       Show the routes for the app.
  run                          Runs a development server.
  shell                        Runs a shell in the app context.
```

In development, you can make an administrator account without having to confirm your email:

```sh
$ flask make-admin-user
Username: redshiftzero
Email: jen@redshiftzero.com
Password:
Type your password again:
Administrator redshiftzero successfully added
```

## Debugging OpenOversight - Use pdb with the app itself
In `docker-compose.yml`, below the line specifying the port number, add the following lines to the `web` service:
```yml
   stdin_open: true
   tty: true    
```
Also in `docker-compose.yml`, below the line specifying the `FLASK_ENV`, add the following to the `environment` portion of the `web` service:
```yml
  FLASK_DEBUG: 0
```
The above line disables the werkzeug reloader, which can otherwise cause a bug when you place a breakpoint in code that loads at import time, such as classes.  The werkzeug reloader will start one pdb process at import time and one when you navigate to the class.  This makes it impossible to interact with the pdb prompt, but we can fix it by disabling the reloader.
    
To set a breakpoint in OpenOversight, first import the pdb module by adding `import pdb` to the file you want to debug.  Call `pdb.set_trace()` on its own line wherever you want to break for debugging.
Next, in your terminal run `docker ps` to find the container id of the `openoversight_web` image, then run `docker attach ${container_id}` to connect to the debugger in your terminal.  You can now use pdb prompts to step through the app.

## Debugging OpenOversight - Use pdb with a test
If you want to run an individual test in debug mode, use the below command.
```yml
`docker-compose run --rm web pytest --pdb -v tests/ -k <test_name_here>`
```
Again, add `import pdb` to the file you want to debug, then write `pdb.set_trace()` wherever you want to drop a breakpoint.  Once the test is up and running in your terminal, you can debug it using pdb prompts.