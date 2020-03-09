# Build the egg first
FROM python:3-alpine as builder

WORKDIR /tmp/build
COPY . .
RUN python3 setup.py bdist_egg

# The real image to be built
FROM python:3-alpine
MAINTAINER maxisoft
LABEL Description="This image is used to start freenom dns updater" Version="1.0"

WORKDIR /tmp/build
COPY --from=builder /tmp/build/dist/*.egg .

RUN python -m easy_install ./*.egg && \
     rm -rf *

WORKDIR /

CMD fdu process /etc/freenom.yml

