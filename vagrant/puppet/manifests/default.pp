# Install prerequisites and a development environment for OpenOversight



  # Ubuntu renamed their vagrant image's default user between
  # ubuntu/trusty64 and ubuntu/xenial64. This doesn't work on
  # xenial64 yet, because of stankevich/puppet-python, but we
  # will be more prepared when the time comes maybe
  case $operatingsystemmajrelease {
    '16.04': {
      $system_user = 'ubuntu'
    }
    default: {
      $system_user = 'vagrant'
    }
  }

  $virtualenv = "/home/${system_user}/oovirtenv"

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

  python::dotfile {'/vagrant/OpenOversight/.env':
    ensure  => present,
    owner   => $system_user,
    mode    => '0644',
    config  => {
      'global' => {
        'SQLALCHEMY_DATABASE_URI' => $database_uri,
        'SECRET_KEY' => $csrf_token,
      }
    },
    notify  => Python::Gunicorn['oo'],
  }

  python::virtualenv {'/vagrant':
    ensure       => present,
    requirements => '/vagrant/requirements.txt',
    venv_dir     => $virtualenv,
    owner        => $system_user,
    require      => Package['libpq-dev'],
  }

  python::gunicorn {'oo':
    ensure     => present,
    virtualenv => $virtualenv,
    dir        => '/vagrant/OpenOversight',
    bind       => '0.0.0.0:3000',
    require    => [ File['/vagrant/OpenOversight/.env'], Postgresql::Server::Db['openoversight-dev'] ]
  }

  package {['libpq-dev', 'libffi-dev']: }

  exec{'set up database':
    command     => "python create_db.py",
    cwd         => '/vagrant',
    path        => "${virtualenv}/bin",
    user        => $system_user,
    require     => [ File['/vagrant/OpenOversight/.env'], Python::Virtualenv['/vagrant'], Postgresql::Server::Db[$database_name]  ]
  }

  exec{'create test data':
    command     => "python test_data.py -p",
    cwd         => '/vagrant',
    path        => "${virtualenv}/bin",
    user        => $system_user,
    require     => Exec['set up database'],
  }

  exec{'/usr/bin/apt-get update': }
  Exec['/usr/bin/apt-get update'] -> Package <| |>
