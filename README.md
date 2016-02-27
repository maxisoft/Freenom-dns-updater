# Freenom dns updater
A tool to update [freenom](http://Freenom.com)'s dns records

[![Build Status](https://travis-ci.org/maxisoft/Freenom-dns-updater.svg?branch=master)](https://travis-ci.org/maxisoft/Freenom-dns-updater)
[![PyPI Version](https://img.shields.io/pypi/v/freenom-dns-updater.svg)](https://pypi.python.org/pypi/freenom-dns-updater)
[![PyPI](https://img.shields.io/pypi/l/freenom-dns-updater.svg)](https://pypi.python.org/pypi/freenom-dns-updater)

# Main Features
* Manage (add/update/remove) a domain's dns record with cli
* Automatic records updates according to ip (v4/v6) changes 

# Upcoming features
* Auto renew domains

## Installation
```bash
pip install freenom-dns-updater
```
## Usage

### Basic usage
Let's say you want to add/update your main A/AAAA domain records *exemple.tk* with your current ip (v4/v6).
Simply type : 
```
fdu record update $LOGIN $PASSWORD exemple.tk
```

Note that if you don't have an ipv6 access, the tool'll detect that and will update only the A record (ipv4) of *exemple.tk*.

In order to add/update the subdomain *sub.exemple.tk*:
```
fdu record update $LOGIN $PASSWORD exemple.tk -n sub
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
  # If you don't have an ipv6 connection, the program'll detect it and will only update the A record (ipv4)
  - domain: test.tk

  # the following will update both your subdomain's A and AAAA records with your current ips (v4 and v6)
  - domain: test.tk
    name: mysubdomain

  # here's more advanced exemples

  # the following will update the AAAA record with a specified ipv6
  - domain: test2.tk
    name: # you can omit this line
    type: AAAA
    target: "fd2b:1c1b:3641:1cd8::" # note that you has to quote ipv6 addresses
    ttl: 24440

  # the following will update the your subdomain's A record with your current ip (v4)
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

In order to use such configuration, you can use the following :
```bash
fdu update /path/to/config
```

Where /path/to/config can be either: 
- A path to a file (default location is ```/etc/freenom.yml```)
- A http url (a raw secret [gist](https://gist.githubusercontent.com/maxisoft/1b979b64e4cf5157d58d/raw/freenom.yml) for instance)



## Docker image
[![Docker layers](https://badge.imagelayers.io/maxisoft/freenom-dns-updater:latest.svg)](https://imagelayers.io/?images=maxisoft/freenom-dns-updater:latest)

If you want to run this in an isolated environment there's a docker image available at 
[maxisoft/freenom-dns-updater](https://hub.docker.com/r/maxisoft/freenom-dns-updater/)

### for armhf
There's also an image for armhf (raspberry pi for instance) available at 
[maxisoft/freenom-dns-updater-armhf](https://hub.docker.com/r/maxisoft/freenom-dns-updater-armhf)