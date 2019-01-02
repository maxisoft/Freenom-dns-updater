FROM python:3-alpine
MAINTAINER maxisoft
LABEL Description="This image is used to start freenom dns updater" Version="1.0"

# Placeholder for armhf

RUN git clone https://github.com/bitteruhe/Freenom-dns-updater && cd Freenom-dns-updater && python3 setup.py install

CMD fdu process -i -c -t 3600 /etc/freenom.yml
