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

You can develop from here and also access the PostgreSQL development database via:

`psql  -h localhost -d openoversight-dev -U openoversight --password`

with the password `terriblepassword`. 

The credentials for the testing/development set up are expected to be in a file `$PGPASS`, so set that up: 

`echo "localhost:5432:openoversight-dev:openoversight:terriblepassword" >> ~/.pgpass`

## Running Unit Tests