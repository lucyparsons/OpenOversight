# Contributing Guide

First, thanks for being interested in helping us out! If you find an issue you're interested in, feel free to make a comment about how you're thinking of approaching implementing it in the issue and we can give you feedback.  Please also read our [code of conduct](/CODE_OF_CONDUCT.md) before getting started.

## Submitting a PR

When you come to implement your new feature, you should branch off `develop` and add commits to implement your feature. If your git history is not so clean, please do rewrite before you submit your PR - if you're not sure if you need to do this, go ahead and submit and we can let you know when you submit.

Use [PULL_REQUEST_TEMPLATE.md](/PULL_REQUEST_TEMPLATE.md) to create the description for your PR! (The template should populate automatically when you go to open the pull request.)

### Linting / Style Checks

 `flake8` is a tool for automated linting and style checks. Be sure to run `flake8` and fix any errors before submitting a PR.

## Development Environment

You can use our Docker or Vagrant/VirtualBox development environments.

### Docker

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

### VirtualBox + Vagrant

Our standard development environment is an Ubuntu 14 VM. We manage it with Vagrant, which means you'll need Vagrant and VirtualBox installed to start out.

* Install Vagrant: https://www.vagrantup.com/downloads.html
* Install VirtualBox: https://www.virtualbox.org/wiki/Downloads

Make sure you've started VirtualBox, and then in your project directory, run:

`vagrant up`

This creates a new, pristine virtual machine and provisions it to be an almost-copy of production with a local test database. (Behind the scenes, this is all happening via the files in vagrant/puppet.) If everything works, you should get a webserver listening at `http://localhost:3000` that you can browse to on your host machine.

In addition, you can now SSH into it:

`vagrant ssh`

The provisioning step creates a virtual environment (venv) in `~/oovirtenv`. If you will be running lots of python-related commands, you can 'activate' the virtual environment (override the built-in python and pip commands and add pytest and fab to your path) by activating it:
```sh
vagrant@vagrant-ubuntu-trusty-64:~$ source /home/vagrant/oovirtenv/bin/activate
```

You can tell that your virtual environment is activated by seeing the addition of `(oovirtenv)` to your prompt:
```sh
(oovirtenv)vagrant@vagrant-ubuntu-trusty-64:~$
```
When this is done, you no longer need to preface python commands (as below) with `~/oovirtenv/bin`.

In the VM instance, your code is copied to a folder inside of `/vagrant`, so you'll want to run this:
```sh
(oovirtenv)vagrant@vagrant-ubuntu-trusty-64:~$ cd /vagrant/OpenOversight
```

*Note:* the photo upload functionality - which uses an S3 bucket - and the email functionality - which
requires an email account - do not work in the development environment as they require some environment
variables to be configured.

## Server commands

The app, as provisioned, is running under gunicorn, which means that it does not dynamically reload your changes.

If you run the app in debug mode, you can see these changes take effect on every update, but certain changes will kill the server in a way some of us find really irritating. To do this:

`vagrant ssh` (if you're not already there)
```sh
$ sudo service gunicorn stop
 * Stopping Gunicorn workers
 [oo] *
(oovirtenv)vagrant@vagrant-ubuntu-trusty-64:~$ cd /vagrant/OpenOversight/ # (again, if you're not already there)
(oovirtenv)vagrant@vagrant-ubuntu-trusty-64:/vagrant/OpenOversight$ python manage.py runserver
 * Running on http://127.0.0.1:3000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
```

## Database commands

You can access your PostgreSQL development database via psql using:

```sh
psql  -h localhost -d openoversight-dev -U openoversight --password
```

with the password `terriblepassword`.


The provisioning step already does this, but in case you need it, in the `/vagrant` directory, there is a script to create the database:

```sh
~/oovirtenv/bin/python create_db.py
```

In the event that you need to create or delete the test data, you can do that with
`~/oovirtenv/bin/python test_data.py --populate` to create the data
or
`~/oovirtenv/bin/python test_data.py --cleanup` to delete the data

### Migrating the Database

If you e.g. add a new column or table, you'll need to migrate the database.

You can use the management interface to first generate migrations:

```sh
(oovirtenv)vagrant@vagrant-ubuntu-trusty-64:/vagrant/OpenOversight$ python manage.py db migrate
```

And then you should inspect/edit the migrations. You can then apply the migrations:

```sh
(oovirtenv)vagrant@vagrant-ubuntu-trusty-64:/vagrant/OpenOversight$ python manage.py db upgrade
```

You can also downgrade the database using `python manage.py db downgrade`.

## OpenOversight Management Interface

In addition to running the development server, `manage.py` (OpenOversight's management interface) can be used to do the following:

```sh
(oovirtenv)vagrant@vagrant-ubuntu-trusty-64:/vagrant/OpenOversight$ python manage.py
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
(oovirtenv)vagrant@vagrant-ubuntu-trusty-64:/vagrant/OpenOversight$ python manage.py make_admin_user
Username: redshiftzero
Email: jen@redshiftzero.com
Password:
Type your password again:
Administrator redshiftzero successfully added
```

## Running Unit Tests

 Run tests with `pytest`:

```sh
(oovirtenv)vagrant@vagrant-ubuntu-trusty-64:/vagrant/OpenOversight/$ cd tests
(oovirtenv)vagrant@vagrant-ubuntu-trusty-64:/vagrant/OpenOversight/tests$ pytest
```

## Changing the Development Environment

If you're making massive changes to the development environment provisioning, you should know that Vagrant and the Puppet modules that provision the box use Ruby, so you'll want some reasonably-modern Ruby. Anything in the 2.0-2.2 area should work. Puppet has some annoying interactions where puppet 3 doesn't work with ruby 2.2, though, so you might have to get creative on modern OSes.

If you don't have bundler installed:

`gem install bundler`

If you don't have rake installed:

`bundle install`

Then provision the VM:

`rake vagrant:provision`

Puppet modules are dropped into place by librarian-puppet, and there's a rake task that'll do it without the headache of remembering all the paths and such:

`rake vagrant:build_puppet`
