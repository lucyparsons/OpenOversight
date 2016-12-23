require 'spec_helper'

describe 'python', :type => :class do
  context "on Debian OS" do
    let :facts do
      {
        :id                     => 'root',
        :kernel                 => 'Linux',
        :lsbdistcodename        => 'squeeze',
        :osfamily               => 'Debian',
        :operatingsystem        => 'Debian',
        :operatingsystemrelease => '6',
        :path                   => '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        :concat_basedir         => '/dne',
      }
    end

    it { is_expected.to contain_class("python::install") }
    # Base debian packages.
    it { is_expected.to contain_package("python") }
    it { is_expected.to contain_package("python-dev") }
    it { is_expected.to contain_package("pip") }
    # Basic python packages (from pip)
    it { is_expected.to contain_package("virtualenv")}

    describe "with python::dev" do
      context "true" do
        let (:params) {{ :dev => 'present' }}
        it { is_expected.to contain_package("python-dev").with_ensure('present') }
      end
      context "empty/default" do
        it { is_expected.to contain_package("python-dev").with_ensure('absent') }
      end
    end

    describe "with manage_gunicorn" do
      context "true" do
        let (:params) {{ :manage_gunicorn => true }}
        it { is_expected.to contain_package("gunicorn") }
      end
      context "empty args" do
        #let (:params) {{ :manage_gunicorn => '' }}
        it { is_expected.to contain_package("gunicorn") }
      end
      context "false" do
        let (:params) {{ :manage_gunicorn => false }}
        it {is_expected.not_to contain_package("gunicorn")}
      end
    end

    describe "with python::provider" do
      context "pip" do
        let (:params) {{ :provider => 'pip' }}
        it { is_expected.to contain_package("virtualenv").with(
          'provider' => 'pip'
        )}
        it { is_expected.to contain_package("pip").with(
          'provider' => 'pip'
        )}
      end

      # python::provider
      context "default" do
        let (:params) {{ :provider => '' }}
        it { is_expected.to contain_package("virtualenv")}
        it { is_expected.to contain_package("pip")}

        describe "with python::virtualenv" do
          context "true" do
            let (:params) {{ :provider => '', :virtualenv => true }}
            it { is_expected.to contain_package("virtualenv").with_ensure('present') }
          end
        end

        describe "without python::virtualenv" do
          context "default/empty" do
            let (:params) {{ :provider => '' }}
            it { is_expected.to contain_package("virtualenv").with_ensure('absent') }
          end
        end
      end
    end

    describe "with python::dev" do
      context "true" do
        let (:params) {{ :dev => 'present' }}
        it { is_expected.to contain_package("python-dev").with_ensure('present') }
      end
      context "default/empty" do
        it { is_expected.to contain_package("python-dev").with_ensure('absent') }
      end
    end
  end

  context "on a Redhat 5 OS" do
    let :facts do
      {
        :id => 'root',
        :kernel => 'Linux',
        :osfamily => 'RedHat',
        :operatingsystem => 'RedHat',
        :operatingsystemrelease => '5',
        :concat_basedir => '/dne',
        :path => '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
      }
    end
    it { is_expected.to contain_class("python::install") }
    # Base debian packages.
    it { is_expected.to contain_package("python") }
    it { is_expected.to contain_package("python-dev").with_name("python-devel") }
    it { is_expected.to contain_package("pip") }
    # Basic python packages (from pip)
    it { is_expected.to contain_package("virtualenv")}

    describe "with python::dev" do
      context "true" do
        let (:params) {{ :dev => 'present' }}
        it { is_expected.to contain_package("python-dev").with_ensure('present') }
      end
      context "empty/default" do
        it { is_expected.to contain_package("python-dev").with_ensure('absent') }
      end
    end

    describe "with manage_gunicorn" do
      context "true" do
        let (:params) {{ :manage_gunicorn => true }}
        it { is_expected.to contain_package("gunicorn") }
      end
      context "empty args" do
        #let (:params) {{ :manage_gunicorn => '' }}
        it { is_expected.to contain_package("gunicorn") }
      end
      context "false" do
        let (:params) {{ :manage_gunicorn => false }}
        it {is_expected.not_to contain_package("gunicorn")}
      end
    end

    describe "with python::provider" do
      context "pip" do
        let (:params) {{ :provider => 'pip' }}

        it { is_expected.to contain_package("virtualenv").with(
          'provider' => 'pip'
        )}
        it { is_expected.to contain_package("pip").with(
          'provider' => 'pip'
        )}
      end

      # python::provider
      context "default" do
        let (:params) {{ :provider => '' }}
        it { is_expected.to contain_package("virtualenv")}
        it { is_expected.to contain_package("pip")}

        describe "with python::virtualenv" do
          context "true" do
            let (:params) {{ :provider => '', :virtualenv => 'present' }}
            it { is_expected.to contain_package("virtualenv").with_ensure('present') }
          end
        end

        describe "with python::virtualenv" do
          context "default/empty" do
            let (:params) {{ :provider => '' }}
            it { is_expected.to contain_package("virtualenv").with_ensure('absent') }
          end
        end
      end
    end

    describe "with python::dev" do
      context "true" do
        let (:params) {{ :dev => 'present' }}
        it { is_expected.to contain_package("python-dev").with_ensure('present') }
      end
      context "default/empty" do
        it { is_expected.to contain_package("python-dev").with_ensure('absent') }
      end
    end
  end

  context "on a SLES 11 SP3" do
    let :facts do
      {
        :id => 'root',
        :kernel => 'Linux',
        :lsbdistcodename => nil,
        :osfamily => 'Suse',
        :operatingsystem => 'SLES',
        :operatingsystemrelease => '11.3',
        :concat_basedir => '/dne',
        :path => '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
      }
    end
    it { is_expected.to contain_class("python::install") }
    # Base Suse packages.
    it { is_expected.to contain_package("python") }
    it { is_expected.to contain_package("python-dev").with_name("python-devel") }
    it { is_expected.to contain_package("pip") }
    # Basic python packages (from pip)
    it { is_expected.to contain_package("virtualenv")}

    describe "with python::dev" do
      context "true" do
        let (:params) {{ :dev => 'present' }}
        it { is_expected.to contain_package("python-dev").with_ensure('present') }
      end
      context "empty/default" do
        it { is_expected.to contain_package("python-dev").with_ensure('absent') }
      end
    end

    describe "with manage_gunicorn" do
      context "true" do
        let (:params) {{ :manage_gunicorn => true }}
        it { is_expected.to contain_package("gunicorn") }
      end
      context "empty args" do
        #let (:params) {{ :manage_gunicorn => '' }}
        it { is_expected.to contain_package("gunicorn") }
      end
      context "false" do
        let (:params) {{ :manage_gunicorn => false }}
        it {is_expected.not_to contain_package("gunicorn")}
      end
    end

    describe "with python::provider" do
      context "pip" do
        let (:params) {{ :provider => 'pip' }}

        it { is_expected.to contain_package("virtualenv").with(
          'provider' => 'pip'
        )}
        it { is_expected.to contain_package("pip").with(
          'provider' => 'pip'
        )}
      end

      # python::provider
      context "default" do
        let (:params) {{ :provider => '' }}
        it { is_expected.to contain_package("virtualenv")}
        it { is_expected.to contain_package("pip")}

        describe "with python::virtualenv" do
          context "true" do
            let (:params) {{ :provider => '', :virtualenv => 'present' }}
            it { is_expected.to contain_package("virtualenv").with_ensure('present') }
          end
        end

        describe "with python::virtualenv" do
          context "default/empty" do
            let (:params) {{ :provider => '' }}
            it { is_expected.to contain_package("virtualenv").with_ensure('absent') }
          end
        end
      end
    end

    describe "with python::dev" do
      context "true" do
        let (:params) {{ :dev => 'present' }}
        it { is_expected.to contain_package("python-dev").with_ensure('present') }
      end
      context "default/empty" do
        it { is_expected.to contain_package("python-dev").with_ensure('absent') }
      end
    end
  end
end
