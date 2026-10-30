# AWS reference

TODO(team): replace these defaults with the services you actually use.

## Service mapping

| Need | Typical AWS service |
|---|---|
| Containers | ECS on Fargate, or EKS for full Kubernetes |
| Postgres | Amazon RDS for PostgreSQL / Aurora PostgreSQL |
| Redis | ElastiCache (Redis OSS / Valkey) or MemoryDB |
| Kafka | Amazon MSK (provisioned or serverless) |
| Search | Amazon OpenSearch Service, or Elastic Cloud on AWS |
| Secrets | Secrets Manager / SSM Parameter Store + IAM roles |
| Images | ECR |
| Static frontend | S3 + CloudFront |
| Workflows / scheduling | Step Functions, EventBridge Scheduler, Glue, MWAA (Airflow) |
| Observability | CloudWatch, X-Ray / ADOT |
| CI/CD | GitHub Actions (OIDC role assumption) or CodePipeline |

## IaC

- Terraform (aws provider): `terraform plan -var-file=<env>.tfvars`; remote state in S3 with locking.
- CDK: `cdk diff <stack>`; CloudFormation change sets for review.

## Conventions

- One account per environment (via AWS Organizations) where possible; otherwise strict naming + tags.
- Task/pod IAM roles per service (ECS task role / EKS IRSA or Pod Identity). No access keys in containers.
- Data services in private subnets; security groups allow only the app's security group.
- RDS: Multi-AZ in prod, automated backups, IAM auth or Secrets Manager rotation.

## Notes

- If the code targets Elasticsearch but AWS runs OpenSearch, check client and API compatibility before shipping (they diverged after ES 7.10).
- MSK IAM auth needs the `aws-msk-iam-auth` library on the Java client classpath.
