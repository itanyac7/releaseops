# ReleaseOps

ReleaseOps is a portfolio DevOps/SRE project designed to demonstrate operational practices around safe delivery, verification, rollback, monitoring, and failure recovery. The application itself is intentionally simple; the focus is on the delivery and operational lifecycle.

## Architecture

```text
                         ┌─────────────────────┐
                         │      GitHub          │
                         │   Source / main      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   GitHub Actions     │
                         │ Test / Build / Push  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       GHCR           │
                         │ Immutable SHA image  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Render — Staging     │
                         │ Deploy + Smoke Test  │
                         └──────────┬──────────┘
                                    │
                              Manual approval
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Render — Production  │
                         │ Deploy + Verify      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     UptimeRobot      │
                         │ /health monitoring   │
                         └─────────────────────┘
```

### Components

- **GitHub** — source control and the `main` branch.
- **GitHub Actions** — CI/CD orchestration.
- **GitHub Container Registry (GHCR)** — stores container images tagged with the full Git SHA.
- **Render staging** — first deployment target for a successful build.
- **Render production** — production environment protected by a GitHub Environment approval gate.
- **UptimeRobot** — external availability monitoring for the production `/health` endpoint.

The application exposes:

- `/` — basic service response.
- `/health` — health endpoint used by deployment smoke tests and external monitoring.
- `/api/version` — exposes the deployed Git SHA, service name, and environment for deployment verification.

## Deployment Flow

ReleaseOps uses a promotion-based deployment flow:

1. A change is pushed to `main`.
2. GitHub Actions runs the CI workflow.
3. Python tests run.
4. A Docker image is built and pushed to GHCR.
5. The image is tagged with the commit's full Git SHA.
6. A successful CI run triggers the staging deployment workflow.
7. Render staging is deployed using the exact SHA-tagged image.
8. The workflow waits for `/api/version` to report the expected SHA.
9. Staging smoke tests verify:
   - `/health` returns a healthy status.
   - `/api/version` reports the expected SHA.
   - The environment is `staging`.
   - The service name is `releaseops-staging`.
10. After staging succeeds, the production workflow pauses at a manual GitHub Environment approval gate.
11. Once approved, the same immutable image is deployed to production.
12. The production workflow waits for the expected SHA to become live.
13. Production smoke tests verify health, environment, service name, and deployed SHA.

This means production is promoted from a specific, verified build rather than rebuilding the application during production deployment.

## Rollback Strategy

Rollback is based on immutable container images rather than rebuilding from source.

Each image in GHCR is tagged with a full 40-character Git SHA. A rollback can therefore target a previously proven image directly.

The manual `Rollback production` workflow:

1. Accepts a full 40-character rollback SHA.
2. Validates that the input is a valid lowercase Git SHA.
3. Constructs the corresponding GHCR image reference.
4. Deploys that exact image to Render production.
5. Waits for `/api/version` to report the rollback SHA.
6. Verifies `/health`.
7. Verifies the production environment, service name, and final SHA.

This gives the deployment process a clear recovery target: **the last known-good immutable image**.

## Observability

ReleaseOps currently uses external uptime monitoring through UptimeRobot.

The production health endpoint:

```text
https://releaseops-production.onrender.com/health
```

is monitored every **5 minutes**.

The monitoring setup provides:

- External availability checks.
- UP notifications.
- DOWN notifications.
- Visibility independent of the deployment pipeline.

Deployment workflows also provide deployment-time observability by polling `/api/version` until the expected SHA is live and then running smoke tests against `/health`.

### Current monitoring evidence

The UptimeRobot configuration has been tested with both UP and DOWN notification tests, and the corresponding notification emails were received.

A real production outage incident has **not** yet been intentionally triggered. Controlled failure injection is planned as a future validation step.

## Failure / Recovery Evidence

Rollback and recovery have been tested against the live production service.

The proven sequence was:

```text
e9241149d99b462b34b03e3132a116d754690be0
                │
                ▼
438cf196d6bef27d5ee1423ff6bb794db75189d7
                │
                ▼
e9241149d99b462b34b03e3132a116d754690be0
```

### Initial production state

Production was running:

```json
{
  "environment": "production",
  "service": "releaseops-production",
  "version": "e9241149d99b462b34b03e3132a116d754690be0"
}
```

The `/health` endpoint returned:

```json
{
  "status": "healthy"
}
```

### Rollback test

The rollback workflow was executed with:

```text
438cf196d6bef27d5ee1423ff6bb794db75189d7
```

The rollback workflow completed successfully.

Production then reported:

```json
{
  "environment": "production",
  "service": "releaseops-production",
  "version": "438cf196d6bef27d5ee1423ff6bb794db75189d7"
}
```

The health check remained healthy.

### Restore test

Production was then restored using the same rollback workflow, targeting:

```text
e9241149d99b462b34b03e3132a116d754690be0
```

The restore workflow completed successfully.

Production returned to:

```json
{
  "environment": "production",
  "service": "releaseops-production",
  "version": "e9241149d99b462b34b03e3132a116d754690be0"
}
```

The health check again returned healthy.

This demonstrates a complete, live rollback-and-recovery path:

**known-good version → previous known-good version → restored version**

## Cost Trade-offs

The project is intentionally designed around a **$0/month target** using free tiers.

### Free-tier choices

- GitHub — source control and GitHub Actions.
- GHCR — container image storage.
- Render — free staging and production services.
- UptimeRobot — external uptime monitoring.

### Trade-offs

The free-tier architecture introduces operational limitations:

- **Cold starts:** free Render services may sleep when inactive, increasing response latency after inactivity.
- **Limited compute:** free instances are not suitable for production workloads with meaningful traffic.
- **Limited observability:** UptimeRobot provides basic availability monitoring rather than full application metrics, logs, and distributed tracing.
- **Shared/free infrastructure:** performance and reliability are constrained compared with paid infrastructure.
- **Registry and CI limits:** free-tier quotas can affect build frequency, storage, or retention as the project grows.
- **No high availability:** the deployment uses single free-tier services rather than multiple replicas or availability zones.

These limitations are intentional and documented rather than hidden. The project demonstrates how to make reasonable operational decisions under a strict cost constraint.

## Known Limitations

ReleaseOps is a portfolio demonstration, not a production-scale platform.

Known limitations include:

1. **No real production traffic load** — the deployment and monitoring paths are validated, but the application is not handling meaningful user traffic.
2. **Basic health checking** — `/health` verifies application availability but does not currently validate dependencies or deeper application health.
3. **Limited monitoring depth** — UptimeRobot detects endpoint availability but does not provide full metrics, traces, or log aggregation.
4. **No automated rollback on an observed outage** — rollback is currently a deliberate manual operational action through GitHub Actions.
5. **No intentional outage test yet** — notification delivery has been tested, but a real controlled production failure has not yet been injected.
6. **Free-tier constraints** — cold starts, resource limits, and lack of redundancy reduce the system's production realism.
7. **Single-region deployment** — both staging and production currently run in Render's Virginia region.
8. **Simple application architecture** — the Flask API intentionally has minimal business logic because the project's purpose is to demonstrate DevOps/SRE practices rather than application complexity.

## Operational Design Summary

The main design principle behind ReleaseOps is:

> **Deploy immutable artifacts, verify what is actually running, promote only after validation, and keep a known-good rollback path.**

The project therefore prioritizes operational evidence over the number of tools used. The current implementation has demonstrated:

- CI test and container build.
- SHA-based immutable image tagging.
- Automated staging deployment.
- Staging smoke testing.
- Manual production approval.
- Production deployment of the verified SHA.
- Production smoke testing.
- Manual SHA-based rollback.
- Live rollback and restoration.
- External production uptime monitoring.
- Tested UP and DOWN notification delivery.

The next planned operational validation is controlled failure injection to demonstrate detection and recovery from an actual service failure.
