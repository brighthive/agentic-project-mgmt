---
title: "AWS to Azure Network Connectivity for Synapse Integration"
epic: "BH-171"
author: "drchinca"
status: "Draft"
created: "2026-04-09"
generates: "tickets"
tags: [aws, azure, networking, synapse, cross-cloud, vpn, security]
related:
  specs: ["azure-synapse-full-integration.md"]
  pocs: []
  features: []
---

# AWS to Azure Network Connectivity for Synapse Integration

## Problem

BrightHive runs entirely on AWS (us-east-1). Azure Synapse workspaces are the first cross-cloud dependency. Today, all connectivity uses public endpoints with TLS. As we move from BYOW read-only (Phase 1) to ingestion pipelines that push data from S3/Glue into customer Synapse instances (Phase 2), we need a clear network connectivity strategy that balances security, cost, and operational complexity for a four-person engineering team.

## Current Situation

- **AWS**: VPC in us-east-1 with public/private subnets. Glue jobs, Step Functions, Lambdas run inside VPC.
- **Azure Synapse**: `bh-synapse-workspace` in westus2. Public endpoint enabled. Firewall restricts by IP.
- **Connectivity**: Public internet only. TLS 1.2+ encrypted. Endpoint: `bh-synapse-workspace.sql.azuresynapse.net:1433`.
- **Auth**: SQL auth (username/password) in AWS Secrets Manager. No Azure AD integration.

### Hard Limitations

1. No existing cross-cloud VPN or private link
2. NAT Gateway IPs not static by default — Elastic IPs must be explicitly attached
3. Synapse Managed VNet restricts outbound from Synapse (doesn't affect BH-initiated connections)
4. BrightHive does not own an Azure subscription — customer-owned resources constrain options

---

## Connectivity Options

### Option 1: Public Endpoints with TLS (Current)

Lambda/Glue connects to Synapse SQL endpoint over public internet. TLS 1.2+ encrypts traffic. Synapse firewall allowlists BrightHive NAT Gateway Elastic IPs.

| Dimension | Assessment |
|-----------|------------|
| **Cost** | $0 incremental (NAT Gateway charges apply regardless) |
| **Latency** | 20-60ms us-east-1 to westus2 |
| **Security** | TLS 1.2+ in transit, Synapse firewall IP restriction, SQL creds in Secrets Manager |
| **Complexity** | Minimal — attach EIPs to NAT GWs, add to Synapse firewall |
| **Scale fit** | Dev/staging and early production batch pipelines |

**Hardening requirements**: Elastic IPs on NAT Gateways, `encrypt: true` in mssql connections, Secrets Manager credential rotation.

**Risks**: IP allowlisting fragile on NAT GW replacement. Enterprise customers may reject public endpoints in security reviews.

### Option 2: AWS Site-to-Site VPN + Azure VPN Gateway

IPsec tunnel between AWS VGW/TGW and Azure VPN Gateway. Traffic over public internet in encrypted tunnel, private IP addressing.

| Dimension | Assessment |
|-----------|------------|
| **Cost** | ~$210-250/month (AWS VPN $72 + Azure VPN GW $140) |
| **Latency** | 20-60ms (same backbone, IPsec adds <2ms) |
| **Security** | IPsec AES-256 wrapping TLS, private IP addressing |
| **Complexity** | Moderate — BGP/static routes, tunnel monitoring, CIDR coordination |
| **Scale fit** | Production MVP when customers require private connectivity |

**Risks**: Requires Azure-side infra (customer or BH-managed). VPN tunnels can flap. Per-customer tunnels don't scale past ~10 without Transit Gateway.

### Option 3: AWS Direct Connect + Azure ExpressRoute

Dedicated private circuits through colocation facility (Equinix, Megaport). Traffic never touches public internet.

| Dimension | Assessment |
|-----------|------------|
| **Cost** | $700-1000+/month + $1000-5000 setup |
| **Latency** | 10-20ms (dedicated fiber) |
| **Security** | Strongest — private network, MACsec available |
| **Complexity** | High — colocation provider, 2-8 week provisioning, dedicated networking expertise |
| **Scale fit** | Enterprise at TB/day volumes. Not justified for current scale. |

### Option 4: Azure Private Link + VPN (Overlay)

Private endpoints for Synapse SQL — no public exposure. **Requires VPN (Option 2) or Direct Connect (Option 3) underneath.** Not a standalone cross-cloud solution.

| Dimension | Assessment |
|-----------|------------|
| **Cost** | ~$15/month on top of VPN costs |
| **Security** | Strongest isolation — Synapse exposed only via private IP |
| **Complexity** | Moderate-High — overlay on Option 2 |
| **Scale fit** | High-security customers, layered on VPN |

---

## Data Transfer Patterns (Independent of Network)

### Pattern A: Direct SQL Load (Current for Connect)

```
Lambda/Glue --[TDS/SQL]--> Synapse SQL Endpoint
```

Best for: small-medium datasets, schema operations, Connect destinations.
Limitation: slow for bulk data.

### Pattern B: S3 to Azure Blob via AzCopy, then COPY INTO Synapse (Recommended for Phase 2)

```
S3 --[AzCopy]--> Azure Blob --[COPY INTO]--> Synapse
```

1. Glue writes Parquet/Delta to S3 (existing)
2. Lambda runs AzCopy to copy from S3 to customer Azure Blob container
3. Lambda executes `COPY INTO` on Synapse from Blob
4. AzCopy handles retry, checkpointing, parallelism
5. Parquet preserves schema, is Synapse-optimized

**Cost**: S3 egress $0.09/GB + Azure Blob ingress free. ~$9/100GB.

---

## Comparison Matrix

| Criteria | Public + TLS | VPN | Direct Connect | Private Link + VPN |
|----------|-------------|-----|----------------|-------------------|
| Monthly cost | $0 | $210-250 | $700-1000+ | $225-265 |
| Setup time | Hours | Days | Weeks | Days |
| Latency | 20-60ms | 20-60ms | 10-20ms | 20-60ms |
| Security | Good | Strong | Strongest | Strong |
| Complexity | Low | Moderate | High | Moderate-High |
| Azure subscription needed | No | Yes | Yes | Yes |
| Team expertise | None | Networking basics | Dedicated networking | Networking + Azure |

---

## Recommendations by Stage

### Dev/Test (Now)

**Option 1: Public Endpoints with TLS.**

- Assign Elastic IPs to NAT Gateways
- Add EIPs to `bh-synapse-workspace` firewall
- Enforce `encrypt: true` in mssql connections
- SQL creds in Secrets Manager with rotation
- Use Pattern A (direct SQL) for Connect, Pattern B (AzCopy) for bulk ingestion testing
- Zero additional cost, operational in hours

### Production MVP (3-6 months)

**Stay on Option 1, hardened.**

Unless a customer explicitly requires private connectivity for compliance:
1. Dedicated Elastic IPs documented per environment
2. Secrets Manager rotation Lambda (90-day rotation)
3. VPC Flow Logs for audit trail
4. CloudWatch alarms on Synapse connection failures
5. Customer-facing Synapse firewall configuration guide
6. Pattern B validated at production data volumes

**Upgrade trigger**: Customer security team rejects public endpoints during onboarding.

### Production Scale (12+ months)

**Option 2 (VPN) as default + Option 4 (Private Link) for high-security customers.**

1. AWS Transit Gateway as VPN hub (multiple customer connections)
2. Site-to-site VPN per customer Azure VNet
3. Private Link overlay for zero public exposure
4. Consider BrightHive Azure subscription for centralized VPN Gateway

**Option 3 (Direct Connect) remains out of scope** unless TB/day cross-cloud transfer with dedicated networking staff.

---

## Acceptance Criteria

- [ ] Elastic IPs assigned to NAT Gateways in Glue/Lambda subnets
- [ ] EIPs documented and added to `bh-synapse-workspace` firewall
- [ ] mssql connections enforce TLS 1.2+ (`encrypt: true, trustServerCertificate: false`)
- [ ] AzCopy S3-to-Blob transfer tested in dev
- [ ] COPY INTO Synapse from Blob validated with Parquet
- [ ] Customer-facing network config guide drafted

## Dependencies

| Dependency | Status |
|------------|--------|
| Elastic IPs on NAT Gateways | Not started |
| Azure Blob Storage for staging | Not started |
| AzCopy in Lambda layer or ECS | Not started |
| Customer Synapse firewall access | Available (bh-synapse-workspace) |
| BH-312 (Synapse ingestion Step Functions) | Done |
