local = data_bag_item('data', 'local')
name = local['username']

group name
user name do
  gid name
  home "/home/#{name}"
end

directory "/home/#{name}" do
  owner name
  group name
  mode "0755"
end
