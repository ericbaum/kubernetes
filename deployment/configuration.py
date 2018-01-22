import logging
import yaml


logger = logging.getLogger("Configuration")


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
                ceph_keys = ["cephMonitors", "cephAdminId", "cephAdminKey", "cephUserId", "cephUserKey"]

                for ceph_param in ceph_keys:
                    if ceph_param not in storage_data.keys():
                        logger.error("Ceph storage configuration '%s' missing from file" % ceph_param)

            elif storage_type == 'gcp':

                if "gcpStorageType" not in storage_data.keys():
                    logger.warning("Parameter gcpStorageType not found, using default value: 'pd-standard'")
                    storage_data["gcpStorageType"] = "pd-standard"

            else:
                logger.error("Invalid storage type, values supported: ['ceph', 'gcp']")

    def get_config_data(self, param=None):

        if param:
            return self.config_data.get(param, None)
        else:
            return self.config_data
