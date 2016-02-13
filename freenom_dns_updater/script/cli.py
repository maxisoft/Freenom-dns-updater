#!/usr/bin/env python
import click
import pathlib
import freenom_dns_updater
import sys
import six
import requests

if six.PY2:
    try:
        from urlparse import urlparse
    except ImportError:
        raise
else:
    from urllib.parse import urlparse


@click.group()
@click.version_option('1.0')
@click.help_option('--help', '-h')
def cli():
    pass


@cli.command(help='''Update freenom's dns records according to the provided configuration file''')
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
        try:
            if rec.domain is None:
                click.secho("you don't own the domain \"{}\"".format(domain_name), fg='yellow', bold=True)
                if ignore_errors:
                    continue
                else:
                    sys.exit(7)
            freenom.add_record(rec, True)
        except Exception as e:
            if not ignore_errors:
                raise
            #TODO log e
            err_count += 1
        else:
            ok_count += 1
            
    if ok_count:
        if not err_count:
            click.echo('Successfully Updated {} record{}'.format(ok_count, "s" if ok_count > 1 else ""))
        else:
            click.echo('Updated {} record{}'.format(ok_count, "s" if ok_count > 1 else ""))
    else:
        click.secho('no record updated', fg='yellow', bold=True)

if __name__ == '__main__':
    cli()

