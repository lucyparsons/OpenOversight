source ENV['GEM_SOURCE'] || "https://rubygems.org"

group :development, :test do
  gem 'metadata-json-lint',      :require => false
  gem 'rspec-puppet',            :require => false
  gem 'puppetlabs_spec_helper', '1.1.1'
  gem 'puppet-lint',             :require => false
  gem 'pry',                     :require => false
  gem 'simplecov',               :require => false
end

# pin old versions for ruby 1.8.7
if RUBY_VERSION >= '1.8.7' and RUBY_VERSION < '1.9'
  gem 'rspec', '~> 2.0'
  gem 'rake', '~> 10.0'
else
  gem 'rake', :require => false
end

if RUBY_VERSION >= '1.8.7' and RUBY_VERSION < '2.0'
  # json 2.x requires ruby 2.0. Lock to 1.8
  gem 'json', '~> 1.8'
  # json_pure 2.0.2 requires ruby 2.0. Lock to 2.0.1
  gem 'json_pure', '= 2.0.1'
else
  gem 'json'
end

if facterversion = ENV['FACTER_GEM_VERSION']
  gem 'facter', facterversion, :require => false
else
  gem 'facter', :require => false
end

if puppetversion = ENV['PUPPET_GEM_VERSION']
  gem 'puppet', puppetversion, :require => false
else
  gem 'puppet', :require => false
end

group :system_tests do
  gem 'serverspec',              :require => false
  gem 'beaker',                  :require => false
  gem 'beaker-rspec',            :require => false
end

# vim:ft=ruby
