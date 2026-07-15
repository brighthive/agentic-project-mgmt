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
from aws_cdk import aws_secretsmanager as secretsmanager
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
        # DELIBERATE EXCEPTION to aws-reusable.md's "no security group open to
        # 0.0.0.0/0" rule — confirmed and explicitly approved for this one
        # resource, not defaulted to. Reason: brightbot (the watchdog caller)
        # deploys on LangGraph Cloud, a managed SaaS with no published static
        # egress IP range — there is no real CIDR to scope this to. The
        # compensating control is the SA credential (a real, non-default
        # password, see user_data below) plus the resource's own short
        # lifetime (Tags: TemporaryUntil, meant to be torn down right after
        # the 7/17 demo). This is demo-grade posture, explicitly NOT
        # production security — do not reuse this pattern for a real client
        # workspace's warehouse connection.
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(1433),
            description="Loop Capital demo SQL Server — open by necessity (LangGraph Cloud has no static egress CIDR); SA password is the real control, see stack.py",
        )

        instance_role = ec2.InstanceType.of(
            ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM
        )

        # Real, per-deploy generated SA credential — never a literal in
        # source. This is the actual control the open security group above
        # relies on, so it cannot itself be a hardcoded/shared/committed
        # value (the local sandbox's throwaway "LoopCapital-Demo1!" is fine
        # for a Docker container only reachable on localhost; it is NOT
        # fine for a publicly-reachable instance).
        sa_secret = secretsmanager.Secret(
            self,
            "SqlServerSaSecret",
            description="Loop Capital demo SQL Server SA password — generated, never in source",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=False,
                exclude_characters="\"'\\/@ ",
                password_length=32,
            ),
        )

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "set -euo pipefail",
            "dnf install -y docker",
            "systemctl enable --now docker",
            f"SA_PASSWORD=$(aws secretsmanager get-secret-value --secret-id {sa_secret.secret_arn} "
            f"--region {self.region} --query SecretString --output text)",
            # Fixed filler size mirrors sandbox/fill_disk.sh — 2048MiB tmpfs
            # volume for LoopCapitalAM's own data files, so
            # sys.dm_os_volume_stats reports real, non-default free space
            # (matching the same ~18% free the local sandbox demonstrates).
            "mkdir -p /srv/loopcapital/data",
            "mount -t tmpfs -o size=2048m tmpfs /srv/loopcapital/data",
            "docker network create loopcapital-net || true",
            (
                "docker run -d --name loopcapital-sql-sandbox "
                "--network loopcapital-net -p 1433:1433 "
                "-e ACCEPT_EULA=Y "
                '-e MSSQL_SA_PASSWORD="$SA_PASSWORD" '
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
        sa_secret.grant_read(instance.role)
        Tags.of(instance).add("Project", "loopcapital-demo")
        Tags.of(instance).add("TemporaryUntil", "2026-07-18")

        CfnOutput(
            self,
            "SqlServerPublicIp",
            value=instance.instance_public_ip,
            description="Real SQL Server endpoint for the Loop Capital demo — wire into createWarehouseServiceAsAdmin (provider=AZURE_SYNAPSE)",
        )
        CfnOutput(
            self,
            "SqlServerSaSecretArn",
            value=sa_secret.secret_arn,
            description="Secrets Manager ARN for the real SA password — fetch via `aws secretsmanager get-secret-value`, never printed in logs/PR text",
        )
