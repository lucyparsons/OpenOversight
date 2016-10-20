# Contributing Guide

First, thanks for being interested in helping us out! If you find an issue you're interested in, feel free to make a comment about how you're thinking of approaching implementing it in the issue and we can give you feedback. 

## Submitting a PR

When you come to implement your new feature, you should branch off `develop` and add commits to implement your feature. If your git history is not so clean, please do rewrite before you submit your PR - if you're not sure if you need to do this, go ahead and submit and we can let you know when you submit. 

## Development Environment

Our standard development environment is an Ubuntu 14 VM. We manage it with Vagrant, which means you'll need Vagrant and Virtualbox installed to start out. Vagrant and the Puppet modules that provision the box use Ruby, so you'll want some reasonably-modern Ruby. Anything in the 2.0-2.2 area should work.

If you don't have bundler installed:

`gem install bundler`

If you don't have rake installed:

`bundle install`

Then provision the VM:

`rake vagrant:provision`

This brings the vagrant box up and provisions it. (Behind the scenes, it's grabbing some puppet modules and then running `vagrant up`.) If everything works, you should get a webserver listening at `http://localhost:3000` you can browse to. In addition, you can now SSH into it:

`vagrant ssh`

The app is running under gunicorn, which means that it does not dynamically reload your changes.

If you run the app in debug mode, you can see these changes take effect on every update, but certain changes will kill the server. To do this:

`vagrant ssh` (if you're not already there)
```
$ sudo service gunicorn stop
 * Stopping Gunicorn workers
 [oo] *
vagrant@vagrant-ubuntu-trusty-64:~$ cd /vagrant/OpenOversight/
vagrant@vagrant-ubuntu-trusty-64:/vagrant/OpenOversight$ ~/oovirtenv/bin/python ./run.py
 * Running on http://127.0.0.1:3000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
```

You can access your PostgreSQL development database via psql using:

`psql  -h localhost -d openoversight-dev -U openoversight --password`

with the password `terriblepassword`.

The provisioning step already does this, but in case you need it, in the `/vagrant/OpenOversight` directory, there is a script to create the database:

`python create_db.py`

If the database doesn't already exist, `create_db.py` will set it up and store the version in a new folder `db_repository`. 

In the event that you need to create or delete the test data, you can do that with
`python test_data.py --populate`
or
`python test_data.py --cleanup`

## Running Unit Tests

 Run tests with `nose`:

```nosetests -v```

Note: One could put `test_data.populate()` into `setUp` and `test_data.cleanup()` into `tearDown` but in this case we want the data to stay in the database so that we can play with the web application so we should just have vagrant run that during the provisioning of the development VM.

## Migrating the Database

If you e.g. add a new column or table, you'll need to migrate the database. You can use:

`python migrate_db.py`

to do this.
`python upgrade_db.py` and `python downgrade_db.py` can also be used as necessary. Note that I followed [this tutorial](http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database) to set this up.