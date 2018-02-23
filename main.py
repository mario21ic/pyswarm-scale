#!/usr/bin/env python3
# Usage: python main.py action monit myservice 2 5
# Example: python main.py services|monit <service> <min> <max>|list|scale_up <service>|scale_down <service>

import time
import platform
import logging
import os
import sys

import docker


docker_client = docker.from_env()
# docker_api = docker.APIClient(base_url='unix://var/run/docker.sock')
logging.basicConfig(level=logging.INFO, format="%(asctime)s " + platform.node() + ": %(message)s")


def main(action="services"):
    logging.info("========================")

    # List services with mode replicated
    if action == "services":
        logging.info("###### Services ######")
        services = docker_client.services.list(filters={"mode": 'replicated'})
        logging.info("ID\t\t\t\tNAME\t\tREPLICAS\tIMAGE\t\tPORTS\t\tLABELS")
        for service in services:
            # logging.info("Service attrs: " + str(service.attrs))

            ports = []
            if "Ports" in service.attrs['Endpoint']:
                for ingress in service.attrs['Endpoint']['Ports']:
                    ports.append(
                        ingress['Protocol'] + "/" + str(ingress['PublishedPort']) + ":" + str(ingress['TargetPort']))

            labels = []
            for k, v in service.attrs['Spec']['Labels'].items():
                labels.append(k + "=" + v)

            logging.info("%s\t%s\t\t%s\t%s\t%s\t%s" % (
                service.attrs['ID'],
                service.name[:7],
                service.attrs['Spec']['Mode']['Replicated']['Replicas'],
                service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split("@")[0],
                ",".join(ports),
                ",".join(labels),
            ))
        return

    # Monit a service
    if action == "monit":
        logging.info("###### Monit ######")
        services = docker_client.services.list()
        service_name = sys.argv[2]
        for service in services:
            if service.name == service_name:
                try:
                    labels = service.attrs['Spec']['Labels']
                    labels['pyscale'] = "true"
                    labels['pyscale_min'] = sys.argv[3]
                    labels['pyscale_max'] = sys.argv[4]
                    service.update(
                        labels=labels
                    )
                    logging.info("Service %s to monit with min=%s and max=%s" %
                                 (service_name, labels['pyscale_min'], labels['pyscale_max']))
                except Exception as e:
                    logging.error("Monit Error: " + str(e))
        return

    # List services to monit
    if action == "list":
        logging.info("###### Services ######")
        services = docker_client.services.list(filters={"label": "pyscale=true"})
        logging.info("ID\t\t\t\tNAME\t\tREP\tMIN/MAX\tIMAGE\t\tPORTS")
        for service in services:
            # logging.info("Service attrs: " + str(service.attrs))
            ports = []
            if "Ports" in service.attrs['Endpoint']:
                for ingress in service.attrs['Endpoint']['Ports']:
                    ports.append(
                        ingress['Protocol'] + "/" + str(ingress['PublishedPort']) + ":" + str(
                            ingress['TargetPort']))

            labels = []
            for k, v in service.attrs['Spec']['Labels'].items():
                labels.append(k + "=" + v)

            logging.info("%s\t%s\t\t%s\t%s\t%s\t%s" % (
                service.attrs['ID'],
                service.name[:7],
                service.attrs['Spec']['Mode']['Replicated']['Replicas'],
                service.attrs['Spec']['Labels']['pyscale_min'] + "/" + service.attrs['Spec']['Labels']['pyscale_max'],
                service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split("@")[0],
                ",".join(ports)
            ))
        return

    # Scale up a service
    if action == "scale_up":
        logging.info("###### Scale up ######")
        services = docker_client.services.list()
        service_name = sys.argv[2]
        for service in services:
            if service.name == service_name:
                try:
                    replicas = service.attrs['Spec']['Mode']['Replicated']['Replicas']
                    labels = service.attrs['Spec']['Labels']
                    replicas_new = replicas + 1
                    if replicas_new <= int(labels['pyscale_max']):
                        service.update(
                            mode={'Replicated': {
                                'Replicas': replicas_new
                            }}
                        )
                        logging.info("Scale is to %s " % replicas_new)
                    else:
                        logging.warn("Scale already is to max (%s) " % labels['pyscale_max'])
                except Exception as e:
                    logging.error("Scale up Error: " + str(e))
        return

    # Scale down a service
    if action == "scale_down":
        logging.info("###### Scale down ######")
        services = docker_client.services.list()
        service_name = sys.argv[2]
        for service in services:
            if service.name == service_name:
                try:
                    replicas = service.attrs['Spec']['Mode']['Replicated']['Replicas']
                    labels = service.attrs['Spec']['Labels']
                    replicas_new = replicas - 1
                    if replicas_new >= int(labels['pyscale_min']):
                        service.update(
                            mode={'Replicated': {
                                'Replicas': replicas_new
                            }}
                        )
                        logging.info("Scale is to %s " % replicas_new)
                    else:
                        logging.warn("Scale already is to min (%s) " % labels['pyscale_min'])
                except Exception as e:
                    logging.error("Scale up Error: " + str(e))
        return


if __name__ == "__main__":
    main(sys.argv[1])
