FROM httpd:latest
RUN chown -R www-data:www-data /usr/local/apache2/logs && \
    apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install pyotp Jinja2 && \
    mkdir /data && \
    mkdir /auth && \
    chown www-data /data && \
    chown www-data -R /usr/local/apache2/conf
COPY httpd.conf /usr/local/apache2/conf/httpd.conf
COPY auth /auth
COPY login.py /usr/local/apache2/htdocs/auth/login.py
CMD /auth/docker-entrypoint.sh
USER www-data
#COPY --chown=www-data src /usr/local/apache2/htdocs/auth

