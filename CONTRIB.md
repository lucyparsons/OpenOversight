# Contributing Guide

First, thanks for being interested in helping us out! If you find an issue you're interested in, feel free to make a comment about how you're thinking of approaching implementing it in the issue and we can give you feedback.  Please also read our [code of conduct](/CODE_OF_CONDUCT.md) before getting started.

## Submitting a PR

When you come to implement your new feature, you should branch off `develop` and add commits to implement your feature. If your git history is not so clean, please do rewrite before you submit your PR - if you're not sure if you need to do this, go ahead and submit and we can let you know when you submit.

Use [PULL_REQUEST_TEMPLATE.md](/PULL_REQUEST_TEMPLATE.md) to create the description for your PR! (The template should populate automatically when you go to open the pull request.)

### Linting / Style Checks

 `flake8` is a tool for automated linting and style checks. Be sure to run `flake8` and fix any errors before submitting a PR.

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

Similarly to hop into the web container:

```
$ docker exec -it openoversight_web_1 /bin/bash
```

Once you're done, `make stop` and `make clean` to stop and remove the containers respectively.

## Database commands

You can access your PostgreSQL development database via psql using:

```sh
psql  -h localhost -d openoversight-dev -U openoversight --password
```

with the password `terriblepassword`.


In the Docker environment, you'll need to run the script to create the database:

```sh
$ python create_db.py
```

In the event that you need to create or delete the test data, you can do that with
`$ python test_data.py --populate` to create the data
or
`$ python test_data.py --cleanup` to delete the data

### Migrating the Database

If you e.g. add a new column or table, you'll need to migrate the database.

You can use the management interface to first generate migrations:

```sh
$ python manage.py db migrate
```

And then you should inspect/edit the migrations. You can then apply the migrations:

```sh
$ python manage.py db upgrade
```

You can also downgrade the database using `python manage.py db downgrade`.

## OpenOversight Management Interface

In addition to running the development server, `manage.py` (OpenOversight's management interface) can be used to do the following:

```sh
$ python manage.py
--------------------------------------------------------------------------------
INFO in __init__ [/vagrant/OpenOversight/app/__init__.py:57]:
OpenOversight startup
--------------------------------------------------------------------------------
usage: manage.py [-?]
                 {runserver,db,shell,make_admin_user,link_images_to_department}
                 ...

positional arguments:
  {runserver,db,shell,make_admin_user,link_images_to_department}
    runserver           Runs the Flask development server i.e. app.run()
    db                  Perform database migrations
    shell               Runs a Python shell inside Flask application context.
    make_admin_user     Add confirmed administrator account
    link_images_to_department
                        Link existing images to first department

optional arguments:
  -?, --help            show this help message and exit
```

In development, you can make an administrator account without having to confirm your email:

```sh
$ python manage.py make_admin_user
Username: redshiftzero
Email: jen@redshiftzero.com
Password:
Type your password again:
Administrator redshiftzero successfully added
```
