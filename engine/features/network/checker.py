import socket
import logging

logger = logging.getLogger(__name__)


def check_tcp(host, port, timeout=5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def run_checks(competition):
    from features.network.models import ServiceDefinition, ServiceCheck

    services = list(ServiceDefinition.objects.filter(
        competition=competition
    ).select_related("machine_template"))
    teams = list(competition.teams.prefetch_related("vms__machine_template").all())
    results = []

    for service in services:
        for team in teams:
            vms = team.vms.filter(competition=competition)
            if service.machine_template:
                vms = vms.filter(machine_template=service.machine_template)

            target_ip = next((vm.ip_address for vm in vms if vm.ip_address), None)
            if not target_ip:
                continue

            is_up = check_tcp(target_ip, service.port)
            ServiceCheck.objects.create(service=service, team=team, is_up=is_up)
            results.append({"service": service.name, "team": team.name, "is_up": is_up})

    return results
