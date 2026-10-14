# Slalom Capabilities Management API

<p align="center">
  <img src="./.images/byte-teacher.png" alt="Byte Teacher" width="200" />
</p>

A FastAPI application that enables Slalom consultants to register their capabilities and manage consulting expertise across the organization.

## Features

- View all available consulting capabilities
- Register consultant expertise and availability
- Track skill levels and certifications
- Manage capability capacity and team assignments
- Practice lead login with role-based access: only authenticated practice leads can register or unregister consultants, limited to their practice areas

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc
   - Capabilities Dashboard: http://localhost:8000/

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/capabilities`                                                   | Get all capabilities with details and current consultant assignments |
| POST   | `/capabilities/{capability_name}/register?email=consultant@slalom.com` | Register consultant for a capability (practice lead) |
| DELETE | `/capabilities/{capability_name}/unregister?email=consultant@slalom.com` | Unregister consultant from a capability (practice lead) |
| POST   | `/auth/login`                                                     | Log in with `{"username", "password"}`; returns a Bearer token       |
| POST   | `/auth/logout`                                                    | End the current session                                              |
| GET    | `/auth/me`                                                        | Get the logged-in practice lead's profile                            |

Register and unregister require an `Authorization: Bearer <token>` header and return 401 without a valid session or 403 outside the lead's practice areas. Sessions are in memory and expire after 8 hours. Register, unregister, login and logout events are written to the `audit` logger.

## Practice Leads

Accounts are stored in `practice_leads.json` with salted PBKDF2-SHA256 password hashes. Demo accounts for this exercise:

| Username        | Password             | Practice area |
| --------------- | -------------------- | ------------- |
| `tech.lead`     | `tech-lead-demo`     | Technology    |
| `strategy.lead` | `strategy-lead-demo` | Strategy      |
| `ops.lead`      | `ops-lead-demo`      | Operations    |

Replace these with real credentials, or SSO, before any real deployment.

## Data Model

The application uses a consulting-focused data model:

1. **Capabilities** - Uses capability name as identifier:
   - Description of the consulting capability
   - Skill levels (Emerging, Proficient, Advanced, Expert)
   - Practice area (Strategy, Technology, Operations)
   - Industry verticals served
   - Required certifications
   - List of consultant emails registered
   - Available capacity (hours per week)
   - Geographic location preferences

2. **Consultants** - Uses email as identifier:
   - Name
   - Practice area
   - Skill level
   - Certifications
   - Availability

All data is currently stored in memory for this learning exercise. In a production environment, this would be backed by a robust database system.

## Future Enhancements

This exercise will guide you through implementing:
- Capability maturity assessments
- Intelligent team matching algorithms  
- Analytics dashboards for practice leads
- Integration with project management systems
- Advanced search and filtering capabilities
