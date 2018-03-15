import logging
import kubernetes

from kubernetes.client.rest import ApiException

logger = logging.getLogger("Kubernetes")


class KubeClient:

    def __init__(self):
        self._prepare_kube()

    def _prepare_kube(self):
        kubernetes.config.load_kube_config()
        self.v1 = kubernetes.client.CoreV1Api()
        self.storageV1Beta1 = kubernetes.client.StorageV1beta1Api()
        self.extensionsV1Beta1 = kubernetes.client.ExtensionsV1beta1Api()
        self.authorizationV1Beta1 = kubernetes.client.RbacAuthorizationV1beta1Api()
        self.appsV1Beta1 = kubernetes.client.AppsV1beta1Api()
        self.batchV1 = kubernetes.client.BatchV1Api()

    def create_namespace(self, namespace):
        try:
            res = self.v1.read_namespace(namespace)
            if res.metadata.name == namespace:
                logger.info("Namespace '%s' already exists!" % namespace)
        except ApiException as error:
            if error.status == 404:
                logger.info("Namespace '%s' not found, creating..." % namespace)
                self.v1.create_namespace({'metadata': {'name': namespace}})
        finally:
            logger.info("Namespace '%s' is ready" % namespace)

    def create_secret(self, name, secret_type, namespace, data):

        body = {
            'metadata': {
                'name': name
            },
            'type': secret_type,
            'data': data
        }

        try:
            res = self.v1.read_namespaced_secret(name, namespace)
            if res.metadata.name == name:
                logger.info("Updating existing secret with name '%s'" % name)
                self.v1.replace_namespaced_secret(name, namespace, body)
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating secret %s at namespace '%s'" % (name, namespace))
                self.v1.create_namespaced_secret(namespace, body)
            else:
                logger.error(error)
                exit(1)

    def create_storage_class(self, name, data):

        body = {
            'metadata': {
                'name': name
            }
        }
        body.update(data)

        try:
            res = self.storageV1Beta1.read_storage_class(name)
            if res.metadata.name == name:
                logger.info("Storage class '%s' already exists, nothing done" % name)
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating storage class named '%s'" % name)
                self.storageV1Beta1.create_storage_class(body)
            else:
                logger.error(error)
                exit(1)

    def create_deployment(self, name, namespace, spec):

        body = {
            'metadata': {
                'name': name
            },
            'spec': spec
        }

        try:
            res = self.extensionsV1Beta1.read_namespaced_deployment(name, namespace)
            if res.metadata.name == name:
                logger.info("Updating existing deployment with name '%s' on namespace '%s'" %
                            (name, namespace))
                self.extensionsV1Beta1.replace_namespaced_deployment(name, namespace, body)
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating deployment '%s' at namespace '%s'" % (name, namespace))
                self.extensionsV1Beta1.create_namespaced_deployment(namespace, body)
            else:
                logger.error(error)
                exit(1)

    def create_service_account(self, name, namespace):

        body = {
            'metadata': {
                'name': name
            }
        }

        try:
            res = self.v1.read_namespaced_service_account(name, namespace)
            if res.metadata.name == name:
                logger.info("Service Account '%s' already exists at namespace '%s', nothing done" %
                            (name, namespace))
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating service account named '%s' at namespace '%s'" %
                            (name, namespace))
                self.v1.create_namespaced_service_account(namespace, body)
            else:
                logger.error(error)
                exit(1)

    def create_cluster_role(self, name, rules):

        body = {
            'metadata': {
                'name': name
            },
            'rules': rules
        }

        try:
            res = self.authorizationV1Beta1.read_cluster_role(name)
            if res.metadata.name == name:
                logger.info("Updating existing cluster role with name '%s'" % name)
                self.authorizationV1Beta1.replace_cluster_role(name, body)
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating cluster role '%s'" % name)
                self.authorizationV1Beta1.create_cluster_role(body)
            else:
                logger.error(error)
                exit(1)

    def create_cluster_role_binding(self, name, subjects, cluster_role):

        body = {
            'metadata': {
                'name': name
            },
            'subjects': subjects,
            'roleRef': {
                "kind": "ClusterRole",
                "name": cluster_role,
                "apiGroup": "rbac.authorization.k8s.io"
            }
        }

        try:
            res = self.authorizationV1Beta1.read_cluster_role_binding(name)
            if res.metadata.name == name:
                logger.info("Updating existing cluster role binding with name '%s'" % name)
                self.authorizationV1Beta1.replace_cluster_role_binding(name, body)
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating cluster role binding '%s'" % name)
                self.authorizationV1Beta1.create_cluster_role_binding(body)
            else:
                logger.error(error)
                exit(1)

    def create_service(self, name, namespace, spec):

        body = {
            'metadata': {
                'name': name
            },
            'spec': spec
        }

        try:
            res = self.v1.read_namespaced_service(name, namespace)

            body['metadata']['resourceVersion'] = res.metadata.resource_version

            cluster_ip = getattr(res.spec, 'cluster_ip', None)

            if cluster_ip:
                body['spec']['clusterIP'] = cluster_ip

            if res.metadata.name == name:
                logger.info("Updating existing service with name '%s'" % name)
                self.v1.replace_namespaced_service(name, namespace, body)
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating service '%s' on namespace '%s'" % (name, namespace))
                self.v1.create_namespaced_service(namespace, body)
            else:
                logger.error(error)
                exit(1)

    def create_stateful_set(self, name, namespace, spec):

        body = {
            'metadata': {
                'name': name
            },
            'spec': spec
        }

        try:
            self.appsV1Beta1.read_namespaced_stateful_set(name, namespace)

            # TODO: Check the correct way of scaling updating a statefulSet deployment

            logger.warn("It is not possible to update or scale the stateful"
                        " set %s via this script at the moment" % name)

        except ApiException as error:
            if error.status == 404:
                logger.info("Creating stateful set '%s' on namespace '%s'" % (name, namespace))
                self.appsV1Beta1.create_namespaced_stateful_set(namespace, body)
            else:
                logger.error(error)
                exit(1)

    def create_role(self, name, namespace, rules):

        body = {
            'metadata': {
                'name': name
            },
            'rules': rules
        }

        try:
            res = self.authorizationV1Beta1.read_namespaced_role(name, namespace)
            if res.metadata.name == name:
                logger.info("Updating existing role with "
                            "name '%s' on namespace '%s'" % (name, namespace))
                self.authorizationV1Beta1.replace_namespaced_role(name, namespace, body)
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating role '%s' on namespace '%s'" % (name, namespace))
                self.authorizationV1Beta1.create_namespaced_role(namespace, body)
            else:
                logger.error(error)
                exit(1)

    def create_role_binding(self, name, namespace, subjects, role):

        for subject in subjects:
            subject['namespace'] = namespace

        body = {
            'metadata': {
                'name': name
            },
            'subjects': subjects,
            'roleRef': {
                "kind": "Role",
                "name": role,
                "apiGroup": "rbac.authorization.k8s.io"
            }
        }

        try:
            res = self.authorizationV1Beta1.read_namespaced_role_binding(name, namespace)
            if res.metadata.name == name:
                logger.info("Updating existing role binding with "
                            "name '%s' on namespace '%s'" % (name, namespace))
                self.authorizationV1Beta1.replace_namespaced_role_binding(name, namespace, body)
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating role binding '%s' on namespace '%s'" % (name, namespace))
                self.authorizationV1Beta1.create_namespaced_role_binding(namespace, body)
            else:
                logger.error(error)
                exit(1)

    def start_job(self, name, namespace, spec):

        body = {
            'metadata': {
                'name': name
            },
            'spec': spec
        }

        try:
            res = self.batchV1.read_namespaced_job(name, namespace)
            if res.metadata.name == name:
                logger.info("Updating existing job with "
                            "name '%s' on namespace '%s'" % (name, namespace))
                self.batchV1.patch_namespaced_job(name, namespace, body)
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating job '%s' on namespace '%s'" % (name, namespace))
                self.batchV1.create_namespaced_job(namespace, body)
            else:
                logger.error(error)
                exit(1)

    def create_config_map(self, name, namespace, data):

        body = {
            'metadata': {
                'name': name
            },
            'data': data
        }

        try:
            res = self.v1.read_namespaced_config_map(name, namespace)
            if res.metadata.name == name:
                logger.info("Updating existing configmap with "
                            "name '%s' on namespace '%s'" % (name, namespace))
                self.v1.replace_namespaced_config_map(name, namespace, body)
        except ApiException as error:
            if error.status == 404:
                logger.info("Creating configmap '%s' on namespace '%s'" % (name, namespace))
                self.v1.create_namespaced_config_map(namespace, body)
            else:
                logger.error(error)
                exit(1)
