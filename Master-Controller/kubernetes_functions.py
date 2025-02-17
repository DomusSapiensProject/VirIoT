import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pprint import pprint

# This variable set the node anti affinity to deploy the resources in the default zone, composed of the node without label "viriot-zone"
zone_affinity = {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [{'matchExpressions': [{'key': 'viriot-zone', 'operator': 'DoesNotExist'}]}, {'matchExpressions': [{'key': 'viriot-zone', 'operator': 'In', 'values': ['default']}]}]}}}

def create_deployment(namespace, image_name, name, container_port = None, environment=None):
    api_instance_apps = kubernetes.client.AppsV1Api()
    pod_spec = client.V1PodSpec(containers=[client.V1Container(name=name,
                                                               image=image_name,
                                                               ports=[client.V1ContainerPort(container_port= container_port)] if container_port is not None else None,
                                                               # ports=[client.V1ContainerPort(container_port=container_port)],
                                                               env=environment
                                                               )
                                            ]
                                )

    pod_template = client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(labels={"broker": str(image_name.split("/")[-1])}),
                                            spec=pod_spec
                                            )

    statefulset_spec = client.V1StatefulSetSpec(replicas=1,
                                                service_name="svc-%s" % str(image_name.split("/")[-1]),
                                                selector=client.V1LabelSelector(match_labels={"broker": str(image_name.split("/")[-1])}),
                                                template=pod_template
                                                )

    statefulset_body = client.V1StatefulSet(api_version="apps/v1",
                                            kind="StatefulSet",
                                            metadata=client.V1ObjectMeta(name=name),
                                            spec=statefulset_spec
                                            )

    try:
        return api_instance_apps.create_namespaced_deployment(namespace, statefulset_body, pretty="true")
    except Exception as err:
        return err

def create_deployment_from_yaml(namespace, body):
    api_instance_apps = kubernetes.client.AppsV1Api()

    try:
        return api_instance_apps.create_namespaced_deployment(namespace, body, pretty="true")

    except Exception as err:
        return err

def delete_deployment(namespace, name):
    api_instance_apps = kubernetes.client.AppsV1Api()

    try:
        return True, api_instance_apps.delete_namespaced_deployment(name=name, namespace=namespace, pretty="true")
    except Exception as err:
        return False, err



def create_service(namespace, image_name, container_port, target_container_port, service_node_port, name):
    api_instance_core = kubernetes.client.CoreV1Api()
    service_body = client.V1Service(api_version="v1",
                                    kind="Service",
                                    metadata=client.V1ObjectMeta(name="svc-%s" % str(name)),
                                    spec=client.V1ServiceSpec(selector={"flavour": str(image_name.split("/")[-1])},
                                                              ports=[client.V1ServicePort(port=container_port,
                                                                                          target_port=target_container_port,
                                                                                          node_port=service_node_port
                                                                                          )
                                                                     ],
                                                              type="NodePort"
                                                              )
                                    )
    try:
        return api_instance_core.create_namespaced_service(namespace, body=service_body)
    except Exception as err:
        return err

def create_service_from_yaml(namespace, body):
    api_instance_core = kubernetes.client.CoreV1Api()

    try:
        return api_instance_core.create_namespaced_service(namespace, body=body)
    except Exception as err:
        return err

def delete_service(namespace, name):
    api_instance_core = kubernetes.client.CoreV1Api()

    try:
        return True, api_instance_core.delete_namespaced_service(name=name, namespace=namespace, pretty="true")
    except Exception as err:
        return False, err


def dictSearch(key, dictionary):
    for k, v in dictionary.items():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in dictSearch(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in dictSearch(key, d):
                    yield result

# prec_env contains the list of env variables
# found in the yaml file for a container
def convert_env(env, prec_env = []):
    new_env = prec_env
    for key in env:
        new_env.append({"name": key, "value": str(env[key])})

    return tuple(new_env)

# prec_hosts contains the list of hostAliases
# found in the yaml file for a deployment
def convert_hostAliases(hosts, prec_hosts = []):
    new_hosts = prec_hosts
    for host in hosts:
        new_hosts.append({"ip": host["cluster_ip"], "hostnames": [host["prec"]]})

    return tuple(new_hosts)


def discover_mongodb_nodeport_debug(mongodb_svc_name, working_namespace):
    api_instance_core = kubernetes.client.CoreV1Api()
    try:
        api_response = api_instance_core.read_namespaced_service_status(mongodb_svc_name, working_namespace)
    except ApiException as e:
        # print("Exception when calling AppsV1Api->read_namespaced_deployment_status: %s\n" % e)
        api_response = e
    if api_response.status == 404:
        return False
    else:
        return api_response.spec.ports[0].node_port


def discover_mqtt_nodeport_debug(mqtt_svc_name, working_namespace):
    api_instance_core = kubernetes.client.CoreV1Api()
    try:
        api_response = api_instance_core.read_namespaced_service_status(mqtt_svc_name, working_namespace)
    except ApiException as e:
        # print("Exception when calling AppsV1Api->read_namespaced_deployment_status: %s\n" % e)
        api_response = e
    if api_response.status == 404:
        return False
    else:
        return api_response.spec.ports[0].node_port

def discover_mqtt_serviceIP_debug(mqtt_svc_name, working_namespace):
    api_instance_core = kubernetes.client.CoreV1Api()
    try:
        api_response = api_instance_core.read_namespaced_service_status(mqtt_svc_name, working_namespace)
    except ApiException as e:
        # print("Exception when calling AppsV1Api->read_namespaced_deployment_status: %s\n" % e)
        api_response = e
    if api_response.status == 404:
        return False
    else:
        return api_response.spec.cluster_ip

def list_available_node_zone():
    api_instance = kubernetes.client.CoreV1Api()
    zones = {}
    try:
        api_response = api_instance.list_node()
        for node in api_response.items:
            if "viriot-zone" in node.metadata.labels.keys():
                if "viriot-gw" in node.metadata.labels.keys():
                    zones[node.metadata.labels["viriot-zone"]] = node.metadata.labels["viriot-gw"]
                else:
                    # Alredy have an entry {"viriot-zone": "gw"}
                    if node.metadata.labels["viriot-zone"] not in zones.keys():
                        zones[node.metadata.labels["viriot-zone"]] = ""
        return zones

    except ApiException as e:
        # print("Exception when calling AppsV1Api->read_namespaced_deployment_status: %s\n" % e)
        print("Error: in list_available_node_zone", e)
        return False


def get_master_node_ip():
    api_instance = kubernetes.client.CoreV1Api()
    try:
        api_response = api_instance.list_node()
        for node in api_response.items:
            if "node-role.kubernetes.io/master" in node.metadata.labels.keys():
                # print(node.metadata)
                address = node.status.addresses[0].address
                return address
        return False
    except ApiException as e:
        # print("Exception when calling AppsV1Api->read_namespaced_deployment_status: %s\n" % e)
        print("Error: in get_master_node_ip", e)
        return False
