# System Architecture Document

## 1. Overview
The platform follows a **Microservices-ready Monolithic architecture** (or Modular Monolith) to ensure ease of development while allowing for future scalability.

## 2. Tech Stack
* **Frontend:** React.js (SPA) with TypeScript and Tailwind CSS.
* **Backend:** Node.js with Express.
* **Database:** PostgreSQL (Relational data for users and products).
* **Caching:** Redis (for session/token management).
* **Infrastructure:** Docker containers orchestrated via Kubernetes (optional) or Docker Compose for dev.

## 3. Data Flow
1.  **Client Request:** User interacts with the React UI.
2.  **API Gateway/Load Balancer:** Nginx routes traffic to the backend.
3.  **Middleware Layer:** Intercepts requests for logging, CORS, and JWT Authentication.
4.  **Controller Layer:** Handles business logic.
5.  **Data Access Layer:** ORM (Prisma/Sequelize) interacts with PostgreSQL.

## 4. Security Architecture
* **Authentication:** JWT (JSON Web Tokens) using RS256 signatures.
* **Data Encryption:** bcrypt for password hashing; TLS for data in transit.
* **Validation:** Zod or Joi schema validation on all API inputs.