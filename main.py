from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from models import UserSignup, UserLogin, ServiceRequest, RequestAction
from bson import ObjectId
from datetime import datetime

# Load environment variables
load_dotenv()

# Create FastAPI instance
app = FastAPI(
    title="ElderCare API",
    description="API for elderly care management system",
    version="1.0.0"
)

# Configure CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "eldercare_db")

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the ElderCare API"}

# Signup endpoint with email uniqueness check
@app.post("/signup")
async def signup(user: UserSignup):
    try:
        # Check if email already exists
        existing_user = await db.users.find_one({"email": user.email})
        
        if existing_user:
            raise HTTPException(
                status_code=409,  # 409 Conflict status code
                detail="Email already registered. Please use a different email or login to your existing account."
            )
        
        # If email doesn't exist, create new user
        user_data = {
            "name": user.name,
            "email": user.email,
            "password": user.password,  # In production, ensure to hash passwords
            "dob": user.dob,
            "role": user.role
        }
        
        result = await db.users.insert_one(user_data)
        
        # Return success response with document id
        if result.acknowledged:
            return {"message": "Account created successfully!"}
        else:
            raise HTTPException(status_code=500, detail="Signup failed")
            
    except HTTPException:
        # Re-raise HTTP exceptions (like email already exists)
        raise
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Signup failed due to server error")

# Login endpoint
@app.post("/login")
async def login(user: UserLogin):
    try:
        # Find user by email
        existing_user = await db.users.find_one({"email": user.email})
        
        if not existing_user:
            raise HTTPException(
                status_code=404,  # 404 Not Found status code
                detail="User not found. Please check your email or sign up."
            )
        
        # Check password (in production, ensure to hash and compare passwords securely)
        if existing_user["password"] != user.password:
            raise HTTPException(
                status_code=401,  # 401 Unauthorized status code
                detail="Incorrect password. Please try again."
            )
        
        # Return user data with document ID
        return {
            "message": "Login successful!",
            "user": {
                "id": str(existing_user["_id"]),
                "name": existing_user["name"],
                "email": existing_user["email"],
                "role": existing_user["role"],
                "dob": existing_user["dob"]
            }
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed due to server error")

# Service request endpoints
@app.post("/service-request")
async def create_service_request(request: ServiceRequest):
    """Create a new service request"""
    try:
        request_data = {
            "userId": request.userId,
            "userName": request.userName,
            "userEmail": request.userEmail,
            "serviceType": request.serviceType,
            "requirements": request.requirements,
            "cost": request.cost,  # Added cost field
            "status": request.status,
            "createdAt": request.createdAt,
            "updatedAt": datetime.now().isoformat()
        }
        
        result = await db.service_requests.insert_one(request_data)
        
        if result.acknowledged:
            return {
                "message": "Service request created successfully!", 
                "requestId": str(result.inserted_id)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create service request")
            
    except Exception as e:
        print(f"Service request error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create service request: {str(e)}")

@app.get("/service-requests/pending")
async def get_pending_requests():
    """Get all pending service requests for caregivers"""
    try:
        cursor = db.service_requests.find({"status": "pending"}).sort("createdAt", -1)
        requests = []
        
        async for request in cursor:
            request["id"] = str(request["_id"])
            del request["_id"]
            requests.append(request)
        
        return {"requests": requests}
        
    except Exception as e:
        print(f"Error fetching requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch service requests")

@app.patch("/service-request/{request_id}/{action}")
async def handle_request_action(request_id: str, action: str, caregiver_data: RequestAction):
    """Approve or reject a service request"""
    try:
        if action not in ["approve", "reject"]:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")
        
        # Validate ObjectId
        try:
            obj_id = ObjectId(request_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid request ID format")
        
        status = "approved" if action == "approve" else "rejected"
        
        update_data = {
            "status": status,
            "caregiverId": caregiver_data.caregiverId,
            "caregiverName": caregiver_data.caregiverName,
            "caregiverEmail": caregiver_data.caregiverEmail,
            "processedAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        
        result = await db.service_requests.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        if result.matched_count:
            return {"message": f"Request {status} successfully!"}
        else:
            raise HTTPException(status_code=404, detail="Service request not found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process service request: {str(e)}")

# Test endpoint to verify the service is running
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)