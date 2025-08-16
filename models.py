from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Pydantic model for user signup
class UserSignup(BaseModel):
    name: str
    email: str
    password: str
    dob: str
    role: str

class UserLogin(BaseModel):
    email: str
    password: str

# New models for service requests
class ServiceRequest(BaseModel):
    userId: str
    userName: str
    userEmail: str
    serviceType: str
    requirements: str
    cost: float  # Added cost field
    status: str = "pending"
    createdAt: str

class RequestAction(BaseModel):
    caregiverId: str
    caregiverName: str
    caregiverEmail: str