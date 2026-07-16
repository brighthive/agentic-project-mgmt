#!/usr/bin/env python3
"""CDK entrypoint — one EC2 instance running real SQL Server for the Loop Capital demo.

NOT the brighthive-admin per-workspace-AWS-account provisioning factory. This
is a single, isolated, easy-to-tear-down resource in the EXISTING shared
STAGE account. See README.md before running `cdk deploy`.
"""

from __future__ import annotations

import aws_cdk as cdk

from loopcapital_sqlserver_ec2.stack import LoopCapitalSqlServerStack

app = cdk.App()

LoopCapitalSqlServerStack(
    app,
    "LoopCapitalSqlServerDemo",
    env=cdk.Environment(account="873769991712", region="us-east-1"),
    description="BH-1036: one EC2 instance running real SQL Server for the Loop Capital demo — see clients/trials/loopcapital/infra/README.md",
    tags={
        "Project": "loopcapital-demo",
        "Owner": "drchinca",
        "TemporaryUntil": "2026-07-18",
    },
)

app.synth()
