# DeployGuard AI Technology Stack and Architecture

**Status:** Approved architecture source of truth
**Last updated:** August 20, 2026

## 1. Purpose

DeployGuard AI is a secure control plane for registering, evaluating, monitoring, approving, deploying, auditing, and rolling back business AI agents.

This document is the permanent source of truth for major technology and architecture decisions.

Before replacing, adding, or removing a major technology:

1. Explain the reason for the change.
2. Compare relevant alternatives.
3. Identify security, cost, and migration effects.
4. Receive explicit approval from the project owner.
5. Update this document through a feature branch and Pull Request.

## 2. Architecture principles

- Build one small, production-quality milestone at a time.
- Keep the complete MVP locally buildable and testable for $0.
- Use a modular monolith until scale or operational requirements justify another architecture.
- Separate frontend, backend, database, AI provider, storage, and cloud infrastructure through clear interfaces.
- Keep deterministic security and approval rules separate from LLM decisions.
- Require human approval for production deployments and important rollback-policy changes.
- Do not build password storage or authentication protocols from scratch.
- Do not introduce infrastructure before a real requirement exists.
- Do not create paid resources or enable paid APIs without explicit approval.
- Use feature branches, Pull Requests, required CI checks, and squash merging.

## 3. Technology status definitions

- **Implemented:** Present in the repository and currently used.
- **Planned:** Approved direction, but not necessarily implemented.
- **Undecided:** Requires an alternatives review and explicit approval.
- **Deferred:** Excluded from the MVP unless a demonstrated requirement changes the decision.
- **Paid or cost-controlled:** May generate charges and requires explicit approval before activation.

## 4. Implemented technologies

### Application

| Area | Technology | Version or decision |
| --- | --- | --- |
| Language | Python | 3.14.4 |
| Backend framework | FastAPI | 0.141.1 |
| ASGI server | Uvicorn | 0.52.3 |
| Data validation | Pydantic | 2.13.4 |
| Configuration | Pydantic Settings | 2.15.0 |

### Database persistence

| Area | Technology | Version or decision |
| --- | --- | --- |
| System of record | PostgreSQL | 18.x; 18.6 local implementation |
| Object-relational mapping | SQLAlchemy | 2.0.52 with synchronous sessions |
| Database migrations | Alembic | 1.19.1 with explicit execution |
| PostgreSQL driver | Psycopg | 3.3.4 with binary distribution for development and CI |
| Connection management | SQLAlchemy | Pre-ping and bounded pool configuration |
| Integration testing | PostgreSQL | Dedicated database ending in `_test`; no SQLite substitute |
| Tenant persistence | SQLAlchemy and PostgreSQL | UUID tenant record with unique slug, controlled status, and timestamps |

#### Milestone 3A architecture decision

**Status:** Approved by the project owner on August 18, 2026 and implemented through PR #13.

The approved PostgreSQL persistence foundation is:

- PostgreSQL 18.x using the latest supported patch release
- PostgreSQL 18.6 at the time of approval
- SQLAlchemy 2.0.52 with synchronous sessions
- Alembic 1.19.1 for explicit, version-controlled migrations
- Psycopg 3.3.4 as the PostgreSQL driver
- `psycopg[binary]` for Windows development and CI
- Real PostgreSQL integration tests using a dedicated database whose name ends in `_test`
- Database credentials loaded through Pydantic Settings
- Migrations executed explicitly rather than during API startup
- No SQLite substitute for PostgreSQL integration tests
- No paid services or persistent cloud resources

PR #13 was limited to database configuration, the SQLAlchemy engine and session
foundation, Alembic configuration, an empty baseline migration, integration
tests, CI test-database support, dependency updates, and documentation.

PR #13 did not add business tables, tenant tables, authentication,
authorization, Row-Level Security policies, product API routes, deployment
logic, Docker Compose, or cloud resources.

The persistence foundation is classified as implemented. PostgreSQL `jsonb`
usage and Row-Level Security remain planned until their own approved
milestones are implemented.

#### Milestone 3B architecture decision

**Status:** Approved by the project owner on August 20, 2026 and implemented through PR #14.

The approved tenant persistence model is:

- One `tenants` table representing customer organizations
- Application-generated UUID primary keys
- Unique tenant slugs containing 3 to 63 lowercase letters, numbers, or single hyphens
- Required display names containing 1 to 120 characters
- Controlled tenant statuses limited to `active` and `suspended`
- Timezone-aware creation and update timestamps
- Alembic revision `0002_create_tenants`
- Real PostgreSQL constraint and persistence integration tests
- Transaction rollback after every tenant persistence test
- No seeded tenant or production data

PR #14 is limited to the tenant SQLAlchemy model, Alembic migration,
model metadata tests, PostgreSQL persistence and constraint integration
tests, shared integration-test fixtures, and architecture documentation.

PR #14 does not add authentication, authorization, tenant memberships,
PostgreSQL Row-Level Security policies, agent records, product API routes,
tenant provisioning workflows, deployment logic, Docker resources, or
cloud resources.

Tenant-aware authorization and PostgreSQL Row-Level Security remain planned
for separately approved milestones.

### Testing and code quality

| Area | Technology | Version or decision |
| --- | --- | --- |
| Backend testing | Pytest | 9.1.1 |
| API testing | FastAPI TestClient with httpx2 | 2.10.0 |
| Coverage | pytest-cov | 7.1.0 with a 90% minimum |
| Linting and formatting | Ruff | 0.16.3 |
| Dependency validation | pip check | Required in CI |

### Security and CI/CD

| Area | Technology | Version or decision |
| --- | --- | --- |
| Dependency vulnerability scanning | pip-audit | 2.10.1 |
| Static Python security analysis | Bandit | 1.9.4 |
| Secret scanning | Gitleaks | 8.30.0 |
| Code scanning | GitHub CodeQL | Python analysis |
| CI/CD | GitHub Actions | Actions pinned to full commit SHAs |
| Workflow permissions | GitHub Actions | Read-only unless additional access is required |
| Git workflow | Git | Feature branch → tests → Pull Request → CI → squash merge |

Direct Python dependencies remain pinned in the requirements files. `.env` and `.venv` content must remain outside Git.

## 5. Planned technologies

These technologies are approved directions but are not considered implemented until added through their own reviewed milestones.

### Frontend

- Next.js with the App Router
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query when API integration begins
- Vitest and React Testing Library
- Playwright for end-to-end testing

### Backend architecture

- Continue using FastAPI.
- Use a modular monolith.
- Introduce versioned REST endpoints under `/api/v1`.
- Keep business logic separate from HTTP routing.
- Keep database, AI provider, object storage, and cloud integrations behind clear interfaces.

### Planned database capabilities

- PostgreSQL `jsonb` for provider-specific metadata
- PostgreSQL Row-Level Security after tenant isolation is implemented

### Authentication and authorization

- OpenID Connect
- OAuth 2.0
- Signed access tokens validated by FastAPI
- Tenant-aware Role-Based Access Control
- No custom password-storage implementation

The identity provider remains undecided.

### AI and agent integration

- A provider-neutral AI adapter interface
- Mocked AI responses or a local model during early development
- Human approval for production deployments
- Human approval for important rollback-policy changes
- Deterministic security and approval policies outside the LLM

The first hosted LLM provider remains undecided.

### Object storage

- MinIO for local development
- An S3-compatible storage interface
- Amazon S3 as an optional AWS production reference

### Containers and infrastructure

- Docker
- Docker Compose for local development
- Terraform for approved infrastructure changes

### Observability

- Structured JSON logging
- Correlation IDs
- OpenTelemetry
- CloudWatch only in an approved AWS environment

### Optional AWS production reference architecture

The documented enterprise reference architecture may use:

- Amazon ECS Fargate
- Amazon Elastic Container Registry
- Amazon Relational Database Service for PostgreSQL
- Amazon S3
- AWS Secrets Manager
- AWS Key Management Service
- Amazon CloudWatch
- Terraform

This is a reference architecture only. No AWS deployment is approved by this document.

## 6. Undecided technologies

### Identity provider

No identity provider has been selected.

Before selection, compare relevant options for:

- OpenID Connect and OAuth 2.0 support
- Tenant and role management
- FastAPI and Next.js integration
- Security controls
- Local development support
- Free-tier limitations
- Production pricing
- Migration and vendor-lock-in risk

### First hosted LLM provider

No hosted LLM provider has been selected.

When the first hosted AI feature begins, compare OpenAI and Azure OpenAI for:

- Model capabilities
- Security and privacy controls
- Regional availability
- Authentication
- Rate limits
- Pricing
- Monitoring
- Portability through the provider-neutral adapter

No paid API may be enabled without explicit approval.

## 7. Deferred technologies

The following technologies and architecture patterns are deferred from the MVP:

- Kubernetes
- Microservices
- A separate vector database
- Multi-cloud deployment
- Custom model training
- Fully autonomous production deployment
- Celery and Redis until a real asynchronous workflow exists
- Prometheus and Grafana until monitored workloads exist
- LangChain or LangGraph until a real workflow requires them

PostgreSQL remains the system of record. A queue, vector database, or additional orchestration framework must not be introduced based only on possible future needs.

## 8. Zero-cost local development rule

The complete MVP must remain buildable and testable locally for $0.

Use free and open-source local tools whenever possible:

- PostgreSQL locally
- Redis locally only when an asynchronous workflow requires it
- MinIO locally
- Docker Compose
- Mocked AI responses or a local model during early development
- Standard GitHub Actions runners for the public repository

Free tiers have limits and can change. They must not be described as permanently free.

## 9. Paid and cost-controlled technologies

The following services can generate charges:

- OpenAI API
- Azure OpenAI
- Amazon ECS Fargate
- Amazon RDS
- AWS Secrets Manager
- Amazon S3
- Amazon CloudWatch
- AWS KMS
- Amazon ECR
- AWS load balancers
- Amazon Route 53
- Managed Redis
- Custom domains

Do not create a paid cloud resource, enable a paid API, or request billing information without explicit approval.

Before any cloud deployment:

1. Verify current official pricing.
2. Estimate the maximum expected cost.
3. Explain free-tier limitations.
4. Configure budgets and billing alerts where available.
5. Provide a complete teardown procedure.
6. Receive explicit approval.

AWS remains a documented enterprise reference architecture until an actual deployment is approved. A temporary demonstration deployment must be removed after the demonstration unless continued operation is explicitly approved.

## 10. Security boundaries

- Validate all authentication tokens using approved libraries.
- Enforce tenant-aware authorization on protected operations.
- Add PostgreSQL Row-Level Security after tenant isolation exists.
- Apply least-privilege permissions to CI and cloud resources.
- Never commit secrets.
- Store production secrets in an approved secrets manager.
- Keep audit records separate from ordinary application logs.
- Do not allow an LLM to make final access-control decisions.
- Do not allow fully autonomous production deployments.
- Test security-sensitive changes before merging.

Security scanners reduce risk but do not prove that the application is vulnerability-free.

## 11. Change-control process

Every major architecture change must use this process:

1. Create a focused feature or documentation branch.
2. Explain the problem and proposed decision.
3. Compare relevant alternatives.
4. Document security, cost, and migration effects.
5. Receive explicit approval.
6. Update this source-of-truth document.
7. Run applicable tests and security checks.
8. Review the Git diff.
9. Open a Pull Request.
10. Merge only after required checks pass.

Application work must follow the architecture recorded in this document.
