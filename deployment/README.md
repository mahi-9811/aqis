# Deployment

The CD workflow publishes Docker images to GitHub Container Registry on pushes to
`main` and version tags.

Images:

- `ghcr.io/<owner>/<repo>/python-api:<tag>`
- `ghcr.io/<owner>/<repo>/java-gateway:<tag>`
- `ghcr.io/<owner>/<repo>/web:<tag>`

For branch builds, `<tag>` is the commit SHA. For Git tags, `<tag>` is the Git
tag name. `latest` is also updated.

## Optional SSH deployment

Set repository or environment variables:

- `DEPLOY_ENABLED`: set to `true` to enable deployment
- `DEPLOY_PATH`: remote directory for `docker-compose.prod.yml` and `.env`
- `SMOKE_BASE_URL`: public Python API base URL for smoke tests
- `SMOKE_GATEWAY_URL`: optional public Java gateway base URL
- `SMOKE_WEB_URL`: optional public web app URL
- `AQIS_GATEWAY_AUTH_ENABLED`: optional gateway API-key auth flag

Set secrets:

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
- `DEPLOY_PORT`: optional, defaults to `22`
- `DEPLOY_REGISTRY_USERNAME`: optional, used for private registry pulls
- `DEPLOY_REGISTRY_TOKEN`: optional, used for private registry pulls
- `AQIS_GATEWAY_API_KEY`: required only when gateway auth is enabled

The remote host must have Docker and Docker Compose installed.

## Kubernetes secrets

`deployment/k8s/secret.yaml` uses External Secrets Operator instead of checked-in
secret values. Provision a `ClusterSecretStore` named `aqis-secret-store` in the
cluster and store AQIS production values at the remote key `aqis/production`.

The manifest currently syncs:

- `AQIS_GATEWAY_API_KEY`
