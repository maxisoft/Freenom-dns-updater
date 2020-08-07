FROM python:3-alpine as builder
RUN mkdir -p '/opt/freenom_dns_updater'
COPY . /opt/freenom_dns_updater/tmp
WORKDIR /opt/freenom_dns_updater
RUN python3 -m pip install --no-cache-dir /opt/freenom_dns_updater/tmp/dist/freenom*.whl
RUN rm -rf /opt/freenom_dns_updater/tmp

FROM python:3-alpine
LABEL Description="This image is used to start freenom dns updater" Version="1.0"
COPY --from=builder / /
WORKDIR /opt/freenom_dns_updater
CMD fdu process -i -c -t 3600 /etc/freenom.yml
