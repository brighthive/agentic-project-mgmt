#!/usr/bin/env python3
"""CDK entrypoint — Loop Capital demo infra: SQL Server EC2 + Bedrock Knowledge Base.

NOT the brighthive-admin per-workspace-AWS-account provisioning factory. Both
stacks are single, isolated, easy-to-tear-down resources in the EXISTING
shared STAGE account. See README.md before running `cdk deploy`.
"""

from __future__ import annotations

import aws_cdk as cdk

from loopcapital_knowledge_base.stack import LoopCapitalKnowledgeBaseStack
from loopcapital_sqlserver_ec2.stack import LoopCapitalSqlServerStack

app = cdk.App()

_ENV = cdk.Environment(account="873769991712", region="us-east-1")
_TAGS = {
    "Project": "loopcapital-demo",
    "Owner": "drchinca",
    "TemporaryUntil": "2026-07-18",
}

LoopCapitalSqlServerStack(
    app,
    "LoopCapitalSqlServerDemo",
    env=_ENV,
    description="BH-1036: one EC2 instance running real SQL Server for the Loop Capital demo — see clients/trials/loopcapital/infra/README.md",
    tags=_TAGS,
)

LoopCapitalKnowledgeBaseStack(
    app,
    "LoopCapitalKnowledgeBaseDemo",
    env=_ENV,
    description="BH-1036: Bedrock Knowledge Base for Loop Capital demo enterprise context — see clients/trials/loopcapital/infra/README.md",
    tags=_TAGS,
)

app.synth()
