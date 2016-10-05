desc 'install the gems required for vagrant/puppet'
task :bundle_install do
  sh 'bundle install'
end

namespace :vagrant do
  desc 'build the puppet modules required for vagrant'
  task :build_puppet do
    sh 'cd vagrant/puppet && librarian-puppet install --verbose --path=modules'
  end

  desc 'bring up the vagrant development VM'
  task :provision => [:bundle_install, 'vagrant:build_puppet']  do
    sh 'vagrant up'
  end
end
