import ipaddress
import logging
import yaml


logger = logging.getLogger("Configuration")

DEFAULT_EXTERNAL_PORTS = {
    'httpPort': 80,
    'httpsPort': 443,
    'mqttPort': 1883,
    'coapPort': 5684
}


class ConfigData:

    def __init__(self, config_file):
        self.config_data = {}
        self._parse_configurations(config_file)
        self._check_configuration()

    def _parse_configurations(self, config_file):

        logger.info("Parsing Configuration file")

        with open(config_file, "r") as f:
            try:
                self.config_data = yaml.load(f)
            except yaml.YAMLError as exc:
                logger.error(exc)

    def _check_configuration(self):

        logger.info("Checking configuration integrity")

        # Check namespace
        if 'namespace' not in self.config_data:
            logger.info("Setting namespace to default value: 'dojot'")
            self.config_data['namespace'] = 'dojot'

        # Check containers version
        if 'version' not in self.config_data:
            logger.info("Setting dojot version to default value: 'latest'")
            self.config_data['version'] = 'latest'

        if 'storage' not in self.config_data:
            logger.error("Storage configuration not found")
            exit(1)
        else:
            storage_data = self.config_data['storage']
            storage_type = storage_data.get('type', None)

            if storage_type == 'ceph':
                ceph_keys = ["cephMonitors", "cephAdminId",
                             "cephAdminKey", "cephUserId", "cephUserKey"]

                for ceph_param in ceph_keys:
                    if ceph_param not in storage_data.keys():
                        logger.error("Ceph storage configuration '%s'"
                                     " missing from file" % ceph_param)

            elif storage_type == 'gcp':

                if "gcpStorageType" not in storage_data.keys():
                    logger.warning("Parameter gcpStorageType not found, "
                                   "using default value: 'pd-standard'")
                    storage_data["gcpStorageType"] = "pd-standard"

            else:
                logger.error("Invalid storage type,"
                             " values supported: ['ceph', 'gcp']")

        if 'externalAccess' not in self.config_data:
            logger.error("externalAccess configuration not found")
            exit(1)
        else:
            external_data = self.config_data.get('externalAccess')
            external_type = external_data.get('type', None)

            if external_type == 'publicIP':
                ips_list = external_data.get('ips', None)

                if not ips_list:
                    logger.error("Missing External IPs List")
                    exit(1)

                if not isinstance(ips_list, list):
                    logger.error("The ips parameter must "
                                 "contain a list of external IPs")
                    exit(1)

                for ip_addr in ips_list:
                    try:
                        ipaddress.ip_address(ip_addr)
                    except ValueError:
                        logger.error("Ip address '%s' in external "
                                     "IPs list is invalid" % ip_addr)
                        exit(2)

            elif external_type == 'loadBalancer':
                # No special parameters for now
                pass
            else:
                logger.error("Invalid external access type,"
                             " values supported: ['publicIP, loadBalancer]")

            ports = external_data.get('ports', {})

            for port in DEFAULT_EXTERNAL_PORTS.items():
                if port[0] not in ports:
                    logger.info("Using default value %d for port %s" %
                                (port[1], port[0]))
                    ports.update([port])

    def get_config_data(self, param=None):

        if param:
            return self.config_data.get(param, None)
        else:
            return self.config_data
