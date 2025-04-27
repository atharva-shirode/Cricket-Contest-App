# Cricket-Contest-App

 # FastAPI User Management API

## Overview

This project is a FastAPI-based API for managing users, including registration, OTP verification, and score tracking. It uses SQLAlchemy for database interactions and includes features like user ranking and weekly score retrieval.

## Features

* **User Registration:** Registers new users with name, phone number, date of birth, and email.
* **OTP Verification:** Sends and verifies OTPs for phone number verification.
* **User Management:** Retrieves user information.
* **Score Tracking:** Adds and retrieves user scores, including daily score limits.
* **Ranking:** Calculates user rank based on daily scores.
* **Weekly Scores:** Retrieves users' weekly scores.
* **Database:** Uses SQLite for data storage.

## Technologies Used

* [FastAPI](https://fastapi.tiangolo.com/):  A modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.
* [Uvicorn](https://www.uvicorn.org/):  An ASGI server for running Python web applications.
* [SQLAlchemy](https://www.sqlalchemy.org/):  The Python SQL Toolkit and Object Relational Mapper.
* [Pillow](https://pillow.readthedocs.io/):  Adds support for opening, manipulating, and saving many different image file formats.
* [Logging](https://docs.python.org/3/library/logging.html): Provides a flexible framework for event logging.

## Requirements

* Python 3.9+
* The following Python packages:

    ```text
    fastapi
    uvicorn
    sqlalchemy
    Pillow
    logging
    ```

## Installation

1.  Clone the repository.
2.  Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

## Database Setup

The application uses an SQLite database (`users.db`). The database file will be created in the project directory.  The database schema is defined in `database.py` and is automatically created on startup.

## Running the Application

1.  Run the application using Uvicorn:

    ```bash
     uvicorn main:app --reload
    ```

    This will start the server at `http://localhost:8000`.
2. Add /docs to the above mentioned URL to utilize the Swagger UI and openapi documentation provided by fast_api and test the apis accordingly.
   ```bash
   http://localhost:8000/docs
   ```

## API Endpoints

* **POST /register/**: Register a new user.
* **POST /verify-otp/**: Verify OTP for a user.
* **GET /users/**: Get all users.
* **GET /users/{user_id}**: Get a specific user.
* **POST /request-otp/{phone_number}**: Request a new OTP.
* **POST /scores/**: Add a new score for a user.
* **GET /scores/rank/{user_id}**: Get a user's score and rank for today.
* **GET /scores/weekly/{user_id}**: Get a user's weekly scores.

## Project Structure

├── main.py # Main FastAPI or Entry Point

├── schemas.py # The api schema and pydantic validation

├── database.py # The database table classes for sqlalchemy orm
