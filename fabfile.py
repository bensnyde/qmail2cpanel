from subprocess import Popen, PIPE
from httplib import HTTPSConnection
from base64 import b64encode
from fabric.api import *
import json


env.hosts=["qmail.example.com"]
env.user="root"
env.password="password"

qmail_ip = "x.x.x.x"
qmail_tmpdir = "/tmp/"

whm_url = "whm.example.com"
whm_user = "root"
whm_password = "password"
whm_port = 2087


def enumerate():
    listing = parse(fetch())
    post(listing)

# Function to retrieve domains/accounts from latte servers
def fetch():
    put('enumerate_latte.py', '%eenumerate.py' % qmail_tmpdir)
    result = run('python %eenumerate.py' % qmail_tmpdir)
    run('rm -rf %eenumerate.py*' % qmail_tmpdir)
    return result

def parse(miglist):
    try:
        miglist = json.loads(miglist)
        success_list = miglist["success"]
        failed_list = miglist["failed"]
    except:
        print "Could not parse qmail data."
        return []

    if len(failed_list) > 0:
        print "The following domains/users were skipped:"
        for failed in failed_list:
            print "\t%s" % failed

    print "Total domains: %d" % len(success_list)
    for domain in success_list:
        # Manually populate Cpanel username for each domain
        while True:
            cpanel_username = raw_input("Enter the Cpanel username for %s: " % domain["domain"])
            cpanel_username = cpanel_username.strip()
            if len(cpanel_username) > 0 or len(cpanel_username) <9:
                domain["cpanel_username"] = cpanel_username
                break    

    return success_list

def post(miglist):
    print "\n\nPosting information to Cpanel:"
    for domain in miglist:
        # DOMAIN
        result = cpanel_create_domain(domain["cpanel_username"], domain["domain"])
        if not result:
            continue

        # IP Address
        cpanel_set_primary_ip(domain["domain"])

           # Users
        for user in domain["users"]:
            result = cpanel_create_pop_account(domain["cpanel_username"], domain["domain"], user["email"], user["password"], user["quota"])
            if not result:
                continue

            # Sync mailbox
            imap_sync(user["email"], user["password"])

        # Aliases
        for alias in domain["aliases"]:
            cpanel_create_alias(domain["cpanel_username"], domain["domain"], alias["src"], alias["dst"])


# Function to query CPanel API
def http_query(url, port, username, password, querystr):
    try:
        conn = HTTPSConnection(url, port)
        conn.request('GET', querystr, headers={'Authorization':'Basic ' + b64encode(username+':'+password).decode('ascii')})
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return json.loads(data)
    except:
        return False

def cpanel_create_alias(cpanel_username, domain, src, dst):
    print "\t\tCreating forward %s -> %s" % (src, dst)
    # Query Cpanel to add forward
    result = http_query(whm_url, whm_port, whm_user, whm_password, '/json-api/cpanel?cpanel_jsonapi_user=%s&cpanel_jsonapi_module=Email&cpanel_jsonapi_func=addforward&cpanel_xmlapi_version=2&domain=%s&email=%s&fwdopt=fwd&fwdemail=%s' % (cpanel_username, domain, src, dst))
    try:
        if result["cpanelresult"]["event"]["result"] == 1:
            return True            
    except:
        pass
    print "\t\t\tERROR creating forward %s -> %s" % (src, dst)
    return False    

def cpanel_create_pop_account(cpanel_username, domain, email, password, quota):
    print "\t\tCreating user %s" % email
    # Query Cpanel to add pop account
    result = http_query(whm_url, whm_port, whm_user, whm_password, '/json-api/cpanel?cpanel_jsonapi_user=%s&cpanel_jsonapi_module=Email&cpanel_jsonapi_func=addpop&cpanel_xmlapi_version=2&domain=%s&email=%s&password=%s&quota=%s' % (cpanel_username, domain, email, password, quota))
    try:
        if result["cpanelresult"]["data"][0]["result"] == 1:
            return True
        else:
            print "\t\t\tERROR creating %s: %s" % (email, result)
    except:
        print "\t\t\tERROR creating %s" % email 
    return False

def cpanel_set_primary_ip(domain):
    print "\t\tSetting domain's primary IP address"
    result = http_query(whm_url, whm_port, whm_user, whm_password, '/json-api/setsiteip?domain=%s&ip=%s' % (domain, qmail_ip))
    try:
        if result["result"][0]["status"] == 1:
            return True
        else:
            print "\t\t\tERROR setting domain's ip address: %s" % result["result"][0]["statusmsg"]
    except:
        print "\t\t\tError setting domain's IP Address" 
    return False

def cpanel_create_domain(cpanel_username, domain):
    print "\tCreating domain %s" % domain
    result = http_query(whm_url, whm_port, whm_user, whm_password, '/json-api/createacct?username=%s&domain=%s' % (cpanel_username, domain))
    try:
        if result["result"][0]["status"] == 1:
            return True
        else:
            print "\t\tERROR creating %s: %s" % (domain, result["result"][0]["statusmsg"])
    except:
        print "\t\tERROR creating %s" % domain
    return False

def imap_sync(email, password):
    print "\t\tSynching mailbox %s" % email
    try:
        p = Popen(["/usr/bin/imapsync --buffersize 8192000 --nosyncacls --subscribe --syncinternaldates --host1 %s --user1 %s --password1 \"%s\" -ssl1 --port1 993 --host2 %s --user2 %s --password2 \"%s\" -ssl2 --port2 993 --noauthmd5" % (qmail_ip, email, password, whm_url, email, password)], shell=True, stdout=PIPE, stderr=PIPE)
        if not p.wait():
            return True
    except:
        pass
    print "\t\t\tERROR %s mailbox synch failed" % email
    return False
