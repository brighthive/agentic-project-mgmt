"""Bedrock Knowledge Base for the Loop Capital demo's enterprise context (BH-1036).

NOT the brighthive-admin per-workspace-AWS-account factory (a permanent new
AWS account + 7 CDK stacks + Cognito + Neo4j entity - the real paying-client
onboarding flow, confirmed destructive to an EXISTING workspace since
create_workspace.py runs delete_workspace() before create_workspace()). This
is a small, additive stack in the EXISTING shared STAGE account, scoped only
to giving brightbot's `query_knowledge_base` tool something real to retrieve
for the Loop Capital demo - investment mandates, compliance policy, and
reference exports, already generated in ../../sandbox/knowledge_base/.

Scaled down from brighthive-data-workspace-cdk's BedrockUnstructuredDataStack:
no Bedrock Data Automation Project, no Step Function ingestion pipeline. Those
exist to extract text from raw video/audio/complex documents before they can
be embedded. The Loop Capital KB docs are already plain PDFs/CSVs - Bedrock
Knowledge Base's own S3 data source ingestion (StartIngestionJob) extracts and
chunks these natively, no pre-processing stage required.
"""

from __future__ import annotations

from aws_cdk import (
    CfnOutput,
    CfnResource,
    RemovalPolicy,
    Stack,
    Tags,
    aws_bedrock as bedrock,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds,
    aws_s3 as s3,
    custom_resources as cr,
)
from constructs import Construct

_WORKSPACE_UUID = "e3fc0917-03a6-4ac6-aad4-ac265329bfb9"  # Loop Capital, STAGE


class LoopCapitalKnowledgeBaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        account_id = self.account
        region = self.region
        embedding_model_arn = (
            f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0"
        )
        kb_database_name = "postgres"
        kb_schema_name = "bedrock_integration"
        kb_table_name = f"{kb_schema_name}.bedrock_kb"

        docs_bucket = s3.Bucket(
            self,
            "LoopCapitalKbDocsBucket",
            bucket_name=f"loopcapital-kb-docs-{account_id}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Default VPC in the shared STAGE account - same pattern as the SQL
        # Server EC2 stack, no new VPC/NAT for demo infra.
        vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)

        # Default VPC in this shared STAGE account has no private subnet group
        # (same constraint the SQL Server EC2 stack works within) - Aurora goes
        # in the public subnets, VPC-CIDR-scoped ingress only (no public access),
        # matching the EC2 stack's existing precedent for this account/VPC.
        aurora_sg = ec2.SecurityGroup(
            self,
            "LoopCapitalKbVectorStoreSg",
            vpc=vpc,
            description="Loop Capital demo KB - Aurora pgvector store, VPC-internal only",
            allow_all_outbound=False,
        )
        aurora_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL access from within VPC",
        )

        aurora_cluster = rds.DatabaseCluster(
            self,
            "LoopCapitalKbAurora",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.of("16.11", "16")
            ),
            writer=rds.ClusterInstance.serverless_v2("writer", publicly_accessible=False),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[aurora_sg],
            enable_data_api=True,
            credentials=rds.Credentials.from_generated_secret(
                "bedrock_kb_admin",
                secret_name=f"loopcapital-kb-aurora-credentials-{account_id}",
            ),
            serverless_v2_min_capacity=0.5,
            serverless_v2_max_capacity=2,
            cluster_identifier=f"loopcapital-kb-aurora-{account_id}",
            removal_policy=RemovalPolicy.DESTROY,
        )

        rds_data_policy = cr.AwsCustomResourcePolicy.from_statements(
            [
                iam.PolicyStatement(
                    actions=["rds-data:ExecuteStatement"],
                    resources=[aurora_cluster.cluster_arn],
                ),
                iam.PolicyStatement(
                    actions=["secretsmanager:GetSecretValue"],
                    resources=[aurora_cluster.secret.secret_arn],
                ),
            ]
        )

        def rds_call(logical_id: str, sql: str, prev=None):
            resource = cr.AwsCustomResource(
                self,
                logical_id,
                on_create=cr.AwsSdkCall(
                    service="RDSDataService",
                    action="executeStatement",
                    parameters={
                        "resourceArn": aurora_cluster.cluster_arn,
                        "secretArn": aurora_cluster.secret.secret_arn,
                        "database": kb_database_name,
                        "sql": sql,
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(f"{logical_id}-{account_id}"),
                ),
                policy=rds_data_policy,
            )
            resource.node.add_dependency(aurora_cluster)
            if prev:
                resource.node.add_dependency(prev)
            return resource

        step1 = rds_call("EnablePgVectorExtension", "CREATE EXTENSION IF NOT EXISTS vector;")
        step2 = rds_call(
            "CreateBedrockSchema", f"CREATE SCHEMA IF NOT EXISTS {kb_schema_name};", prev=step1
        )
        step3 = rds_call(
            "CreateBedrockKbTable",
            (
                f"CREATE TABLE IF NOT EXISTS {kb_table_name} ("
                "id UUID PRIMARY KEY, "
                "embedding vector(1024), "
                "chunks TEXT, "
                "metadata JSON, "
                "custom_metadata JSONB"
                ");"
            ),
            prev=step2,
        )
        step4 = rds_call(
            "CreateEmbeddingHnswIndex",
            f"CREATE INDEX IF NOT EXISTS idx_kb_embedding ON {kb_table_name} "
            "USING hnsw (embedding vector_cosine_ops);",
            prev=step3,
        )
        step5 = rds_call(
            "CreateChunksGinIndex",
            f"CREATE INDEX IF NOT EXISTS idx_kb_chunks ON {kb_table_name} "
            "USING gin (to_tsvector('simple', chunks));",
            prev=step4,
        )
        create_embeddings_table = rds_call(
            "CreateCustomMetadataGinIndex",
            f"CREATE INDEX IF NOT EXISTS idx_kb_custom_metadata ON {kb_table_name} "
            "USING gin (custom_metadata);",
            prev=step5,
        )

        kb_role = iam.Role(
            self,
            "LoopCapitalKbRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            role_name=f"loopcapital-kb-role-{account_id}",
        )
        kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:ListBucket"],
                resources=[docs_bucket.bucket_arn, f"{docs_bucket.bucket_arn}/*"],
            )
        )
        kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:Retrieve"],
                resources=[embedding_model_arn],
            )
        )
        kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "rds-data:BatchExecuteStatement",
                    "rds-data:ExecuteStatement",
                    "rds:DescribeDBClusters",
                ],
                resources=[aurora_cluster.cluster_arn],
            )
        )
        kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[aurora_cluster.secret.secret_arn],
            )
        )

        # CfnKnowledgeBase in aws-cdk-lib doesn't expose StorageConfigurationProperty
        # yet — same CfnResource-with-raw-properties workaround as the reference
        # stack (bedrock_unstructured_data_stack.py) uses.
        knowledge_base = CfnResource(
            self,
            "LoopCapitalKnowledgeBase",
            type="AWS::Bedrock::KnowledgeBase",
            properties={
                "Name": f"loopcapital-{account_id}-kb",
                "Description": "Loop Capital demo - investment mandates, compliance policy, client onboarding, reference exports",
                "RoleArn": kb_role.role_arn,
                "KnowledgeBaseConfiguration": {
                    "Type": "VECTOR",
                    "VectorKnowledgeBaseConfiguration": {"EmbeddingModelArn": embedding_model_arn},
                },
                "StorageConfiguration": {
                    "Type": "RDS",
                    "RdsConfiguration": {
                        "ResourceArn": aurora_cluster.cluster_arn,
                        "CredentialsSecretArn": aurora_cluster.secret.secret_arn,
                        "DatabaseName": kb_database_name,
                        "TableName": kb_table_name,
                        "FieldMapping": {
                            "VectorField": "embedding",
                            "TextField": "chunks",
                            "MetadataField": "metadata",
                            "PrimaryKeyField": "id",
                            "CustomMetadataField": "custom_metadata",
                        },
                    },
                },
            },
        )
        knowledge_base.node.add_dependency(create_embeddings_table)

        data_source = bedrock.CfnDataSource(
            self,
            "LoopCapitalKbDataSource",
            name=f"loopcapital-{account_id}-kb-datasource",
            knowledge_base_id=knowledge_base.ref,
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type="S3",
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=docs_bucket.bucket_arn,
                ),
            ),
        )
        data_source.node.add_dependency(docs_bucket)

        # brightbot's query_knowledge_base tool assumes this role via STS before
        # every KB query (brightbot/tools/aws/knowledge_base.py:_assume_role).
        # Verified via `aws iam get-user --user-name brightagent-aws` against
        # both profiles: brightagent-aws lives IN this STAGE account
        # (873769991712), not a separate platform/MAIN account - this is a
        # same-account trust, not cross-account, since Loop Capital has no
        # dedicated AWS account of its own.
        brightagent_kb_role = iam.Role(
            self,
            "LoopCapitalBrightAgentKbAccessRole",
            assumed_by=iam.ArnPrincipal(f"arn:aws:iam::{account_id}:user/brightagent-aws"),
            role_name=f"loopcapital-brightagent-kb-access-role-{account_id}",
            description="Allows brightagent-aws to query the Loop Capital demo Knowledge Base",
        )
        brightagent_kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:Retrieve",
                ],
                resources=[knowledge_base.get_att("KnowledgeBaseArn").to_string()],
            )
        )

        # Bedrock's managed reranker (brightbot's query_knowledge_base uses it
        # for retrieval precision) needs its own grant, separate from the KB
        # access above: bedrock:Rerank doesn't support resource-level ARN
        # scoping (must be "*"), and the reranker is a different foundation
        # model than the KB's own embedding model. Confirmed live against this
        # role that neither is covered by the grant above.
        #
        # This exact 3-statement block is duplicated in brighthive-data-
        # workspace-cdk's general BedrockUnstructuredDataStack construct
        # (brighthive_data_cdk/bedrock_unstructured_data_stack.py) since this
        # trial stack isn't an instance of that construct — keep both in sync
        # if the required action list ever changes.
        rerank_model_arn = f"arn:aws:bedrock:{region}::foundation-model/cohere.rerank-v3-5:0"
        brightagent_kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:Rerank"],
                resources=["*"],
            )
        )
        brightagent_kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=[rerank_model_arn],
            )
        )
        # Cohere Rerank is a third-party model; Bedrock auto-subscribes via AWS
        # Marketplace on first invoke, which requires these actions on the
        # caller's role. Without them the subscription attempt fails and Rerank
        # returns 403 even with bedrock:Rerank/InvokeModel already granted.
        brightagent_kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "aws-marketplace:ViewSubscriptions",
                    "aws-marketplace:Subscribe",
                    "aws-marketplace:Unsubscribe",
                ],
                resources=["*"],
            )
        )

        Tags.of(self).add("Project", "loopcapital-demo")
        Tags.of(self).add("TemporaryUntil", "2026-07-18")

        CfnOutput(self, "DocsBucketName", value=docs_bucket.bucket_name)
        CfnOutput(
            self,
            "KnowledgeBaseId",
            value=knowledge_base.ref,
            description="Write into workspace_secret_store/e3fc0917-.../services.knowledge_base.knowledge_base_id",
        )
        CfnOutput(
            self,
            "KnowledgeBaseArn",
            value=knowledge_base.get_att("KnowledgeBaseArn").to_string(),
        )
        CfnOutput(self, "DataSourceId", value=data_source.attr_data_source_id)
        CfnOutput(
            self,
            "BrightAgentKbAccessRoleArn",
            value=brightagent_kb_role.role_arn,
            description="Write into workspace_secret_store/e3fc0917-.../services.knowledge_base.brightagent_kb_role_arn",
        )
