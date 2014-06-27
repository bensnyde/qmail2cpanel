qmail2cpanel
============

Qmail/Vpopmail to CPanel Email Migration

An authomated <a href="http://www.fabfile.com">Fabric</a> script to migrate email domains/users/quotas/passwords/messages from a Vpopmail/Qmail server to a Cpanel server.  


Notes
============

One additional variable required by Cpanel that will not be present on the Qmail/Vpopmail is the Cpanel Account Username. The script currently prompts for this variable for each domain. This routine could easily be rewritten if you have another way to fetch/generate this variable.

For seamless migrations, you'll want to set the Cpanel Account's primary IP Address to match that of the Qmail/Vpopmail. Currently this IP Address is defined as a Global Variable in fabfile.py. Again, this routine could be rewritten if you have other means/plans for the IP Address.

Usage
============

1. Configure fabfile.py with server variables
2. # fab enumerate
