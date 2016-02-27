FROM frolvlad/alpine-python3
MAINTAINER maxisoft
LABEL Description="This image is used to start freenom dns updater" Version="1.0"

# Placeholder for armhf

ADD https://github.com/maxisoft/Freenom-dns-updater/archive/master.zip fdu.zip
RUN unzip fdu.zip \
	&& rm fdu.zip \
	&& pip3 install ./Freenom-dns-updater-master \
	&& rm -rf Freenom-dns-updater-master

CMD fdu process /etc/freenom.yml