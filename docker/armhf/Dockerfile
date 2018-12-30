FROM multiarch/alpine:armhf-v3.3
MAINTAINER maxisoft
LABEL Description="This image is used to start freenom dns updater" Version="1.0"


RUN apk add --no-cache git && \
    apk add --no-cache python3

RUN git clone https://github.com/bitteruhe/Freenom-dns-updater && cd Freenom-dns-updater && python3 setup.py install

CMD fdu process -c -t 3600 /etc/freenom.yml
