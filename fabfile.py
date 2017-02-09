from __future__ import with_statement
from fabric.api import env, local, run, sudo, cd, hosts, get
from fabric.context_managers import prefix
from fabric.contrib.console import confirm
import datetime, os
from os.path import expanduser
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

basedir = os.path.abspath(os.path.dirname(__file__))

env.use_ssh_config = False

# Hosts
# env.hosts list references aliases in ~/.ssh/config or IP address. When using .ssh/config,
# fab will use the ssh keyfile referenced by the host alias, otherwise need to do what is
# being done in dev to assign env a key_filename


def staging():
    env.hosts=['162.243.156.49']
    env.user='root'
    env.host='staging.openoversight.lucyparsonslabs.com'


def production():
    env.hosts=['45.55.11.175']
    env.user='root'
    env.host='openoversight.lucyparsonslabs.com'


def deploy():
    if env.host=='openoversight.lucyparsonslabs.com':
        venv_dir='/home/nginx/oovirtenv'
        code_dir='/home/nginx/oovirtenv/OpenOversight'
    else:
	venv_dir='/home/nginx/oovirtenv/venv'
        code_dir='/home/nginx/oovirtenv/venv/OpenOversight'
    with cd(code_dir):
        run('su nginx -c "git status"')
        confirm("Update to latest commit in this branch?")
        run('su nginx -c "git pull"')
        run('su nginx -c "%s/bin/pip install -r requirements.txt"' % venv_dir)
        run('systemctl restart openoversight')


def backup():
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    with cd('/home/nginx/OpenOversight_backup/'):
        run('pg_dump %s -f backup.sql' % SQLALCHEMY_DATABASE_URI)
        run('mv backup.sql backup.sql_`date +"%d-%m-%Y"`')
        run('find . -type f -mtime -5 -print0 | xargs tar czfv backup.tar.gz')
        get(remote_path="/home/nginx/OpenOversight_backup/backup.tar.gz", local_path="~/backup")
