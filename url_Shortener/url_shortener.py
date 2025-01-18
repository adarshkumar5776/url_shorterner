from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from datetime import datetime, timedelta
import hashlib
import sqlite3

app = FastAPI()

DB_FILE = "url_shortener.db"

def init_db():
    """
    Initialize the database by creating necessary tables if they do not exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY,
            original_url TEXT NOT NULL,
            short_url TEXT UNIQUE NOT NULL,
            creation_time TEXT NOT NULL,
            expiration_time TEXT NOT NULL,
            access_count INTEGER DEFAULT 0
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY,
            short_url TEXT NOT NULL,
            access_time TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            FOREIGN KEY(short_url) REFERENCES urls(short_url)
        )
    """
    )
    conn.commit()
    conn.close()

def generate_short_url(original_url):
    """
    Generate a shortened URL using MD5 hash of the original URL.

    Args:
        original_url (str): The original URL to be shortened.

    Returns:
        str: The shortened URL.
    """
    hash_object = hashlib.md5(original_url.encode())
    return hash_object.hexdigest()[:6]

def is_expired(expiration_time):
    """
    Check if the given expiration time has passed.

    Args:
        expiration_time (str): Expiration time in the format "%Y-%m-%d %H:%M:%S".

    Returns:
        bool: True if the expiration time is past, False otherwise.
    """
    return datetime.utcnow() > datetime.strptime(expiration_time, "%Y-%m-%d %H:%M:%S")

class ShortenRequest(BaseModel):
    """
    Pydantic model for the request body to shorten a URL.

    Attributes:
        original_url (HttpUrl): The original URL to shorten.
        expiry_hours (int): The number of hours until the URL expires. Default is 24 hours.
    """
    original_url: HttpUrl
    expiry_hours: int = 24

@app.post("/shorten")
async def shorten_url(request: ShortenRequest):
    """
    Endpoint to shorten a URL.

    Args:
        request (ShortenRequest): The request body containing the original URL and optional expiry hours.

    Returns:
        dict: A dictionary containing the shortened URL.
    """
    original_url = str(request.original_url) 
    expiry_hours = request.expiry_hours

    short_url = generate_short_url(original_url)
    expiration_time = datetime.utcnow() + timedelta(hours=expiry_hours)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO urls (original_url, short_url, creation_time, expiration_time)
            VALUES (?, ?, ?, ?)
        """,
            (
                original_url,
                short_url,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                expiration_time.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
    except sqlite3.IntegrityError:
        pass 
    conn.commit()
    conn.close()

    return {"short_url": f"https://short.ly/{short_url}"}

@app.get("/{short_url}")
async def redirect_url(short_url: str, request: Request):
    """
    Endpoint to redirect a short URL to its original URL.

    Args:
        short_url (str): The shortened URL.
        request (Request): The incoming request, including client information.

    Returns:
        dict: A dictionary containing the original URL.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT original_url, expiration_time, access_count FROM urls WHERE short_url = ?",
        (short_url,),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Short URL not found")

    original_url, expiration_time, access_count = row

    if is_expired(expiration_time):
        conn.close()
        raise HTTPException(status_code=410, detail="This URL has expired")

    cursor.execute(
        """
        INSERT INTO logs (short_url, access_time, ip_address)
        VALUES (?, ?, ?)
    """,
        (
            short_url,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            request.client.host,
        ),
    )

    cursor.execute(
        """
        UPDATE urls
        SET access_count = access_count + 1
        WHERE short_url = ?
    """,
        (short_url,),
    )
    conn.commit()
    conn.close()

    return {"original_url": original_url}

@app.get("/analytics/{short_url}")
async def get_analytics(short_url: str):
    """
    Endpoint to retrieve analytics for a short URL.

    Args:
        short_url (str): The shortened URL.

    Returns:
        dict: A dictionary containing the original URL, access count, expiration time, and logs.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT original_url, access_count, expiration_time FROM urls WHERE short_url = ?",
        (short_url,),
    )
    url_data = cursor.fetchone()

    if not url_data:
        conn.close()
        raise HTTPException(status_code=404, detail="Short URL not found")

    original_url, access_count, expiration_time = url_data

    cursor.execute(
        "SELECT access_time, ip_address FROM logs WHERE short_url = ?", (short_url,)
    )
    logs = [{"access_time": log[0], "ip_address": log[1]} for log in cursor.fetchall()]
    conn.close()

    return {
        "original_url": original_url,
        "short_url": f"https://short.ly/{short_url}",
        "access_count": access_count,
        "expiration_time": expiration_time,
        "logs": logs,
    }
