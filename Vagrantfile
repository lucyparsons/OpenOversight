# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  config.vm.box = "ubuntu/trusty64"

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine.
   config.vm.network "forwarded_port", guest: 5000, host: 5000

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
   config.vm.provider "virtualbox" do |vb|
     # Customize the amount of memory on the VM:
     vb.memory = "512"
   end

  # Provision with our standalone-puppet provider
  config.vm.provision "puppet" do |puppet|
    puppet.manifests_path = 'vagrant/puppet/manifests'
    puppet.module_path = 'vagrant/puppet/modules'
  end
end
