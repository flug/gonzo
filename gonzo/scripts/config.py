#!/usr/bin/env python
""" Set the account and region for subsequent gonzo commands
"""

from gonzo.config import local_state, global_state, config_proxy
from gonzo.exceptions import ConfigurationError


def set_cloud(cloud):
    if not cloud:
        return

    global_state['cloud'] = cloud

    # set the default region
    cloud_config = config_proxy.CLOUD
    try:
        supported_regions = cloud_config['REGIONS']
    except KeyError:
        raise ConfigurationError(
            'Cloud "{}" has no REGIONS setting'.format(cloud))

    try:
        default_region = supported_regions[0]
        set_region(default_region)
    except IndexError:
        raise ConfigurationError(
            'Cloud "{}" has no supported regions'.format(cloud))


def available_regions():
    try:
        cloud_config = config_proxy.CLOUD
        return cloud_config['REGIONS']
    except (ConfigurationError, KeyError):
        return None


def set_region(region):
    if not region:
        return

    global_state['region'] = region


def set_project(project):
    """ Sets the project name for the local git repository. This will not write
        to the global / system git environments.
    """

    if not project:
        return

    local_state['project'] = project


def print_config():
    print 'cloud:', global_state.get('cloud')
    print 'region:', global_state.get('region')
    print 'project:', local_state.get('project')


def main(args):
    try:
        set_cloud(args.cloud)
        set_region(args.region)
        set_project(args.project)
    except ConfigurationError as ex:
        print ex
        print

    print_config()


def init_parser(parser):
    parser.add_argument(
        '--cloud', dest='cloud', choices=config_proxy.CLOUDS.keys(),
        help='set the active cloud configuration'
    )
    parser.add_argument(
        '--region', dest='region',
        choices=available_regions(), help='set the region'
    )
    parser.add_argument(
        '--project', dest='project',
        help='set the project name to the local git config'
    )
