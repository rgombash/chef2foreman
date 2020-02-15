# chef2foreman
Script reads node data from Chef server and updates Foreman host status

Intended to be run as cronjob.

Can be used as simplified alternative to chef-handler-foreman as there is no need to modify client.rb on clients.

##How does it work ?
Script uses PyChef to get list of nodes from chef. PyCurl is used to get host list from Foreman. Matching is done to determine if chef node is registered as Foreman host. If true, last report time in Foreman is updated to last time Chef client was run. 

## Dependencies
Requires [PyChef](https://pypi.python.org/pypi/PyChef) version >= 0.2.3

## Configuration 
Change chef2foreman.ini to match your system settings

## Ideas
Script can be easily hacked to pass some additional ohai data from Chef node to Foreman
