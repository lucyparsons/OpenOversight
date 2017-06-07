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
  $development = true

  $geckodriver_version = 'v0.13.0'
  $geckodriver_url = "https://github.com/mozilla/geckodriver/releases/download/${geckodriver_version}/geckodriver-${geckodriver_version}-linux64.tar.gz"

  $virtualenv = "/home/${system_user}/oovirtenv"
  $source_path = '/vagrant'
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

  python::dotfile {"${source_path}/OpenOversight/.env":
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

  python::virtualenv {$virtualenv:
    ensure       => present,
    requirements => "${source_path}/requirements.txt",
    venv_dir     => $virtualenv,
    owner        => $system_user,
    require      => Package['libpq-dev'],
  }

  if $development {
    python::requirements { "${source_path}/dev-requirements.txt":
      virtualenv => $virtualenv,
      owner      => $system_user,
      require    => [ Package['firefox'], Python::Virtualenv[$virtualenv] ],
    }

    package {['firefox', 'Xvfb']: }

    exec {'download and install geckodriver': # This is ugly but I'm not going to pull in an archive module for one file
      command => "/usr/bin/wget ${geckodriver_url} && tar zxvf geckodriver-* && mv geckodriver bin",
      cwd     => "/usr/local",
    }
  }

  python::gunicorn {'oo':
    ensure     => present,
    virtualenv => $virtualenv,
    dir        => "${source_path}/OpenOversight",
    bind       => '0.0.0.0:3000',
    require    => [ File["${source_path}/OpenOversight/.env"], Postgresql::Server::Db['openoversight-dev'] ]
  }

  package {['libpq-dev', 'libffi-dev']: }

  exec{'set up database':
    command     => "python create_db.py",
    cwd         => $source_path,
    path        => "${virtualenv}/bin",
    user        => $system_user,
    require     => [ File["${source_path}/OpenOversight/.env"], Python::Virtualenv[$virtualenv], Postgresql::Server::Db[$database_name]  ]
  }

  exec{'create test data':
    command     => "python test_data.py -p",
    cwd         => $source_path,
    path        => "${virtualenv}/bin",
    user        => $system_user,
    require     => Exec['set up database'],
  }

  file {'/tmp/openoversight.log':
    ensure  => present,
    owner   => $system_user,
    group   => $system_user,
    mode    => '0644',
  }

  exec{'/usr/bin/apt-get update': }
  Exec['/usr/bin/apt-get update'] -> Package <| |>
