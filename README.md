# 🚀 Event-Driven CRM System (Microservices)

## 🧠 Overview

This project implements an event-driven CRM system using a microservice architecture:

* **user-service** (Companies & Users)
* **crm-service** (Leads & Workflow)
* PostgreSQL (separate DB per service)
* Kafka (async processing)
* Docker Compose
* GraphQL APIs

---

# 🚀 Setup Instructions

## 1. Clone the repository


## 2. Create your .env file

Copy the template file:

```
cp .env.template .env
```

Update database credentials and environment variables inside `.env`.

---

## 3. Run the project

```
docker compose up --build
```

---

# 🌐 Services

## User Service (Port 8002)

```
http://localhost:8002/graphql/
```

Handles:

* Companies (Parent / Child hierarchy)
* Users (PARENT_ADMIN / CHILD_USER)

---

## CRM Service (Port 8001)

```
http://localhost:8001/graphql/
```

Handles:

* Leads
* Role-based access control
* Kafka event publishing
* Cross-service validation with user-service

---

# 🧩 User Service – GraphQL Examples

### Create Parent Company

```graphql
mutation {
  createCompany(name: "Parent Company") {
    company {
      id
      name
    }
  }
}
```

---

### Create Child Company

```graphql
mutation {
  createCompany(
    name: "Child Company B"
    parentId: "PARENT_COMPANY_ID"
  ) {
    company {
      id
      name
      parent {
        id
        name
      }
    }
  }
}
```

---

### Create User

```graphql
mutation {
  createUser(
    email: "companyBuser@test.com"
    role: "PARENT_ADMIN" # PARENT_ADMIN, CHILD_USER
    companyId: "COMPANY_ID"
  ) {
    user {
      id
      email
      role
      company {
        id
        name
      }
    }
  }
}
```

---

# 🧩 CRM Service – GraphQL Examples

> ⚠️ All CRM requests require header:

```
x-user-id: USER_ID
```

---

### Create Lead

```graphql
mutation {
  createLead(
    name: "Child Lead 11"
    email: "chl11@test.com"
    companyId: "COMPANY_ID"
  ) {
    lead {
      id
      name
      status
      company {
        id
        name
      }
    }
  }
}
```

---

### Query Leads

```graphql
query {
  leads(orderBy: "-created_at") {
    id
    name
    status
    company {
      name
    }
  }
}
```

---

### Update Lead Status

```graphql
mutation {
  updateLeadStatus(
    leadId: "LEAD_ID"
    status: "CONTACTED"
  ) {
    lead {
      id
      status
    }
  }
}
```

---

# 🔄 Asynchronous Workflow

1. Lead is created with status `NEW`.
2. CRM publishes `lead.created` event to Kafka.
3. `crm-worker` consumes event.
4. Worker updates lead status to `QUALIFIED`.
5. Eventual consistency is achieved.

---

# 📌 Lead Lifecycle

* `NEW` → Default
* `QUALIFIED` → Kafka worker
* `CONTACTED`, `REJECTED` → Manual update

---

# 📁 Project Structure

<pre>
aerialytic-event-driven-crm/
│
├── apps/
│   ├── crm-service/
│   │   ├── core/
│   │   ├── leads/
│   │   ├── kafka/
│   │   └── manage.py
│   │
│   └── user-service/
│       ├── core/
│       ├── users/
│       └── manage.py
│
├── docker-compose.yml
├── .env.template
└── README.md
</pre>

---

# 🛡 Data Integrity & Security

* Separate databases per service
* No cross-service foreign keys
* Role-based access enforced in CRM
* Cross-service validation via HTTP
* Kafka-based async processing
* Header-based authentication (`x-user-id`)

---

# 🎯 Architecture Decisions

* Microservice separation by bounded context
* Independent databases
* Synchronous validation (HTTP)
* Asynchronous workflow (Kafka)
* GraphQL APIs for flexibility
* Dockerized reproducible environment

* Clean separation
* Preserved business logic
* Cross-service validation
* Event-driven processing
* Production-style microservice structure
