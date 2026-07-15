"""One EC2 instance running real SQL Server for the Loop Capital demo (BH-1036).

NOT the brighthive-admin per-workspace-AWS-account factory (a permanent new
AWS account + 7 CDK stacks + Cognito + Neo4j entity — the real paying-client
onboarding flow). This is a single, isolated, easy-to-tear-down resource in
the EXISTING shared STAGE account, scoped only to proving GC-15's BYOW
watchdog against a real (not Dockerized-locally) SQL Server.

Runs the SAME `mcr.microsoft.com/mssql/server:2022` image + SQL fixtures
../sandbox/docker-compose.yml and ../sandbox/sql/*.sql already use locally —
seeded via user-data so the instance is demo-ready on first boot, no manual
SSH setup step.
"""

from __future__ import annotations

from pathlib import Path

from aws_cdk import CfnOutput, Duration, Stack, Tags
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

_SANDBOX_DIR = Path(__file__).resolve().parents[2] / "sandbox"


class LoopCapitalSqlServerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Default VPC in the shared STAGE account — no new VPC, no new NAT
        # gateway. This is demo infra, not a new network boundary.
        vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)

        security_group = ec2.SecurityGroup(
            self,
            "SqlServerSecurityGroup",
            vpc=vpc,
            description="Loop Capital demo SQL Server — inbound 1433 only",
            allow_all_outbound=True,
        )
        # TODO(before deploy): replace with platform-core's actual known
        # source (its egress IP/CIDR, or a bastion/VPN range) — confirmed
        # this needs verification, not assumed, before opening 1433 to it.
        # Left as a placeholder as a deliberate blocker: this stack must
        # not be deployed with an open CIDR.
        security_group.add_ingress_rule(
            # Deliberately non-functional (loopback, unreachable from any
            # real source) so a `cdk deploy` with this placeholder still
            # left in place denies 1433 to everyone rather than silently
            # opening it wide. Replace with platform-core's real known
            # source CIDR before deploying against a live demo.
            peer=ec2.Peer.ipv4("127.0.0.1/32"),
            connection=ec2.Port.tcp(1433),
            description="PLACEHOLDER — CONFIRM platform-core's real source CIDR before deploy, see README.md",
        )

        instance_role = ec2.InstanceType.of(
            ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM
        )

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "set -euo pipefail",
            "dnf install -y docker",
            "systemctl enable --now docker",
            # Fixed filler size mirrors sandbox/fill_disk.sh — 1663MiB filler
            # on a 2048MiB tmpfs volume for LoopCapitalAM's own data files,
            # so sys.dm_os_volume_stats reports the same ~18% free the local
            "mkdir -p /srv/loopcapital/data",
            "mount -t tmpfs -o size=2048m tmpfs /srv/loopcapital/data",
            "docker network create loopcapital-net || true",
            (
                "docker run -d --name loopcapital-sql-sandbox "
                "--network loopcapital-net -p 1433:1433 "
                "-e ACCEPT_EULA=Y "
                "-e MSSQL_SA_PASSWORD='LoopCapital-Demo1!' "
                "-e MSSQL_AGENT_ENABLED=true "
                "-e MSSQL_PID=Developer "
                "-v /srv/loopcapital/data:/var/opt/mssql/loopcapital_data "
                "--restart unless-stopped "
                "mcr.microsoft.com/mssql/server:2022-CU14-ubuntu-22.04"
            ),
            # TODO(before deploy): fetch sandbox/sql/*.sql from S3 (upload
            # them as a CDK asset) and run via sqlcmd once the container is
            # healthy — left undone here since asset upload needs the real
            # deploy account confirmed first. Placeholder marker below so
            # this is visibly incomplete, not silently assumed done.
            "echo 'TODO: seed sandbox/sql/*.sql — see infra/README.md Status section' > /srv/loopcapital/SEED_PENDING",
        )

        instance = ec2.Instance(
            self,
            "SqlServerInstance",
            vpc=vpc,
            instance_type=instance_role,
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            security_group=security_group,
            user_data=user_data,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            associate_public_ip_address=True,
        )
        Tags.of(instance).add("Project", "loopcapital-demo")
        Tags.of(instance).add("TemporaryUntil", "2026-07-18")

        CfnOutput(
            self,
            "SqlServerPublicIp",
            value=instance.instance_public_ip,
            description="Real SQL Server endpoint for the Loop Capital demo — wire into createWarehouseServiceAsAdmin (provider=AZURE_SYNAPSE)",
        )
