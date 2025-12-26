# Simple FRED Site

A simple website that fetches economic data from the Federal Reserve Economic Data (FRED) API and provides AI-powered summaries using the OpenAI API.

## Project Overview

This project consists of:
- **Backend**: FastAPI service that integrates with FRED API and OpenAI API
- **Frontend**: React application for user interaction
- **Infrastructure**: Docker containerization for easy local development

## Features

- Fetch economic data from FRED by series ID
- Generate AI-powered summaries of economic data
- Modern, responsive web interface
- Containerized deployment with Docker

## Prerequisites

- Docker Desktop installed and running
- FRED API key ([Get one here](https://fred.stlouisfed.org/docs/api/api_key.html))
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your API keys
3. Run `docker-compose up` to start all services
4. Access the frontend at `http://localhost:3000`
5. Backend API available at `http://localhost:8000`

## Project Structure

```
SimpleFREDSite/
├── backend/          # FastAPI backend service
├── frontend/         # React frontend application
├── docker-compose.yml # Docker orchestration
└── .github/          # CI/CD workflows
```

## Development

### Running Locally with Docker

```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Stop all services
docker-compose down

# Rebuild images
docker-compose build

# View logs
docker-compose logs -f
```

### Running Tests

```bash
# Backend tests
docker-compose run backend pytest

# Frontend tests
docker-compose run frontend npm test
```

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /api/fred/fetch` - Fetch FRED data by series ID
- `POST /api/summarize` - Generate summary using OpenAI

## Environment Variables

See `.env.example` for required environment variables:
- `FRED_API_KEY` - Your FRED API key
- `OPENAI_API_KEY` - Your OpenAI API key

## License

MIT

