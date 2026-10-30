# Azure reference

TODO(team): replace these defaults with the services you actually use.

## Service mapping

| Need | Typical Azure service |
|---|---|
| Containers | Azure Container Apps, or AKS for full Kubernetes |
| Postgres | Azure Database for PostgreSQL - Flexible Server |
| Redis | Azure Cache for Redis / Azure Managed Redis |
| Kafka | Event Hubs (Kafka-compatible endpoint) or Confluent Cloud on Azure |
| Search | Elastic Cloud on Azure, or self-managed on AKS |
| Secrets | Key Vault + managed identity |
| Images | Azure Container Registry |
| Static frontend | Static Web Apps, or Storage + Front Door |
| Workflows / scheduling | Logic Apps, Container Apps Jobs, Data Factory |
| Observability | Azure Monitor, Application Insights, Log Analytics |
| CI/CD | GitHub Actions (OIDC federated credentials) or Azure DevOps Pipelines |

## IaC

- Bicep: `az deployment group what-if --resource-group <rg> --template-file main.bicep --parameters @<env>.parameters.json`
- Terraform (azurerm): `terraform plan -var-file=<env>.tfvars`; remote state in a Storage Account with state locking.

## Conventions

- Resource group per app per environment: `rg-<app>-<env>-<region>`.
- Naming: follow Cloud Adoption Framework abbreviations (e.g. `ca-`, `kv-`, `psql-`, `acr`).
- Use system- or user-assigned managed identity for app -> Key Vault/Postgres/Storage access; Entra ID auth for Postgres where possible.
- Private endpoints + private DNS zones for Postgres, Redis, Key Vault, Storage.

## Notes when using Event Hubs as Kafka

- Kafka endpoint on port 9093, SASL_SSL. Some Kafka features (e.g. compaction, transactions) have tier-specific support; verify against current Event Hubs docs before relying on them.
