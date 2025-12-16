# DevOps & CI/CD Strategy

## 1. Containerization (Docker)
We use a multi-stage build to keep images light.

### Backend Dockerfile
1.  **Base:** `node:18-alpine`
2.  **Build:** Install dependencies (`npm ci`), copy source.
3.  **Production:** Copy built artifacts, start command `node dist/index.js`.

## 2. CI/CD Pipeline (GitHub Actions)

### Workflow: `main.yml`
**Trigger:** Push to `main` branch.

**Jobs:**
1.  **Test:**
    * Checkout code.
    * Install dependencies.
    * Run Unit Tests (Jest).
    * Run Linting (ESLint).
2.  **Build & Push:**
    * Login to Docker Hub / AWS ECR.
    * Build Docker Image.
    * Push Image with tag `latest` and `sha-${commit_hash}`.
3.  **Deploy:**
    * Connect to Production Server (via SSH or K8s).
    * Pull new image.
    * Restart containers.

## 3. Environment Variables
The following must be set in the CI secrets and Production server:
* `DATABASE_URL`
* `JWT_SECRET`
* `NODE_ENV` (production)
* `PORT`