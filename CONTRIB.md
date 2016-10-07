# Contributing Guide

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

## Running Unit Tests