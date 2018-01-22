#!python3

import argparse
import logging
import sys

from deployment.configuration import ConfigData
from deployment.deployer import KubeDeployer

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("Main")


def parse_arguments():

    logger.info("Parsing Input Arguments")
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", dest='config_file', action='store', default='config.yaml',
                        help="Path to the configuration file for the deployment")

    return parser.parse_args()


def main():

    args = parse_arguments()
    conf = ConfigData(args.config_file)
    deployer = KubeDeployer(conf)

    deployer.deploy()


if __name__ == '__main__':
    main()
