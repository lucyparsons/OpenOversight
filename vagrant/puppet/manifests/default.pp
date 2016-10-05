# Install postgres and python on the Vagrant VM
  class { 'postgresql::server':
    listen_addresses => '*',
  }

  postgresql::server::db { ['openoversight-dev']:
    user => 'openoversight',
    password => postgresql_password('openoversight','terriblepassword'),
    encoding => 'UTF8',
  }

  class { 'python':
		pip      => present,
		dev      => present,
		gunicorn => present,
    virtualenv => present,
  }
  python::virtualenv {'/vagrant':
    ensure => present,
    requirements => '/vagrant/requirements.txt',
    venv_dir => '/home/vagrant/oovirtenv',
    owner => 'vagrant',
  }

  python::gunicorn {'oo':
    ensure => present,
    virtualenv => '/home/vagrant/oovirtenv',
    dir => '/vagrant/OpenOversight',
    bind => '0.0.0.0:3000'
  }

  package {'libpq-dev': }

