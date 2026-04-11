# Django Tech Challenge - Accommodation Booking API

Welcome to the Django implementation of Buoy's accommodation booking tech challenge!

This repository contains a **partially implemented accommodations booking REST API**, designed as a work-in-progress prototype for a real-world application.

You must use the provided code sample and its dependencies to solve the problems explained below.

The solution must be a cloud git repository, hosted on any cloud git tool of your choice.

- Its first commit must:
  - Have the message "First commit"
  - Have the exact code sample as it was provided, no changes whatsoever
- From this point on, work on the problems exposed below as you like

NOTE: In case you want to create a private git repository, please grant the user matthew@buoydevelopment.com full access to the repo. If you do so, please make it clear once you reply with your answer.

---

# Problem #1

### Issue to solve

There's an Accommodations entity already in place, however the business model only includes Hotels and Apartments.

### Expected behaviour

- Add these 2 new entities to the project.
- Provide endpoints for their management.

# Problem #2

### Issue to solve

Currently, every Accommodation can contain several overlapping Bookings with the same `start_date` and `end_date`. This makes sense for Hotels, which can have different Rooms booked simultaneously, but it wouldn't work for Apartments.

### Expected behaviour

- Apartments should not allow overlapping bookings during the same period (`start_date` and `end_date`).
- Hotels should allow overlapping bookings during the same period, as these would correspond to bookings for different rooms within the hotel.

# Problem #3

### Issue to solve

If frontend needs to, given an accommodation's `id` and a `date`, retrieve the next available date for that accommodation.

### Question

- How would you solve this problem?
- What data or API would you provide to the frontend?

# Problem #4 – Voice Notes (Voice-to-Text Extension)

> **Context**  
> As this API grows, accommodation operators and support agents want to move faster when capturing contextual information about a booking (special requests, incident reports, hand-off notes between shifts, etc.). Typing out these notes is slow and often skipped; they’d prefer to speak into their phone or laptop and have the system store both the original audio and a clean text transcript.

### Business Goal

Enable staff to attach short **voice notes** to a booking so that:

- A staff member can **record a brief audio note** related to a specific booking.
- The system **transcribes that audio to text** using a voice-to-text service.
- Other staff can **view the transcription alongside the original booking**, and (optionally) download or listen to the original audio file.

This section is intentionally open-ended: you may choose any tools, libraries, services, or architecture you believe are appropriate.

---

### Functional Requirements

#### 1. Attach a Voice Note to a Booking

- Given an existing booking, the system must allow a client to submit a short audio clip associated with that booking.
- Audio may be uploaded as a file (e.g., `.wav`, `.mp3`, `.m4a`, etc.).
- You are free to design the endpoint(s), but they should be **REST-ful** and consistent with the project’s existing API style.

#### 2. Transcribe the Audio

- The system must send the audio to a **voice-to-text (VTT) service** of your choice and store the resulting transcription.
- The transcription must be persisted in the database and clearly associated with:
  - the booking  
  - the original audio resource
- You may implement transcription **synchronously** (request blocks until complete) or **asynchronously** (background worker, queue, webhook, etc.).
- Document your choice and the trade-offs.

#### 3. Retrieve a Booking’s Voice Notes

- A client must be able to retrieve a booking and see **all voice notes** associated with it, including at least:
  - an identifier  
  - the transcript text  
  - creation timestamp  
- Optionally expose a way to download or play the original audio file.

---

### Technical & Design Guidelines

You are free to choose:

#### Voice-to-Text Provider

Any API or library is acceptable (cloud-hosted or local), provided that:

- The integration is **cleanly encapsulated** behind an interface or abstraction.
- The README includes instructions for running the transcription step locally (API keys, environment variables, etc.).

#### API Design

You may introduce new resources (e.g., nested routes under `bookings`) or extend existing endpoints.  
The design should be:

- consistent with REST principles  
- discoverable and documented  
- aligned with the project’s conventions  

#### Implementation Details

You choose how to:

- model voice notes in the database  
- structure Django/DRF components (serializers, viewsets, services, storage, etc.)  
- handle background work (if used)

The goal is not to pick the “right” VTT provider, but to demonstrate **how** you structure a clean, testable integration.

---

### What We’ll Be Looking For

#### API & Data Modeling

- Clear, extensible API surface  
- Data model that accommodates multiple notes per booking and future enhancements

#### Integration Design

- VTT provider wrapped in a clean abstraction  
- Ability to swap providers with minimal rewriting

#### Error Handling & Edge Cases

- Handling of failed transcription attempts  
- Validation for unsupported audio formats  
- Clear feedback to API consumers  

#### Testing & Observability

- Meaningful tests (mocking external services is fine)  
- Helpful logging for debugging failures  

#### Documentation & Developer Experience

- Notes describing:
  - chosen VTT provider  
  - local configuration instructions  
  - assumptions and limitations  

---

### Scope & Timeboxing

This extension should not double the scope of the exercise.

- Favor a small, well-designed slice over an exhaustive system.
- Reasonable simplifying assumptions are acceptable (e.g., max audio length, limited file formats).
- If the VTT provider requires paid usage, document how we can still verify your integration using free tiers, test modes, or clear stubs/mocks.

# Problem #5 (For Applied ML Candidates Only) — ML Systems Design Add-On

This section is required only for candidates applying to Applied ML / ML Engineering roles.  
It is intentionally short and should take no more than 30–45 minutes.

The purpose is to understand your real-world experience operating ML systems and how you reason about ML architecture, performance, and trade-offs. We are not looking for long essays—short, clear bullet points are preferred.

Where relevant, please reference concrete details from systems you have actually built or operated. We will explore your answers in detail during the live interview.

---

### Part A — Prior Experience (Real-World Applied ML Work)

In 5–10 bullet points, describe a production ML-powered system you have personally built or operated.  
This can be in ASR/VTT, OCR, NLP, RAG, ranking, fraud detection, or any other ML domain.

Please include (at least):

1. What the system did (e.g., OCR pipeline, streaming ASR, retrieval system, fraud detection).  
2. Your exact role and what parts you owned.  
3. Traffic characteristics (throughput, request sizes, concurrency, latency targets, etc.).  
4. Infrastructure / compute details:  
   - CPU vs GPU  
   - instance types  
   - memory/latency constraints  
   - batching strategy (if applicable)  
5. Key bottlenecks or incidents you encountered in production.  
6. Observability:  
   - how you monitored inference  
   - metrics you tracked (latency, drift, error rates, etc.)  
7. What you would do differently with the benefit of hindsight.

Note: Do not include anything confidential. High-level descriptions and ranges are fine.

---

### Part B — Voice-to-Text System Architecture (Applied to This Project)

Using the voice-notes feature from Problem #4, outline how you would design a production-ready voice-to-text subsystem if the product needed to scale beyond the single-app architecture used in the take-home.

You may answer in bullet points.  
Keep this section to 1–2 pages maximum.

Include:

1. High-level architecture:  
   - where transcription happens (inline vs async vs separate microservice)  
   - data flow from API → storage → transcription → callbacks → persistence  

2. Model/provider selection:  
   - hosted API (OpenAI Whisper, Deepgram, etc.) vs self-hosted models  
   - trade-offs of your choice  
   - how you would switch providers if necessary  

3. Performance considerations:  
   - expected latency and throughput  
   - GPU vs CPU inference choices and rationale  
   - batching, streaming, or chunking strategies  

4. Scalability strategy:  
   - autoscaling approach  
   - concurrency limits  
   - worker vs pod model  
   - queue selection (if used)  

5. Observability:  
   - metrics and logs you would capture  
   - how you would track failures, retries, and slowdowns  
   - how you would detect drift or degradation  

6. Failure handling and degraded modes:  
   - behavior when transcription fails  
   - retry strategy  
   - how to handle corrupted audio or timeouts  
   - fallback behavior to maintain system utility  

7. Security and compliance considerations:  
   - storage approach for audio  
   - retention policy  
   - considerations for PII or sensitive audio content  

---

### Part C — Optional Architecture Sketch

If helpful, include a simple diagram showing your proposed architecture.  
A hand-drawn sketch, Mermaid diagram, or ASCII diagram is acceptable.

---

### Notes

- Do not overthink this section. We are evaluating how you think, not how long you spend writing.  
- Specificity is preferred over polished writing.  
- It is acceptable to note assumptions or unknowns.  


---


## TECH CONTEXT
### Stack

The main libraries are:
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django ORM](https://docs.djangoproject.com/en/5.0/topics/db/)

### Docker Setup
To set up the project using Docker Compose, follow these steps:

1. Ensure you have Docker and Docker Compose installed on your machine.
2. Build and start the Docker containers:

  ```bash
  docker compose up --build
  ```

3. The application should now be running and accessible at `http://localhost:8006`.

### Swagger Documentation

The interactive API documentation is available at:
```
http://localhost:8006/documentation/
```

### Migrations

Migrations are automatically applied when the Docker containers start via the `entrypoint.sh` script.

For manual migration management during development:

#### Migration creation
1. Stop the web container: `docker compose stop web`
2. Run the migration creation command: 
   ```bash
   docker compose run --rm web python manage.py makemigrations
   ```
3. Restart containers: `docker compose up`

#### Manual Migration Up
```bash
docker compose run --rm web python manage.py migrate
```

#### Manual Migration Down
```bash
docker compose run --rm web python manage.py migrate <app_name> <migration_number>
```

## 🚀 Current Implementation

### Available Endpoints

#### Accommodations
- `GET /accommodations/` - List all accommodations
- `POST /accommodations/` - Create accommodation
- `GET /accommodations/{id}/` - Get accommodation by ID
- `PUT /accommodations/{id}/` - Update accommodation
- `DELETE /accommodations/{id}/` - Delete accommodation

#### Bookings
- `GET /bookings/` - List all bookings
- `POST /bookings/` - Create booking
- `GET /bookings/{id}/` - Get booking by ID
- `PUT /bookings/{id}/` - Update booking
- `DELETE /bookings/{id}/` - Delete booking

### Current Data Models

#### Accommodation (Base Model)
```json
{
    "id": 1,
    "name": "Luxury Hotel Downtown",
    "description": "A beautiful hotel in the city center",
    "price": "150.00",
    "location": "Downtown"
}
```

#### Booking
```json
{
    "id": 1,
    "accommodation": 1,
    "start_date": "2024-02-01",
    "end_date": "2024-02-05",
    "guest_name": "John Doe"
}
```

## 🔧 Development Setup

### Docker Development (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd tech-challenge-python
   ```

2. **Start with Docker Compose**:
   ```bash
   docker compose up --build
   ```

3. **Access the application**:
   - API: `http://localhost:8006`
   - Documentation: `http://localhost:8006/documentation/`
   - Admin: `http://localhost:8006/admin/`

### Local Development (without Docker)

1. **Prerequisites**:
   - Python 3.11+
   - PostgreSQL 15+

2. **Install PostgreSQL** (if not already installed):
   ```bash
   # macOS with Homebrew
   brew install postgresql
   brew services start postgresql
   
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql
   
   # Windows - Download from https://www.postgresql.org/download/windows/
   ```

3. **Create database**:
   ```bash
   # Connect to PostgreSQL as superuser
   sudo -u postgres psql
   
   # Or on macOS/Windows where postgres user might be your username:
   psql postgres
   
   # Create database and user
   CREATE DATABASE accommodation_booking;
   CREATE USER postgres WITH ENCRYPTED PASSWORD 'postgres';
   GRANT ALL PRIVILEGES ON DATABASE accommodation_booking TO postgres;
   \q
   ```

4. **Setup Python environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env file with your database settings if different from defaults
   ```

7. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

8. **Create superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

9. **Start development server**:
   ```bash
   python manage.py runserver 8006
   ```

10. **Access the application**:
    - API: `http://localhost:8006`
    - Documentation: `http://localhost:8006/documentation/`
    - Admin: `http://localhost:8006/admin/` (if superuser created)

## 📁 Project Structure

```
tech-challenge-python/
├── accommodation_booking/     # Django project settings
│   ├── __init__.py
│   ├── settings.py           # Configuration with PostgreSQL
│   ├── urls.py              # Main URL routing
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
├── accommodations/           # Accommodations app
│   ├── migrations/          # Database migrations
│   ├── models.py            # Accommodation model
│   ├── serializers.py       # DRF serializers with validation
│   ├── views.py            # Accommodation views
│   ├── urls.py             # URL routing
│   ├── admin.py            # Admin configuration
│   └── apps.py             # App configuration
├── bookings/                # Bookings app
│   ├── migrations/          # Database migrations
│   ├── models.py           # Booking model
│   ├── serializers.py      # Booking serializers
│   ├── views.py           # Booking CRUD operations
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin configuration
│   └── apps.py            # App configuration
├── requirements.txt        # Python dependencies
├── docker compose.yml     # Docker services configuration
├── Dockerfile            # Docker image definition
├── entrypoint.sh         # Docker entrypoint script
├── env.example          # Environment variables template
├── manage.py           # Django management commands
└── README.md          # This documentation
```

## 🌐 Environment Variables

Create a `.env` file based on `env.example`:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEBUG` | Enable debug mode | `True` | No |
| `SECRET_KEY` | Django secret key | `django-insecure-your-secret-key-here` | Yes (change in production) |
| `DB_HOST` | Database host | `localhost` | No |
| `DB_PORT` | Database port | `5432` | No |
| `DB_NAME` | Database name | `accommodation_booking` | No |
| `DB_USER` | Database user | `postgres` | No |
| `DB_PASSWORD` | Database password | `postgres` | No |

## 🧪 Testing the API

You can test the API using the interactive documentation at `http://localhost:8006/documentation/` or use curl:

```bash
# List accommodations
curl http://localhost:8006/accommodations/

# Create an accommodation
curl -X POST http://localhost:8006/accommodations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Hotel",
    "description": "A test hotel",
    "price": "100.00",
    "location": "Test City"
  }'

# List bookings
curl http://localhost:8006/bookings/

# Create a booking (replace {accommodation_id} with actual ID)
curl -X POST http://localhost:8006/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "accommodation": 1,
    "start_date": "2024-03-01",
    "end_date": "2024-03-05",
    "guest_name": "John Doe"
  }'
```

## 🚨 Current Dependencies

The project uses the following key dependencies (see `requirements.txt` for versions):

- `Django==5.0.0` - Web framework
- `djangorestframework==3.14.0` - REST API framework
- `psycopg2-binary==2.9.9` - PostgreSQL adapter
- `drf-spectacular==0.27.0` - API documentation
- `django-cors-headers==4.3.1` - CORS handling
- `python-dotenv==1.0.0` - Environment variable management 