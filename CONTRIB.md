# Contributing Guide

First, thanks for being interested in helping us out! If you find an issue you're interested in, feel free to make a comment about how you're thinking of approaching implementing it in the issue and we can give you feedback. 

## Submitting a PR

When you come to implement your new feature, you should branch off `develop` and add commits to implement your feature. If your git history is not so clean, please do rewrite before you submit your PR - if you're not sure if you need to do this, go ahead and submit and we can let you know when you submit. 

## Development Environment

If you don't have bundler installed:

`gem install bundler`

Then provision the VM:

`rake vagrant:provision`

This brings the vagrant box up and you can now SSH into it:

`vagrant ssh`

You can access the PostgreSQL development database via psql using:

`psql  -h localhost -d openoversight-dev -U openoversight --password`

with the password `terriblepassword`. 

For the webapp, the credentials for the testing/development environment are expected to be in a file `$PGPASS`, so set that up: 

`echo "localhost:5432:openoversight-dev:openoversight:terriblepassword" > ~/.pgpass`
`echo "export PGPASS=~/.pgpass" > ~/.bashrc`
`source ~/.bashrc`

In the `/vagrant/OpenOversight` directory, there is a script to create the database:

`python create_db.py`

If the database doesn't already exist, `create_db.py` will set it up and store the version in a new folder `db_repository`. 


After you create the database, run `test_data.populate()` to put test officers, assignments, and images into the database. 


## Running Unit Tests

 Run tests with `nose`:

```nosetests -v```

Note: One could put `test_data.populate()` into `setUp` and `test_data.cleanup()` into `tearDown` but in this case we want the data to stay in the database so that we can play with the web application so we should just have vagrant run that during the provisioning of the development VM. 

## Migrating the Database

If you e.g. add a new column or table, you'll need to migrate the database. You can use:

`python migrate_db.py`

to do this.
`python upgrade_db.py` and `python downgrade_db.py` can also be used as necessary. Note that I followed [this tutorial](http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database) to set this up.
