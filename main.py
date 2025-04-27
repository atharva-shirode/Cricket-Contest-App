from fastapi import FastAPI, HTTPException, Depends, status, Response
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from sqlalchemy import func, desc
from PIL import Image, ImageDraw, ImageFont
import io
from database import engine, SessionLocal, create_tables, UserDB, OTPDB, ScoreDB  
from schemas import (
    UserRegistration,
    User,
    ScoreInput,
    Score,
    UserList,
    OTPVerification,
    WeeklyScoresResponse,
)
import random
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR) 

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    create_tables()
    print("Database tables created (on startup)")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_otp():
    return "1234"


def send_otp(phone_number, otp):
    print(f"Simulating sending OTP '{otp}' to {phone_number}")


@app.post("/register/", response_model=User)
async def register_user(user_data: UserRegistration, db: Session = Depends(get_db)):
    """
    Registers a new user, including OTP generation and handling.
    """
    try:
        db_user_exists_phone = (
            db.query(UserDB).filter(UserDB.phone_number == user_data.phone_number).first()
        )
        if db_user_exists_phone:
            raise HTTPException(status_code=400, detail="Phone number already registered.")

        db_user_exists_email = (
            db.query(UserDB).filter(UserDB.email == user_data.email).first()
        )
        if db_user_exists_email:
            raise HTTPException(status_code=400, detail="Email already registered.")

        new_user = UserDB(
            phone_number=user_data.phone_number,
            name=user_data.name,
            date_of_birth=user_data.date_of_birth,
            email=user_data.email,
            is_verified=0,  # Start with is_verified = 0
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)  # Refresh to get the new user.id

        # Generate OTP and set expiry
        otp = generate_otp()
        expiry = datetime.utcnow() + timedelta(seconds=60)  # OTP expires in 60 seconds

        # Check for existing OTP for the user and delete it.
        existing_otp = db.query(OTPDB).filter(OTPDB.user_id == new_user.id).first()
        if existing_otp:
            db.delete(existing_otp)
            db.commit()

        db_otp = OTPDB(
            user_id=new_user.id, phone_number=user_data.phone_number, otp=otp, expiry=expiry
        )
        db.add(db_otp)
        db.commit()
        send_otp(user_data.phone_number, otp)  # Send the OTP

        return User(  # Return the user data, including the new user_id
            user_id=new_user.id,
            name=new_user.name,
            phone_number=new_user.phone_number,
            date_of_birth=new_user.date_of_birth,
            email=new_user.email,
            is_verified=new_user.is_verified,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.post("/verify-otp/")
async def verify_otp(verification_data: OTPVerification, db: Session = Depends(get_db)):
    db_user = (
        db.query(UserDB).filter(UserDB.phone_number == verification_data.phone_number).first()
    )
    if not db_user:
        raise HTTPException(
            status_code=404, detail="User not found for this phone number."
        )

    db_otp = (
        db.query(OTPDB)
        .filter(OTPDB.user_id == db_user.id)
        .order_by(desc(OTPDB.expiry))
        .first()
    )

    if not db_otp:
        raise HTTPException(
            status_code=404,
            detail="OTP not found for this phone number. Request a new one.",
        )

    if db_otp.expiry < datetime.utcnow():
        db.delete(db_otp)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

    if db_otp.otp != verification_data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    db_user.is_verified = 1
    db.delete(db_otp)
    db.commit()
    db.refresh(db_user)
    return {"message": "Phone number verified successfully!"}


@app.get("/users/", response_model=UserList)
async def get_all_users(db: Session = Depends(get_db)):
    """
    Retrieves all users from the database.
    """
    try:
        users = db.query(UserDB).all()
        # Convert SQLAlchemy UserDB objects to Pydantic User objects
        pydantic_users = [
            User(
                user_id=user.id,
                name=user.name,
                phone_number=user.phone_number,
                date_of_birth=user.date_of_birth,
                email=user.email,
                is_verified=user.is_verified,
            )
            for user in users
        ]
        return UserList(users=pydantic_users)
    except Exception as e:
        logging.error(f"Error in get_all_users: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**db_user.__dict__)


@app.post("/request-otp/{phone_number}")
async def request_otp(phone_number: str, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.phone_number == phone_number).first()
    if not db_user:
        raise HTTPException(
            status_code=404, detail="User not found for this phone number."
        )

    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(seconds=60)
    db_otp = OTPDB(
        user_id=db_user.id, phone_number=phone_number, otp=otp, expiry=expiry
    )
    db.add(db_otp)
    db.commit()
    send_otp(phone_number, otp)
    return {"message": f"OTP sent to {phone_number}."}


@app.post("/scores/", response_model=Score, status_code=status.HTTP_201_CREATED)
async def add_score(score_input: ScoreInput, db: Session = Depends(get_db)):
    """
    Adds a new score for a user, with validation.
    """
    try:
        # Check if the user exists
        db_user = db.query(UserDB).filter(UserDB.id == score_input.user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check the number of scores for the user today
        today = datetime.utcnow().date()
        score_count = (
            db.query(ScoreDB)
            .filter(
                ScoreDB.user_id == score_input.user_id, func.date(ScoreDB.timestamp) == today
            )
            .count()
        )

        if score_count >= 3:
            raise HTTPException(
                status_code=400, detail="Maximum 3 scores allowed per day"
            )

        # Create and add the new score
        new_score = ScoreDB(user_id=score_input.user_id, score=score_input.score)
        db.add(new_score)
        db.commit()
        db.refresh(new_score)
        return new_score
    except Exception as e:
        db.rollback()
        raise


@app.get("/scores/rank/{user_id}")
async def get_user_score_and_rank(user_id: int, db: Session = Depends(get_db)): #as an image didnt add any return type
    """
    Retrieves the user's rank, total score for today, and today's date,
    and returns all in  a image format.
    """
    try:
        today = datetime.utcnow().date()

        # Get the user's score for today
        user_score_obj = (
            db.query(ScoreDB)
            .filter(ScoreDB.user_id == user_id, func.date(ScoreDB.timestamp) == today)
            .first()
        )
        if not user_score_obj:
            raise HTTPException(
                status_code=404, detail="No score found for this user today"
            )
        user_score = user_score_obj.score

        # Get all scores for today
        scores_today = (
            db.query(ScoreDB)
            .filter(func.date(ScoreDB.timestamp) == today)
            .order_by(desc(ScoreDB.score))
            .all()
        )

        # Calculate the user's rank
        user_rank = 0
        for i, score_obj in enumerate(scores_today):
            if score_obj.user_id == user_id:
                user_rank = i + 1
                break
        if user_rank == 0:
            raise HTTPException(
                status_code=404, detail="User not found in todays score"
            )

        # Create a new image
        img = Image.new("RGB", (400, 300), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Load a font
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except OSError:
            font = ImageFont.load_default()

        text_color = (0, 0, 0)
        draw.text((20, 20), f"Today's Score", font=font, fill=text_color)
        draw.text((20, 80), f"Date: {today.strftime('%d %B %Y')}", font=font, fill=text_color)
        draw.text((20, 140), f"Your Rank: {user_rank}", font=font, fill=text_color)
        draw.text((20, 200), f"Your Score: {user_score}", font=font, fill=text_color)

        # Save the image to a BytesIO object
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)  # Reset the pointer to the beginning

        # Return the image as a response
        return Response(content=img_bytes.getvalue(), media_type="image/png")
    except Exception as e:
        raise


@app.get("/scores/weekly/{user_id}", response_model=WeeklyScoresResponse)
async def get_weekly_scores(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the weekly scores for a given user.
    """
    try:
        today = datetime.utcnow().date()
        start_of_week = today - timedelta(days=today.weekday())  # Start of the current week (Monday)
        end_of_week = start_of_week + timedelta(days=6)  # End of the current week (Sunday)

        # Fetch scores for the user within the current week
        weekly_scores = (
            db.query(ScoreDB.score)
            .filter(
                ScoreDB.user_id == user_id,
                ScoreDB.timestamp >= start_of_week,
                ScoreDB.timestamp <= end_of_week,
            )
            .order_by(ScoreDB.timestamp)
            .all()  # Order by timestamp
        )

        # Extract the score values from the query result
        scores = [score_obj.score for score_obj in weekly_scores]

        return WeeklyScoresResponse(success= True if len(scores)>0 else False, weekly=scores)
    except Exception as e:
        raise

