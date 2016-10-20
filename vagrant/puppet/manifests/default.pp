# Install postgres and python on the Vagrant VM
  $virtualenv = '/home/vagrant/oovirtenv'

  $database_name     = 'openoversight-dev'
  $database_server   = 'localhost'
  $database_user     = 'openoversight'
  $database_password = 'terriblepassword'

  $database_uri = "postgresql://${database_user}:${database_password}@${database_server}/${database_name}"

  $csrf_token = "terriblecsrftoken"

  class { 'postgresql::server':
    listen_addresses => '*',
  }

  postgresql::server::db { [$database_name]:
    user     => $database_user,
    password => postgresql_password($database_user, $database_password),
    encoding => 'UTF8',
  }

  class { 'python':
    pip        => present,
    dev        => present,
    gunicorn   => present,
    virtualenv => present,
  }

  file {'/vagrant/OpenOversight/.env':
    ensure  => present,
    owner   => 'vagrant',
    mode    => '0755',
    content => "SQLALCHEMY_DATABASE_URI=\"${database_uri}\"\nSECRET_KEY=${csrf_token}",
    notify  => Python::Gunicorn['oo'],
  }

  python::virtualenv {'/vagrant':
    ensure       => present,
    requirements => '/vagrant/requirements.txt',
    venv_dir     => $virtualenv,
    owner        => 'vagrant',
    require      => Package['libpq-dev'],
  }

  python::gunicorn {'oo':
    ensure     => present,
    virtualenv => $virtualenv,
    dir        => '/vagrant/OpenOversight',
    bind       => '0.0.0.0:3000',
    require    => [ File['/vagrant/OpenOversight/.env'], Postgresql::Server::Db['openoversight-dev'] ]
  }

  package {'libpq-dev': }

  exec{'set up database':
    command     => "python create_db.py",
    cwd         => '/vagrant/OpenOversight',
    path        => "${virtualenv}/bin",
    require     => [ File['/vagrant/OpenOversight/.env'], Python::Virtualenv['/vagrant'], Postgresql::Server::Db[$database_name]  ]
  }

  exec{'create test data':
    command     => "python test_data.py -p",
    cwd         => '/vagrant/OpenOversight',
    path        => "${virtualenv}/bin",
    require     => Exec['set up database'],
  }

  exec{'/usr/bin/apt-get update': }
  Exec['/usr/bin/apt-get update'] -> Package <| |>
