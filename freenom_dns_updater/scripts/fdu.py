#!/usr/bin/env python
import datetime
import json
import pathlib
import platform
import pprint
import subprocess  # nosec
import sys
import time
import traceback
import warnings
from multiprocessing import Process
from typing import Callable, Optional
from urllib.parse import urlparse

import click
import requests
import six
import yaml

import freenom_dns_updater
from freenom_dns_updater import Config, Domain, Freenom, Record
from freenom_dns_updater.exception import UpdateError
from freenom_dns_updater.get_my_ip import get_my_ipv4, get_my_ipv6

is_windows = any(platform.win32_ver())


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
        click.secho(f"You don't own the domain \"{domain}\"", fg='yellow', bold=True)
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
        click.echo(f'Record successfully added{"/updated" if update else ""}.')
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

    ok_count = 0
    try:
        ok_count, err_count = record_action(lambda freenom, rec: freenom.add_record(rec, True), config, False)

        if ok_count:
            click.echo('Record successfully added/updated')
    except UpdateError as update_error:
        if any(msg != 'There were no changes' for msg in update_error.msgs):
            click.echo(f"Update errors: {update_error.msgs}", err=True)
    except Exception as e:
        click.echo(f"Error while updating: {e}", err=True)

    if not ok_count:
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

    ok_count = 0
    try:
        ok_count, err_count = record_action(lambda freenom, rec: freenom.add_record(rec, True), config, ignore_errors)

        if not err_count:
            click.echo(f'Successfully Updated {ok_count} record{"s" if ok_count > 1 else ""}')
        else:
            click.echo(f'Updated {ok_count} record{"s" if ok_count > 1 else ""}')
    except UpdateError as update_error:
        if any(msg != 'There were no changes' for msg in update_error.msgs):
            click.echo(f"Update errors: {update_error.msgs}", err=True)
    except Exception as e:
        click.echo(f"Error while updating: {e}", err=True)

    if not ok_count:
        click.secho('No record updated', fg='yellow', bold=True)


def _renew(config, ignore_errors):
    config = freenom_dns_updater.Config(config_src(config))

    ok_count = 0

    def action(freenom: Freenom, domain: Domain):
        if freenom.need_renew(domain):
            if not freenom.renew(domain):
                raise Exception(f"unable to renew {domain.name}")

    try:
        ok_count, err_count = domain_action(action, config, ignore_errors)

        if not err_count:
            click.echo(f'Successfully Updated {ok_count} domain{"s" if ok_count > 1 else ""}')
        else:
            click.echo(f'Updated {ok_count} domain{"s" if ok_count > 1 else ""}')
    except UpdateError as update_error:
        if any(msg != 'There were no changes' for msg in update_error.msgs):
            click.echo(f"Update errors: {update_error.msgs}", err=True)
    except Exception as e:
        click.echo(f"Error while updating: {e}", err=True)

    if not ok_count:
        click.secho('No record updated', fg='yellow', bold=True)


def config_src(config):
    url = urlparse(config)
    if url.scheme in ('file', 'http', 'https'):
        ret = requests.get(config, stream=True).raw
    else:  # except a file
        ret = pathlib.Path(config)
        if not ret.is_file():
            click.secho(f'File "{ret}" not found.', fg='red', bold=True)
            sys.exit(5)
    return ret


@cli.command('update', help='''Update records according to a configuration file''')
@click.argument('config', default='freenom.yml')
@click.option('-i', '--ignore-errors', default=False, help='ignore errors when updating', is_flag=True)
@click.help_option('--help', '-h')
def update(config, ignore_errors):
    return _update(config, ignore_errors)


def record_action(action: Callable[[Freenom, Record], None], config: Config, ignore_errors: bool):
    records = config.records
    if not records:
        click.secho('There is no record configured', fg='yellow', bold=True)
    freenom = Freenom()
    if not freenom.login(config.login, config.password):
        click.secho('Unable to login with the given credential', fg='red', bold=True)
        sys.exit(6)
    domains = freenom.list_domains()
    domains_mapping = {d.name: d for d in domains}
    ok_count = 0
    err_count = 0
    for rec in records:
        domain_name = rec.domain.name
        rec_domain = domains_mapping.get(domain_name)
        if rec_domain is None:
            click.secho(f"You don't own the domain \"{domain_name}\"", fg='yellow', bold=True)
            if ignore_errors:
                continue
            else:
                sys.exit(7)
        rec.domain = rec_domain
        try:
            action(freenom, rec)
        except Exception:
            if not ignore_errors:
                raise
            warnings.warn(traceback.format_exc())
            err_count += 1
        else:
            ok_count += 1
    return ok_count, err_count


def domain_action(action: Callable[[Freenom, Domain], None], config: Config, ignore_errors: bool):
    records = config.records
    if not records:
        click.secho('There is no record configured', fg='yellow', bold=True)
    freenom = Freenom()
    if not freenom.login(config.login, config.password):
        click.secho('Unable to login with the given credential', fg='red', bold=True)
        sys.exit(6)
    domains = freenom.list_domains()
    domains_mapping = {d.name: d for d in domains}
    ok_count = 0
    err_count = 0
    to_process = set()
    for rec in records:
        domain_name = rec.domain.name
        rec_domain = domains_mapping.get(domain_name)
        if rec_domain is None:
            click.secho(f"You don't own the domain \"{domain_name}\"", fg='yellow', bold=True)
            if ignore_errors:
                continue
            else:
                sys.exit(7)
        rec.domain = rec_domain
        to_process.add(rec_domain)

    for domain in to_process:
        try:
            action(freenom, domain)
        except Exception:
            if not ignore_errors:
                raise
            warnings.warn(traceback.format_exc())
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
    freenom = Freenom()
    if not freenom.login(user, password):
        click.secho('Unable to login with the given credential', fg='red', bold=True)
        sys.exit(6)
    domains = freenom.list_domains()
    click.echo(format_data(domains, format))


@domain.command('forward', help='Forward a Domain or print the current forward domain.')
@click.argument('user')
@click.argument('password')
@click.argument('domain')
@click.option('-u', '--url', help="The forward url")
@click.option('-m', '--mode', help='How to point to the domain either "301_redirect" or "cloak"',
              default="cloak", type=click.Choice(("301_redirect", "cloak")))
@click.help_option('--help', '-h')
def domain_forward(user, password, domain, url, mode):
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
        click.secho(f"You don't own the domain \"{domain}\"", fg='yellow', bold=True)
        sys.exit(7)
    try:
        cururl, curmode = freenom.current_url_forward(domain.id)
    except Exception:
        cururl = None
        curmode = None

    click.echo("Current: " + domain.name + " --" + curmode + "--> " + cururl)

    if url is None:
        return
    if cururl == url and curmode == mode:
        click.echo("Forward already set")
        return

    if freenom.change_url_forward(domain.id, url, mode):
        click.echo("New set: " + domain.name + " --" + mode + "--> " + url)
    else:
        click.echo("Something went wrong!")


@domain.command('renew', help='Renew a domain for X months')
@click.argument('user')
@click.argument('password')
@click.argument('domain')
@click.option('-p', '--period', help='number of months', type=click.IntRange(1, 12))
@click.help_option('--help', '-h')
def domain_renew(user, password, domain, period):
    freenom = Freenom()
    if not freenom.login(user, password):
        click.secho('Unable to login with the given credential', fg='red', bold=True)
        sys.exit(6)
    # search the domain
    domains = freenom.list_domains()
    domain_obj = next((d for d in domains if d.name.upper() == domain.upper()), None)
    if domain_obj is None:
        click.secho(f'Unable to find domain with name "{domain}"', fg='red', bold=True)
        sys.exit(6)
    if not freenom.need_renew(domain_obj):
        click.secho(f'No need to renew domain "{domain_obj.name}"', fg='yellow', bold=True)
        sys.exit(7)
    if freenom.renew(domain_obj, period):
        click.echo(f'Renewed "{domain_obj.name}" for {period} months')
    else:
        click.secho(f'Unable to renew domain "{domain_obj.name}"', fg='red', bold=True)
        sys.exit(6)


@cli.command(help='''Regularly update records according to a configuration file''')
@click.argument('config', default='freenom.yml' if is_windows else '/etc/freenom.yml')
@click.option('-t', '--period', default=60 * 60, help='update period in second', type=click.IntRange(10, 2592000))
@click.option('-i', '--ignore-errors', help='ignore errors when updating', is_flag=True)
@click.option('-c', '--cache', help='cache ip and update only if there is any changes', is_flag=True)
@click.option('-r', '--renew', help='renew domain if needed', is_flag=True)
@click.help_option('--help', '-h')
def process(config, period, ignore_errors, cache, renew):
    config_src(config)
    ipv4 = ''
    ipv6 = ''
    last_renew_date: Optional[datetime.date] = None
    while 1:
        try:
            new_ipv4 = ''
            new_ipv6 = ''
            update_needed = True
            if cache:
                try:
                    new_ipv4 = str(get_my_ipv4())
                except Exception:
                    warnings.warn(traceback.format_exc())
                try:
                    new_ipv6 = str(get_my_ipv6())
                except OSError:
                    pass
                except Exception:
                    warnings.warn(traceback.format_exc())
                update_needed = ipv4 != new_ipv4 or ipv6 != new_ipv6

            def start_and_wait_sub_process(target) -> Optional[int]:
                p = Process(target=target, args=(config, ignore_errors))
                p.start()
                exit_code = None
                try:
                    p.join(500)
                    exit_code = p.exitcode
                except subprocess.TimeoutExpired:
                    p.kill()
                    raise
                finally:
                    p.close()
                return exit_code

            if update_needed:
                start_and_wait_sub_process(_update)
                if cache:
                    ipv4 = new_ipv4
                    ipv6 = new_ipv6

            if renew and last_renew_date != datetime.date.today():
                if start_and_wait_sub_process(_renew) == 0:
                    last_renew_date = datetime.date.today()
        except Exception:
            traceback.print_exc(file=sys.stderr)
        finally:
            time.sleep(period)


if __name__ == '__main__':
    cli()
