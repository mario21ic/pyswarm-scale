#!/usr/bin/env python3
# Usage: python main.py action
# Example: python main.py services|monit|list|up|down

import time
import platform
import logging
import os
import sys

import boto3
import docker


docker_client = docker.from_env()
docker_api = docker.APIClient(base_url='unix://var/run/docker.sock')
logging.basicConfig(level=logging.INFO, format="%(asctime)s " + platform.node() + ": %(message)s")


def main(action=""):
    logging.info("========================")

    if action == "services":
        logging.info("###### Services ######")
        services = docker_client.services.list()
        logging.info("ID\t\t\t\tNAME\t\tMODE\tIMAGE\t\tPORTS\t\tLABELS")
        for service in services:
            # logging.info("Service attrs: " + str(service.attrs))

            mode = ""
            for mod in service.attrs['Spec']['Mode'].keys():
                mode = mod

            replicas = 0
            if mode == "Replicated":
                replicas = service.attrs['Spec']['Mode']['Replicated']['Replicas']

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
                mode[:6],
                service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split("@")[0],
                ",".join(ports),
                ",".join(labels),
            ))
        return


if __name__ == "__main__":
    main(sys.argv[1])
