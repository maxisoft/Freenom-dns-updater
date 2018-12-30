#!/usr/bin/env python3
import pathlib

def gen():
    base_path = pathlib.Path(__file__).parent
    armhf_path = base_path / 'armhf'
    armhf_path.mkdir(exist_ok=True)
    with (armhf_path / 'Dockerfile').open('w') as out:
        for line in (base_path / 'Dockerfile').open():
            line = line.replace('python:3-alpine', 'multiarch/alpine:armhf-v3.3')
            if line.startswith('#') and 'Placeholder for armhf' in line:
                out.write('''
RUN apk add --no-cache git && \\
    apk add --no-cache python3 && \\
    apk add --no-cache --virtual=build-dependencies wget ca-certificates && \\
    wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3 && \\
    apk del build-dependencies\n''')
            else:
                out.write(line)

if __name__ == '__main__':
    gen()
