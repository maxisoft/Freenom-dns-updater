#!/usr/bin/env python
import datetime
import json
import pathlib
import platform
import pprint
import sys
import time
import traceback
from multiprocessing import Process

import click
import requests
import six
import yaml

import freenom_dns_updater
from freenom_dns_updater.get_my_ip import *

is_windows = any(platform.win32_ver())

if six.PY2:
    try:
        from urlparse import urlparse
    except ImportError:
        raise
else:
    from urllib.parse import urlparse

_format_map = {
    None: lambda x: x,
    'TEXT': lambda x: pprint.pformat(x),
    'JSON': lambda x: json.dumps(x, sort_keys=True),
    'YAML': lambda x: yaml.safe_dump(x)
}


def format_data(data, formater='TEXT'):
    if isinstance(data, (list, tuple, set)):
        data = [format_data(x, None) for x in data]
    elif isinstance(data, dict):
        data = {format_data(k, None): format_data(v, None) for k, v in six.iteritems(data)}
    elif isinstance(data, freenom_dns_updater.Domain):
        data = format_data({'name': data.name, 'state': data.state,
                            'type': data.type, 'id': data.id,
                            'register': data.register_date,
                            'expire': data.expire_date}, None)
    elif isinstance(data, freenom_dns_updater.Record):
        data = format_data({'name': data.name, 'type': data.type.name,
                            'ttl': data.ttl, 'target': data.target}, None)
    elif isinstance(data, datetime.date):
        data = str(data)
    return _format_map[formater](data)


click_record_type = click.Choice([t.name for t in freenom_dns_updater.RecordType])


@click.group()
@click.version_option('1.0')
@click.help_option('--help', '-h')
def cli():
    pass


@cli.group(help='''Manage records''')
@click.help_option('--help', '-h')
def record():
    pass


@cli.group(help='''Manage domain''')
@click.help_option('--help', '-h')
def domain():
    pass


@record.command('ls', help='List records of a specified domain')
@click.argument('user')
@click.argument('password')
@click.argument('domain')
@click.option('-f', '--format', help='Output format', default='TEXT', type=click.Choice(("TEXT", "JSON", "YAML")))
@click.help_option('--help', '-h')
def record_ls(user, password, domain, format):
    freenom = freenom_dns_updater.Freenom()
    if not freenom.login(user, password):
        click.secho('Unable to login with the given credential', fg='red', bold=True)
        sys.exit(6)
    # search the domain
    for d in freenom.list_domains():
        if d.name == domain:
            domain = d
            break
    if not isinstance(domain, freenom_dns_updater.Domain):
        click.secho("You don't own the domain \"{}\"".format(domain), fg='yellow', bold=True)
        sys.exit(7)
    records = freenom.list_records(domain)
    click.echo(format_data(records, format))


@record.command('add', help='Add a record into a specified domain')
@click.argument('user')
@click.argument('password')
@click.argument('domain')
@click.option('-n', '--name', help='Record name. Used as subdomain in A records')
@click.option('-t', '--type', help='Record type. A or AAAA for instance', type=click_record_type)
@click.option('-a', '--target', help='Record target. An ip address for A record')
@click.option('-l', '--ttl', help='Record time to live.', type=click.INT)
@click.option('-u', '--update', help='Update existing record', default=True, type=click.BOOL)
@click.help_option('--help', '-h')
def record_add(user, password, domain, name, type, target, ttl, update):
    d = {'login': user, 'password': password, 'record': []}
    record = {'domain': domain}
    if name:
        record['name'] = name
    if type:
        record['type'] = type
    if target:
        record['target'] = target
    if ttl:
        record['ttl'] = ttl
    d['record'].append(record)
    config = freenom_dns_updater.Config(d)

    ok_count, err_count = record_action(lambda freenom, rec: freenom.add_record(rec, update), config, False)

    if ok_count:
        click.echo('Record successfully added{}.'.format("/updated" if update else ""))
    else:
        click.secho('No record updated', fg='yellow', bold=True)


@record.command('update', help='Update a record')
@click.argument('user')
@click.argument('password')
@click.argument('domain')
@click.option('-n', '--name', help='Record name. Used as subdomain in A records')
@click.option('-t', '--type', help='Record type. A or AAAA for instance', type=click_record_type)
@click.option('-a', '--target', help='Record target. An ip address for A records')
@click.option('-l', '--ttl', help='Record time to live.', type=click.INT)
@click.help_option('--help', '-h')
def record_update(user, password, domain, name, type, target, ttl):
    d = {'login': user, 'password': password, 'record': []}
    record = {'domain': domain}
    if name:
        record['name'] = name
    if type:
        record['type'] = type
    if target:
        record['target'] = target
    if ttl:
        record['ttl'] = ttl
    d['record'].append(record)
    config = freenom_dns_updater.Config(d)

    ok_count, err_count = record_action(lambda freenom, rec: freenom.add_record(rec, True), config, False)

    if ok_count:
        click.echo('Record successfully added/updated.')
    else:
        click.secho('No record updated', fg='yellow', bold=True)


@record.command('rm', help='Remove a record from a specified domain')
@click.argument('user')
@click.argument('password')
@click.argument('domain')
@click.option('-n', '--name', help='Record name. Used as subdomain in A records')
@click.option('-t', '--type', help='Record type. A or AAAA for instance', type=click_record_type)
@click.option('-a', '--target', help='Record target. An ip address for A record')
@click.option('-l', '--ttl', help='Record time to live.', type=click.INT)
@click.option('-u', '--update', help='Update existing record', default=True, type=click.BOOL)
@click.help_option('--help', '-h')
def record_rm(user, password, domain, name, type, target, ttl, update):
    d = {'login': user, 'password': password, 'record': []}
    record = {'domain': domain}
    if name:
        record['name'] = name
    if type:
        record['type'] = type
    if target:
        record['target'] = target
    if ttl:
        record['ttl'] = ttl
    d['record'].append(record)
    config = freenom_dns_updater.Config(d)

    ok_count, err_count = record_action(lambda freenom, rec: freenom.remove_record(rec), config, False)

    if ok_count:
        click.echo('Record successfully removed.')
    else:
        click.secho('No record removed', fg='yellow', bold=True)


def _update(config, ignore_errors):
    config = freenom_dns_updater.Config(config_src(config))

    ok_count, err_count = record_action(lambda freenom, rec: freenom.add_record(rec, True), config, ignore_errors)

    if ok_count:
        if not err_count:
            click.echo('Successfully Updated {} record{}'.format(ok_count, "s" if ok_count > 1 else ""))
        else:
            click.echo('Updated {} record{}'.format(ok_count, "s" if ok_count > 1 else ""))
    else:
        click.secho('No record updated', fg='yellow', bold=True)


def config_src(config):
    url = urlparse(config)
    if url.scheme in ('file', 'http', 'https'):
        ret = requests.get(config, stream=True).raw
    else:  # except a file
        ret = pathlib.Path(config)
        if not ret.is_file():
            click.secho('File "{}" not found.'.format(ret), fg='red', bold=True)
            sys.exit(5)
    return ret


@cli.command('update', help='''Update records according to a configuration file''')
@click.argument('config', default='freenom.yml')
@click.option('-i', '--ignore-errors', default=False, help='ignore errors when updating', is_flag=True)
@click.help_option('--help', '-h')
def update(config, ignore_errors):
    return _update(config, ignore_errors)


def record_action(action, config, ignore_errors):
    records = config.records
    if not records:
        click.secho('There is no record configured', fg='yellow', bold=True)
    freenom = freenom_dns_updater.Freenom()
    if not freenom.login(config.login, config.password):
        click.secho('Unable to login with the given credential', fg='red', bold=True)
        sys.exit(6)
    domains = freenom.list_domains()
    domains_mapping = {d.name: d for d in domains}
    ok_count = 0
    err_count = 0
    for rec in records:
        domain_name = rec.domain.name
        rec.domain = domains_mapping.get(domain_name)
        if rec.domain is None:
            click.secho("You don't own the domain \"{}\"".format(domain_name), fg='yellow', bold=True)
            if ignore_errors:
                continue
            else:
                sys.exit(7)
        try:
            action(freenom, rec)
        except Exception as e:
            if not ignore_errors:
                raise
            # TODO log e
            err_count += 1
        else:
            ok_count += 1
    return ok_count, err_count


@domain.command('ls', help='List domains')
@click.argument('user')
@click.argument('password')
@click.option('-f', '--format', help='Output format', default='TEXT', type=click.Choice(("TEXT", "JSON", "YAML")))
@click.help_option('--help', '-h')
def domain_ls(user, password, format):
    freenom = freenom_dns_updater.Freenom()
    if not freenom.login(user, password):
        click.secho('Unable to login with the given credential', fg='red', bold=True)
        sys.exit(6)
    # search the domain
    domains = freenom.list_domains()
    click.echo(format_data(domains, format))


@cli.command(help='''Regularly update records according to a configuration file''')
@click.argument('config', default='freenom.yml' if is_windows else '/etc/freenom.yml')
@click.option('-t', '--period', default=60 * 60, help='update period in second', type=click.IntRange(10, 2592000))
@click.option('-i', '--ignore-errors', help='ignore errors when updating', is_flag=True)
@click.option('-c', '--cache', help='cache ip and update only if there is any changes', is_flag=True)
@click.help_option('--help', '-h')
def process(config, period, ignore_errors, cache):
    config_src(config)
    ipv4 = ''
    ipv6 = ''
    while 1:
        try:
            new_ipv4 = ''
            new_ipv6 = ''
            update_needed = True
            if cache:
                try:
                    new_ipv4 = str(get_my_ipv4())
                except:
                    pass
                try:
                    new_ipv6 = str(get_my_ipv6())
                except:
                    pass
                update_needed = ipv4 != new_ipv4 or ipv6 != new_ipv6

            if update_needed:
                p = Process(target=_update, args=(config, ignore_errors))
                p.start()
                p.join(500)
                if cache:
                    ipv4 = new_ipv4
                    ipv6 = new_ipv6
        except:
            traceback.print_exc(file=sys.stderr)
        finally:
            time.sleep(period)


if __name__ == '__main__':
    cli()
