#!/usr/bin/python
import sys
import json
import pycurl
import cStringIO
import chef
import datetime
import ConfigParser
import logging

# Load config
config = ConfigParser.SafeConfigParser()
config.read('chef2foreman.ini')

#setup logger
logging.basicConfig(level=config.getint('MAIN', 'log_level'))
logger = logging.getLogger()

logging.info("started at:"+str(datetime.datetime.now()))

# cURL function based on pycurl for foreman GET and POST requests
def curl_put(url, data, type='POST'):    
    response = cStringIO.StringIO()

    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.SSL_VERIFYPEER, 0)
    c.setopt(pycurl.SSL_VERIFYHOST, 0)
    c.setopt(pycurl.USERPWD, config.get('FOREMAN', 'foreman_userpass'))
    c.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json'])
    if type == 'POST':
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.POSTFIELDS, data)
        c.setopt(c.WRITEFUNCTION, response.write)
        c.perform()    
        out = json.loads(response.getvalue())
    if type == 'GET':                                
        c.setopt(c.WRITEDATA, response)
        c.perform()    
        out = json.loads(response.getvalue())
    
    c.close()  
    
    return out

# get all foreman hosts
def get_foreman_hosts():
    hosts = []
    result = curl_put(config.get('FOREMAN', 'foreman_url') + '/api/hosts', '', 'GET')   
    
    logging.debug(result)    
    
    for node in result['results']:        
        hosts.append(node['name'])        
        if logger.getEffectiveLevel() <= 10:
            sys.stdout.write('.')    
    
    return hosts

def get_chef_hosts():
    hosts = {}

    # gets all chef hosts that have ohai_time set (chef-client has been run at least one time)
    with chef.ChefAPI(config.get('CHEF', 'chef_url'),config.get('CHEF', 'chef_pem_path'),config.get('CHEF', 'chef_user')):          
        for node in chef.Node.list():           
            if logger.getEffectiveLevel() <= 10:
                sys.stdout.write('.')
            n = chef.Node(node)         
            # is ohai time set?
            ohai_time = n.get('ohai_time')
            if ohai_time != None:                       
                lastupdate = datetime.datetime.fromtimestamp(int(ohai_time)).strftime('%Y-%m-%d %H:%M:%S')          
                # if needed addotional ohai data cen be added here
                hosts.update ({ node : {'lastupdate' : lastupdate, 'fqdn' : n.get('fqdn')}} )
        
        return hosts   

# fetch data
chef_hosts = get_chef_hosts()
foreman_hosts = get_foreman_hosts()

# Host matching
# Loop through chef hosts and only report hosts that are available in foreman
# Matching is done by comparing fqdn's of the hosts
for node in chef_hosts:
    if chef_hosts[node]['fqdn'] in foreman_hosts:
                
        fqdn = chef_hosts[node]['fqdn']
        lastupdate = chef_hosts[node]['lastupdate']
        
        logging.debug(fqdn)
        logging.debug("lastupdate:"+lastupdate)

        # send report to foreman
        json_data = '{ "report": {"host": "' + fqdn + '", "reported_at" : "' + lastupdate + '", "status" : {}, "metrics" : {}, "logs" : {}}'
        result  = curl_put(config.get('FOREMAN', 'foreman_url') + '/api/reports', json_data)
        
        logging.debug(result)

logging.info("finished at:"+str(datetime.datetime.now()))