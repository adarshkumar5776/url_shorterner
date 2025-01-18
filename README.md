# URL Shortener API

## Overview
The URL Shortener API allows users to shorten long URLs and manage them with optional password protection. It provides endpoints for creating short URLs, redirecting to original URLs, and viewing analytics with access logs.

## Features
- Shorten long URLs into shorter, more manageable links.
- Optionally protect shortened URLs with a password.
- Track access counts and view analytics for each shortened URL.

## Getting Started

### Prerequisites
- Python 3.x
- FastAPI
- SQLite

### Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
2. Navigate to the project directory:
     ```bash
   cd url-shortener-api
3. Set up the environment:
     ```bash
   pip install -r requirements.txt
4. Initialize the database:
     ```bash
   python -c "from main import init_db; init_db()"
     
## Configuration
Ensure the database file `url_shortener.db` exists in the project directory. The database is managed using SQLite.

## Running the Application
Start the FastAPI application using the following command:

    uvicorn main:app --reload 
    
Access the API at http://127.0.0.1:8000.


## Shorten URL API Endpoint

**Endpoint**: `/shorten`

**Method**: POST

**Request Body**:

- `original_url` (HttpUrl): The original URL to shorten.
- `expiry_hours` (int, optional): Expiry time in hours (default: 24).
- `password` (str, optional): Optional password for the shortened URL.

**Response**:

- `short_url`: Shortened URL.

## Redirect to Original URL API Endpoint

**Endpoint**: `/`{short_url}`

**Method**: GET

**Parameters**:

- `short_url` (str): The shortened URL.

**Response**:

- `original_url`: Redirects to the original URL.

## Analytics for Shortened URL API Endpoint

**Endpoint**: `/analytics/{short_url}`

**Method**: GET

**Parameters**:

- `short_url` (str): The shortened URL.

**Response**:

- `original_url`
- `short_url`
- `access_count`
- `expiration_time`
- `logs`: List of access logs with timestamps and IP addresses.


## Example cURL Command

### Shorten a URL:
      curl --location 'http://127.0.0.1:8000/shorten' \
      --header 'Content-Type: application/json' \
      --data '{"original_url": "https://www.interviewbit.com/", "expiry_hours": 48}'

### Redirect to Original URL:
      curl --location 'http://127.0.0.1:8000/9aa1c2/'

### Analytics for Shortened URL:
      curl --location 'http://127.0.0.1:8000/analytics/9aa1c2/'












    
    


