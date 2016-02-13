#!/usr/bin/env python
import click
import pathlib

import datetime

import freenom_dns_updater
import sys
import six
import requests
import yaml
import json
import pprint

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


@record.command(help='List records of a specified domain')
@click.argument('user')
@click.argument('password')
@click.argument('domain')
@click.option('-f', '--format', help='Output format', default='TEXT', type=click.Choice(("TEXT", "JSON", "YAML")))
@click.help_option('--help', '-h')
def ls(user, password, domain, format):
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


@record.command(help='Add a record into a specified domain')
@click.argument('user')
@click.argument('password')
@click.argument('domain')
@click.option('-n', '--name', help='Record name. Used as subdomain in A records')
@click.option('-t', '--type', help='Record type. A or AAAA for instance', type=click_record_type)
@click.option('-a', '--target', help='Record target. An ip address for A record')
@click.option('-l', '--ttl', help='Record time to live.', type=click.INT)
@click.option('-u', '--update', help='Update existing record', default=True, type=click.BOOL)
@click.help_option('--help', '-h')
def add(user, password, domain, name, type, target, ttl, update):
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
        click.secho('no record updated', fg='yellow', bold=True)


@record.command(help='Update a record')
@click.argument('user')
@click.argument('password')
@click.argument('domain')
@click.option('-n', '--name', help='Record name. Used as subdomain in A records')
@click.option('-t', '--type', help='Record type. A or AAAA for instance', type=click_record_type)
@click.option('-a', '--target', help='Record target. An ip address for A records')
@click.option('-l', '--ttl', help='Record time to live.', type=click.INT)
@click.help_option('--help', '-h')
def update(user, password, domain, name, type, target, ttl, update):
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
        click.echo('Record successfully added{}.'.format("/updated" if update else ""))
    else:
        click.secho('no record updated', fg='yellow', bold=True)


@record.command(help='Remove a record from a specified domain')
@click.argument('user')
@click.argument('password')
@click.argument('domain')
@click.option('-n', '--name', help='Record name. Used as subdomain in A records')
@click.option('-t', '--type', help='Record type. A or AAAA for instance', type=click_record_type)
@click.option('-a', '--target', help='Record target. An ip address for A record')
@click.option('-l', '--ttl', help='Record time to live.', type=click.INT)
@click.option('-u', '--update', help='Update existing record', default=True, type=click.BOOL)
@click.help_option('--help', '-h')
def rm(user, password, domain, name, type, target, ttl, update):
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
        click.secho('no record removed', fg='yellow', bold=True)


@cli.command(help='''Update records according to a configuration file''')
@click.argument('config', default='freenom.yml')
@click.option('-i', '--ignore-errors', default=False, help='ignore errors when updating', is_flag=True)
@click.help_option('--help', '-h')
def update(config, ignore_errors):
    url = urlparse(config)
    if url.scheme in ('file', 'http', 'https'):
        config_path = requests.get(config, stream=True).raw
    else:  # except a file
        config_path = pathlib.Path(config)
        if not config_path.is_file():
            click.secho('File "{}" not found.'.format(config_path), fg='red', bold=True)
            sys.exit(5)
    config = freenom_dns_updater.Config(config_path)

    ok_count, err_count = record_action(lambda freenom, rec: freenom.add_record(rec, True), config, ignore_errors)

    if ok_count:
        if not err_count:
            click.echo('Successfully Updated {} record{}'.format(ok_count, "s" if ok_count > 1 else ""))
        else:
            click.echo('Updated {} record{}'.format(ok_count, "s" if ok_count > 1 else ""))
    else:
        click.secho('no record updated', fg='yellow', bold=True)


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
            click.secho("you don't own the domain \"{}\"".format(domain_name), fg='yellow', bold=True)
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


@domain.command(help='List domains')
@click.argument('user')
@click.argument('password')
@click.option('-f', '--format', help='Output format', default='TEXT', type=click.Choice(("TEXT", "JSON", "YAML")))
@click.help_option('--help', '-h')
def ls(user, password, format):
    freenom = freenom_dns_updater.Freenom()
    if not freenom.login(user, password):
        click.secho('Unable to login with the given credential', fg='red', bold=True)
        sys.exit(6)
    # search the domain
    domains = freenom.list_domains()
    click.echo(format_data(domains, format))


if __name__ == '__main__':
    cli()
