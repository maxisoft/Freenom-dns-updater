#!/usr/bin/env python
import click
import pathlib
import freenom_dns_updater
import sys

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
    config_path = pathlib.Path(config)
    if not config_path.is_file():
        click.secho('File "{}" not found.'.format(config_path), fg='red', bold=True)
        sys.exit(5)
    config = freenom_dns_updater.Config(str(config_path))
    records = config.records
    if not records:
        click.secho('There is no record configured', fg='yellow', bold=True)
    freenom = freenom_dns_updater.Freenom()
    if not freenom.login(config.login, config.password):
        click.secho('Unable to login with the given credential', fg='red', bold=True)
        sys.exit(6)

    domains = freenom.list_domains()
    domains_mapping = {d.name: d for d in domains}
    count = 0
    for rec in records:
        rec.domain = domains_mapping[rec.domain.name]
        try:
            freenom.add_record(rec, True)
        except Exception as e:
            if not ignore_errors:
                raise
            #TODO log e
        else:
            count += 1
    if count:
        click.echo('Updated {} record{}'.format(count, "s" if count > 1 else ""))
    else:
        click.secho('no record updated', fg='yellow', bold=True)

if __name__ == '__main__':
    cli()

