---
name: cloud-deploy
description: Deploying and operating services on Azure or AWS with infrastructure as code - environment layout, managed Postgres/Redis/Kafka/search equivalents, container hosting, secrets, networking, and safe rollout. Use for any cloud infrastructure, IaC, or deployment configuration task.
---

# Cloud deployment (Azure / AWS)

Read the reference for the target cloud:
- Azure -> `references/azure.md`
- AWS -> `references/aws.md`

TODO(team): state which cloud each system runs on, the IaC tool (Terraform / Bicep / CDK / CloudFormation), state/backends, and environment names (e.g. dev, qa, prod).

## Rules for both clouds

- **Everything is code.** No portal/console-only changes. If something was clicked into existence, import it.
- **Plan before apply.** Always produce `terraform plan` / `az deployment what-if` / `cdk diff` and summarize creates, changes, and **destroys**. Only humans apply to shared environments.
- **Never** run destroy/delete or apply against a non-local environment without explicit human approval in the conversation.
- Secrets live in Key Vault / Secrets Manager and are injected at runtime via managed identity / IAM role. No long-lived access keys in pipelines; use OIDC federation from CI.
- Least privilege: one identity per service with only the permissions it needs.
- Private networking for data services (private endpoints / VPC-only). No public database endpoints.
- Tag every resource: `app`, `env`, `owner`, `cost-center`. TODO(team): your tag policy.
- Environments are identical in shape; differences are variables (size, count), not different code.

## Rollout

- Build once, promote the same image digest through environments.
- Readiness/liveness probes wired to Spring Actuator / app health endpoints.
- Database migrations run as a separate step (Flyway job/task) before the new app version receives traffic, and must be backward compatible (see db-migrations).
- Prefer rolling or blue/green with automated rollback on failed health checks.

## Checklist

- [ ] IaC change with plan/what-if output summarized
- [ ] No destroys unless intended and called out
- [ ] Secrets via managed identity / role, not keys
- [ ] Private networking for data services
- [ ] Tags applied
