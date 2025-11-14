# ExpEngine Service

The **ExpEngine Service** provides a RESTful API interface for managing experiments and workflows remotely. This service allows you to run, control, and monitor experiments through HTTP requests, making it ideal for integration with web applications, CI/CD pipelines, or remote experiment management.

## Overview

The ExpEngine Service runs as a Flask-based web service that exposes endpoints for:

- **Starting experiments** by name
- **Managing experiment lifecycle** (pause, resume, kill)
- **Managing workflow lifecycle** (pause, resume, kill)
- **Cross-origin resource sharing (CORS)** support for web applications

## API Documentation

!!swagger openapi.yaml!!

## Service Configuration

### Prerequisites

- Python >= 3.10
- Flask and Flask-CORS
- ExpEngine package installed
- Properly configured experiment specifications

### Starting the Service

The service runs on `http://localhost:5556` by default.

```bash
python api.py
```

## Security Considerations

!!! warning "Production Deployment"
    - The current implementation runs without authentication
    - Consider implementing API keys or OAuth for production use
    - Ensure proper network security (firewall, VPN) for production deployments
    - Monitor and log API usage for security auditing