FROM multiarch/alpine:armhf-v3.3
MAINTAINER maxisoft
LABEL Description="This image is used to start freenom dns updater" Version="1.0"

RUN apk add --no-cache python3 && \
    apk add --no-cache --virtual=build-dependencies wget ca-certificates && \
    wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3 && \
    apk del build-dependencies

ADD https://github.com/maxisoft/Freenom-dns-updater/archive/master.zip fdu.zip
RUN unzip fdu.zip \
	&& rm fdu.zip \
	&& pip3 install ./Freenom-dns-updater-master \
	&& rm -rf Freenom-dns-updater-master

CMD fdu process /etc/freenom.yml