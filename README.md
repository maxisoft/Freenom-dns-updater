# Freenom dns updater
[![GitHub license](https://img.shields.io/github/license/maxisoft/Freenom-dns-updater)](https://github.com/maxisoft/Freenom-dns-updater/blob/main/LICENSE.txt)
![Unit Test dev and main branch](https://github.com/maxisoft/Freenom-dns-updater/workflows/Unit%20Test%20dev%20and%20main%20branch/badge.svg)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/Freenom-dns-updater)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/maxisoft/Freenom-dns-updater.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/maxisoft/Freenom-dns-updater/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/maxisoft/Freenom-dns-updater.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/maxisoft/Freenom-dns-updater/context:python)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=maxisoft_Freenom-dns-updater&metric=alert_status)](https://sonarcloud.io/dashboard?id=maxisoft_Freenom-dns-updater)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=maxisoft_Freenom-dns-updater&metric=ncloc)](https://sonarcloud.io/dashboard?id=maxisoft_Freenom-dns-updater)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=maxisoft_Freenom-dns-updater&metric=vulnerabilities)](https://sonarcloud.io/dashboard?id=maxisoft_Freenom-dns-updater)
[![deepcode](https://www.deepcode.ai/api/gh/badge?key=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwbGF0Zm9ybTEiOiJnaCIsIm93bmVyMSI6Im1heGlzb2Z0IiwicmVwbzEiOiJGcmVlbm9tLWRucy11cGRhdGVyIiwiaW5jbHVkZUxpbnQiOmZhbHNlLCJhdXRob3JJZCI6MjIxNjYsImlhdCI6MTU5ODc5ODUyNn0.S6xv8IeJvEm6gE7HYJe4wHdv2hIX0tYFvGAZIonb9ac)](https://www.deepcode.ai/app/gh/maxisoft/Freenom-dns-updater/_/dashboard?utm_content=gh%2Fmaxisoft%2FFreenom-dns-updater)

A tool written in python to update [freenom](http://Freenom.com)'s dns records

## Main Features
* Manage (add/update/remove) a domain's dns record with cli
* Automatic records updates according to ip (v4/v6) changes
* Auto renew domains (thanks to [Cedric Farinazzo](https://github.com/cedricfarinazzo))

## Upcoming features
* Password encryption

## Installation
```bash
pip install freenom-dns-updater
```
## Usage

### Basic usage
Let's say you want to add or update your main A/AAAA domain records *exemple.tk* with your current ip (v4/v6).
Simply type :
```
fdu record update $LOGIN $PASSWORD exemple.tk
```

Note that if you don't have a ipv6 access, the tool will detect that and will update only the A record (ipv4) of *example.tk*.

In order to add or update the subdomain *sub.example.tk*:
```
fdu record update $LOGIN $PASSWORD example.tk -n sub
```


### Advanced usage
If you want to update multiple (sub)domains you could call the tool for each domains.
Even better, you can create a configuration file.  
A configuration is a [YAML](https://en.wikipedia.org/wiki/YAML) file, which look like :
```YAML
login: yourlogin@somemail.domain
password: yourpassword

# list here the records you want to add/update
record:
  # the following will update both the A and AAAA records with your current ips (v4 and v6).
  # Note that if you don't have a ipv6 connection, the program'll detect it and will only update the A record (ipv4)
  - domain: test.tk

  # the following will update both your subdomain's A and AAAA records with your current ips (v4 and v6)
  - domain: test.tk
    name: mysubdomain

  # here's more advanced exemples

  # the following will update the AAAA record with a specified ipv6
  - domain: test2.tk
    name: # you can omit this line
    type: AAAA
    target: "fd2b:1c1b:3641:1cd8::" # note that you have to quote ipv6 addresses
    ttl: 24440

  # the following will update your subdomain's A record with your current ip (v4)
  - domain: test2.tk
    name: mysubdomain
    type: A
    target: auto # you can omit this line


  # you can omit the record type and give only ipv4 or ipv6 addresses.
  - domain: test2.tk
    name: ipv6sub
    target: "fd2b:1c1b:3641:1cd8::"

  - domain: test2.tk
    name: ipv4sub
    target: "64.64.64.64"
```

In order to use such configuration, you can use the following command :
```bash
fdu update /path/to/config
```

Where */path/to/config* can be either:
- A path to a file (default location is ```/etc/freenom.yml```)
- A http url (a raw secret [gist](https://gist.githubusercontent.com/maxisoft/1b979b64e4cf5157d58d/raw/freenom.yml) for instance)

## Schedule
In order to launch regularly an update, you can launch the tool with :
```bash
fdu process -c -i -r -t 3600 /path/to/config
```
Where the params are :  

| param           | description                                          |
|-----------------|------------------------------------------------------|
| -c              | cache the ip and update only if there is any changes |
| -i              | ignore errors when updating                          |
| -r              | renew the domains                          |
| -t              | time (in second) to wait between two updates         |
| /path/to/config | a path or a url to a configuration file              |



### Using systemd
For ease of use a systemd unit file is available along the source code.
- Save your configuration into ```/etc/freenom.yml```
- Copy the ```systemd/system/freenom-dns-updater.service``` into a valid systemd unit folder (```/usr/lib/systemd/system/``` for instance).  
- finally enable the service using
```
systemctl enable freenom-dns-updater
systemctl start freenom-dns-updater
```


### Using other Os / services manager
There's two straightforward choices :  
- Launch the previous ```fdu process``` command
- Schedule the ```fdu update``` command using cron, windows' scheduled task, ...

## Known issues
- The website [my.freenom.com](my.freenom.com) is not really stable (503/504 errors very often) => there's 3 retry on every request made by the tool but even with this it's common to face a remote server error   

## Docker image
[![](https://images.microbadger.com/badges/image/maxisoft/freenom-dns-updater.svg)](https://microbadger.com/images/maxisoft/freenom-dns-updater "")

If you want to run this tool in an "isolated" environment there's a docker image available at
[maxisoft/freenom-dns-updater](https://hub.docker.com/r/maxisoft/freenom-dns-updater/)

### Ipv6
Note that if you want to use the ipv6 functionality, you have to enable the [docker ipv6 stack](https://docs.docker.com/v1.5/articles/networking/#ipv6)

### Examples
- Update dns records using a gist config file :
```bash
docker run -it --rm maxisoft/freenom-dns-updater fdu update https://gist.githubusercontent.com/maxisoft/1b979b64e4cf5157d58d/raw/freenom.yml
```
- Run the tool in a background docker with a local config file :  
```bash
docker run -d --rm -v /path/to/config:/etc/freenom.yml maxisoft/freenom-dns-updater
```