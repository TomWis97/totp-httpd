#!/bin/sh
set -e
/usr/local/apache2/htdocs/auth/login.py config-setup
#/auth/login.py config-setup
exec httpd-foreground
