# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-16.04"

  config.vm.network "forwarded_port", guest: 5000, host: 5000, id: "Thumbtack-dev"
  config.vm.network "forwarded_port", guest: 8000, host: 8000, id: "Development"
  config.vm.network "forwarded_port", guest: 8080, host: 8080, id: "Development2"
  config.vm.network "forwarded_port", guest: 8208, host: 8208, id: "Thumbtack"
  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
    v.name = "thumbtack-dev"
  end

  config.vm.provision "shell", path: "provisioning/install.sh"

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end

  if Vagrant.has_plugin?("vagrant-vbguest")
    config.vbguest.auto_update = true
  end

end
