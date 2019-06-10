# totp-haproxy
Docker container with a reverse proxy.

## Goal
Create a smaller attack vector for internet-connected web services such as a Synology NAS.

## What's the idea?
When there's an incoming connection from an unknown IP address, a login page will be displayed. An TOTP can be entered after which the IP will be whitelisted.

