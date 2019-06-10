#!/usr/bin/python3
import os
import re
import sys
import time
import pyotp
import subprocess
import configparser
from jinja2 import Template

#print("Hello, world!")
#print(os.environ)

login_page = """<!DOCTYPE html>
<html>
    <head>
        <title>TOTP authentication</title>
        <style>
            body {
                background-color: rgb(102, 153, 255);
            }
            #container {
                width: 100%;
                max-width: 400px;
                height: 100px;
                margin: auto;
                margin-top: 150px;
                text-align: center;
            }
            h1 {
                font-family: sans-serif;
                color: white;
                font-size: 4em;
                margin: 0;
            }
            input {
                width: 100%;
                padding: 5px;
                border-radius: 5px;
                border: 1px solid grey;
                font-size: 5em;
                text-align: center;
                letter-spacing: 10px;
                box-sizing: border-box;
            }
        </style>
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <div id="container"> 
            <h1>TOTP login</h1>
            <form action="/auth/login.py" method="post">
                <input id="code" name="code" type="text" placeholder="code">
            </form>
        </div>
    </body>
</html>"""

config_template = """
<VirtualHost *:8080>
    ServerName {{ domain_name }}
    ProxyPassMatch ^/auth !
    ProxyPass "/" "{{ backend }}"
    ProxyPassReverse "/" "{{ backend }}"
    <Location />
        {% for ip in allowed_ips %}
        Require ip {{ ip }}
        {% endfor %}
    </Location>
    <Location /auth>
        Require all denied
    </Location>
    ErrorDocument 403 /auth/login.py
    Alias /auth /usr/local/apache2/htdocs/auth
    <Location /auth>
        Require all granted
    </Location>
</VirtualHost>
"""

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def write_config(config):
    """Write config to ./config.ini."""
    with open("/data/config.ini", "wt") as f:
        config.write(f)

def check_code(totp, code):
    """Check if the given code is as expected."""
    if re.fullmatch('code=\d{6}', code):
        return totp.verify(code.split('=')[1])
    else:
        eprint("Invalid input!")
        exit(1)

def create_config(data, restart=True):
    config_j2template = Template(config_template)
    config = config_j2template.render(
            domain_name=data['domain_name'],
            backend=data['backend'],
            allowed_ips=data['allowed_ips'].split(','))
    with open('/usr/local/apache2/conf/revproxy.conf', 'wt') as f:
        f.write(config)
    if restart:
        subprocess.Popen(['/auth/restart-apache.sh'])

def show_login():
    print(login_page)

def run():
    config = configparser.ConfigParser()
    config.read('/data/config.ini')
    if not config.has_option('totp', 'code'):
        eprint("No TOTP code found. Generating one.")
        if not config.has_section('totp'):
            config.add_section('totp')
        config['totp']['code'] = pyotp.random_base32()
        write_config(config)
    if not config.has_section('reverse_proxy'):
        config.add_section('reverse_proxy')
        config['reverse_proxy']['domain_name'] = ""
        config['reverse_proxy']['backend'] = ""
        config['reverse_proxy']['allowed_ips'] = "127.0.0.1"
        write_config(config)
        eprint("Configuration missing! Please edit /data/config.ini.")
        exit(2)
    if len(sys.argv) > 1 and sys.argv[1] == "provisioning-uri":
        totp = pyotp.TOTP(config['totp']['code'])
        print(totp.provisioning_uri("Main", issuer_name="TOTP ACL"))
        exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] == "config-setup":
        create_config(config['reverse_proxy'], restart=False)
        exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] == "get-code":
        totp = pyotp.TOTP(config['totp']['code'])
        print("TOTP code:", totp.now())
        exit(0)
    elif len(sys.argv) > 1:
        print("Supported commands:")
        print("provisioning-uri, config-setup, get-code")
        exit(1)
    if os.environ['REQUEST_METHOD'] == 'POST':
        print("Content-Type: text/html\n")
        post_data = sys.stdin.read()
        totp = pyotp.TOTP(config['totp']['code'])
        if check_code(totp, post_data):
            # Break string up in IPs and add current IP.
            new_ips = config['reverse_proxy']['allowed_ips'].split(',')
            ip = os.environ['REMOTE_ADDR']
            new_ips.append(ip)
            config['reverse_proxy']['allowed_ips'] = ','.join(new_ips)
            write_config(config)
            print("""<!DOCTYTPE html>
            <html><head><!--<meta HTTP-EQUIV="refresh" CONTENT="10;url=/">--!></head>
            <body>Your IP {} has been allowed.
            <script>setTimeout(function(){{window.open("/","_self");}}, 5000);</script>
            </body></html>""".format(ip))
            eprint("IP address added as allowed:", ip)
            create_config(config['reverse_proxy'])
        else:
            show_login()
    elif os.environ['REQUEST_METHOD'] == 'GET':
        print("Content-Type: text/html\n")
        show_login()
    else:
        eprint("Invalid request method")
        exit(1)

if __name__ == '__main__':
    run()
