from subprocess import Popen, PIPE
from httplib import HTTPSConnection
from base64 import b64encode
import simplejson as json


def getDomains():
    try:
        domfile = open('/home/vpopmail/domains/domains.txt')
        return domfile.readlines()
    except:
        return False

def getDomainUsers(domain):
    try:
        pwdfile = open('/home/vpopmail/domains/%s/vpasswd' % domain)
        return pwdfile.readlines()     
    except:
        return False

def getDomainAliases(domain):
        alias_list = []
        try:
            p = Popen(["/home/vpopmail/bin/valias", domain], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            for line in p.stdout.readlines():
                line = line.strip()
                alias_list.append({"src": line[:line.find(' -> ')], "dst": line[line.find('&')+1:]})    
        except:
            pass
        return alias_list

def getUserDetails(email):
    try:
        p = Popen(["/home/vpopmail/bin/vuserinfo", "-C", "-q", email], stdin=PIPE, stdout=PIPE, stderr=PIPE)

        password = p.stdout.readline().strip()
        quota = p.stdout.readline().strip()

        if quota == "NOQUOTA":
            quota = 0
        elif quota.find('S'):
            quota = quota[:-1]

        return {"email": email, "quota": quota, "password": password}
    except:
        return False   

##########################################################################################

migration_list = []
errors_list = []

domains = getDomains()
if not domains:
    print "Could not retrieve domains listing."
else:
    for domain in domains:
        domain = domain.strip()     # Trim whitespace and carriage returns

        alias_list = getDomainAliases(domain)

        users = getDomainUsers(domain)
        if not users:
            errors_list.append(domain)
            continue

        users_list = []
        for user in users:
            try:
                email = "%s@%s" % (user.strip()[0:user.find(':')], domain)
                user_details = getUserDetails(email)
                if not user_details:
                    errors_list.append(user)
                else:
                    users_list.append(user_details) 
            except: 
                errors_list.append(user)

        migration_list.append({"domain":domain, "users": users_list, "aliases": alias_list})

    print json.dumps({"success":migration_list, "failed":errors_list})
