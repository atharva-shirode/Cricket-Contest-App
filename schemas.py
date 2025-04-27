from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional


class UserRegistration(BaseModel):
    name: str = Field(..., title="Full Name")
    phone_number: str = Field(..., title="Phone Number")
    date_of_birth: date = Field(..., title="Date of Birth", description="YYYY-MM-DD")
    email: str = Field(..., title="Email Address")


class User(UserRegistration):
    user_id: int
    is_verified: bool


class ScoreInput(BaseModel):
    user_id: int = Field(..., title="User ID")
    score: int = Field(..., title="Score", ge=50, le=500)


class Score(ScoreInput):
    timestamp: datetime
    id: int


class ScoreRankResponse(BaseModel):
    user_rank: int
    total_score_today: int
    today_date: date
    user_score: int


class UserList(BaseModel):
    users: List[User]


class OTPVerification(BaseModel):
    phone_number: str = Field(..., title="Phone Number")
    otp: str = Field(..., min_length=4, max_length=4, title="OTP")


class WeeklyScoresResponse(BaseModel):
    success: bool
    weekly: List[int]

