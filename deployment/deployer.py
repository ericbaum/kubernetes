import logging
import base64
import yaml

from .kube import KubeClient

logger = logging.getLogger("Deployer")


class KubeDeployer:

    def __init__(self, conf):
        self.config = conf
        self.kube_client = KubeClient()

    def deploy_rbd(self, namespace):

        with open('manifests/STORAGE/CEPH/rbd-provisioner.yaml', 'r') as rbd_model:

            for rbd_data in yaml.load_all(rbd_model):

                if rbd_data["kind"] == "Deployment":
                    spec = rbd_data["spec"]
                    name = rbd_data["metadata"]["name"]
                    rbd_namespace = rbd_data["metadata"]["namespace"]
                    self.kube_client.create_deployment(name, rbd_namespace, spec)
                elif rbd_data["kind"] == "ServiceAccount":
                    name = rbd_data["metadata"]["name"]
                    sa_namespace = rbd_data["metadata"]["namespace"]
                    if sa_namespace != 'kube-system':
                        sa_namespace = namespace
                    self.kube_client.create_service_account(name, sa_namespace)
                elif rbd_data["kind"] == "ClusterRole":
                    name = rbd_data["metadata"]["name"]
                    rules = rbd_data["rules"]
                    self.kube_client.create_cluster_role(name, rules)
                elif rbd_data["kind"] == "ClusterRoleBinding":
                    name = rbd_data["metadata"]["name"]
                    subjects = rbd_data["subjects"]
                    cluster_role = rbd_data["roleRef"]["name"]

                    for subject in subjects:
                        if subject['namespace'] != 'kube-system':
                            subject['namespace'] = namespace

                    self.kube_client.create_cluster_role_binding(name, subjects, cluster_role)
                else:
                    logger.warning("Found unexpected object on RBD model file!")

    def configure_storage(self, namespace):
        storage = self.config.get_config_data('storage')

        if storage['type'] == 'ceph':

            ceph_monitors = storage['cephMonitors']
            admin_id = storage['cephAdminId']
            admin_key = storage['cephAdminKey']
            user_id = storage['cephUserId']
            user_key = storage['cephUserKey']
            user_pool = storage['cephPoolName']

            self.kube_client.create_secret('ceph-secret-admin', 'kubernetes.io/rbd',
                                           'kube-system', {'key': base64.b64encode(admin_key.encode()).decode()})
            self.kube_client.create_secret('ceph-secret-user', 'kubernetes.io/rbd',
                                           namespace, {'key': base64.b64encode(user_key.encode()).decode()})

            with open('manifests/STORAGE/CEPH/dojot-storage-class.yaml', 'r') as st_class:
                st_data = yaml.load(st_class)

                name = st_data['metadata']['name']
                provisioner = st_data['provisioner']
                parameters = st_data['parameters']

                parameters['monitors'] = str(ceph_monitors).strip("[]").replace("'", "").replace(" ", "")
                parameters['userId'] = user_id
                parameters['adminId'] = admin_id
                parameters['pool'] = user_pool

                self.kube_client.create_storage_class(name, {'provisioner': provisioner,
                                                             'parameters': parameters})

            self.deploy_rbd(namespace)

        elif storage['type'] == 'gcp':

            gcp_storage_type = storage['gcpStorageType']

            with open('manifests/STORAGE/GCP/dojot-storage-class.yaml', 'r') as st_class:
                st_data = yaml.load(st_class)

                name = st_data['metadata']['name']
                provisioner = st_data['provisioner']
                parameters = st_data['parameters']

                parameters['type'] = gcp_storage_type
                self.kube_client.create_storage_class(name, {'provisioner': provisioner,
                                                             'parameters': parameters})

    def deploy(self):
        logger.info("Starting deployment")

        namespace = self.config.get_config_data('namespace')

        self.kube_client.create_namespace(namespace)

        self.configure_storage(namespace)

        logger.info("Dojot was successfully deployed!")
