# main.py
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import traceback

# Import after FastAPI setup
from database import Database
from auth_service import hash_password, verify_password, create_access_token, decode_access_token
from workout_scheduler import generate_workout_plan
from datetime import timedelta
import datetime

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class GoalRequest(BaseModel):
    goal_text: str
    context: dict

class GeneratePlanRequest(BaseModel):
    user_input: str

# ============== REGISTER ==============
@app.post("/api/register")
async def register(request: RegisterRequest):
    try:
        print(f"📝 Registration attempt for username: {request.username}")
        
        # Check if username exists
        existing_user = Database.get_user_by_username(request.username)
        if existing_user:
            print(f"⚠️ Username already exists: {request.username}")
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Hash password
        hashed_password = hash_password(request.password)
        print(f"🔒 Password hashed successfully")
        
        # Create user
        user_data = Database.create_user(
            username=request.username,
            email=f"{request.username}@placeholder.com",
            hashed_password=hashed_password
        )
        
        print(f"✅ User registered: {request.username}")
        
        return {
            "message": "User created successfully",
            "username": request.username,
            "user_id": user_data['user_id']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# ============== LOGIN ==============
@app.post("/api/login")
async def login(request: LoginRequest):
    try:
        print(f"🔑 Login attempt for username: {request.username}")
        
        # Find user
        user = Database.get_user_by_username(request.username)
        if not user:
            print(f"⚠️ User not found: {request.username}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify password
        if not verify_password(request.password, user['password']):
            print(f"⚠️ Incorrect password for: {request.username}")
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        # Create token
        access_token = create_access_token(
            data={"user_id": user['user_id'], "username": user['username']},
            expires_delta=timedelta(days=30)
        )
        
        print(f"✅ User logged in: {request.username}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user['user_id'],
            "username": user['username']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

# ============== SAVE GOAL ==============
@app.post("/api/save_goal")
async def save_goal(request: GoalRequest, authorization: Optional[str] = Header(None)):
    try:
        print(f"💾 Saving goal...")
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("user_id")
        
        goal_id = Database.save_goal(
            user_id=user_id,
            goal_text=request.goal_text,
            context=request.context
        )
        
        print(f"✅ Goal saved: {goal_id}")
        
        return {
            "message": "Goal saved successfully",
            "goal_id": goal_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Save goal error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to save goal: {str(e)}")

# ============== GENERATE WORKOUT PLAN ==============
@app.post("/api/generate_plan")
async def generate_plan(request: GeneratePlanRequest, authorization: Optional[str] = Header(None)):
    try:
        print(f"🏋️ Generating workout plan for: {request.user_input}")
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("user_id")
        
        # Generate workout plan using Gemini
        plan = generate_workout_plan(request.user_input)
        
        # Check if there was an error from Gemini
        if "error" in plan:
            print(f"❌ Gemini error: {plan['error']}")
            raise HTTPException(status_code=500, detail=f"AI generation failed: {plan['error']}")
        
        # Check if it's raw text fallback
        if "raw_text" in plan:
            print(f"⚠️ Gemini returned raw text instead of JSON")
            raise HTTPException(status_code=500, detail="AI returned unexpected format")
        
        # Save the plan to database
        plan_id = Database.save_workout_plan(
            user_id=user_id,
            goal_id="generated",  # You can link to actual goal_id if saved
            plan=plan
        )
        
        print(f"✅ Workout plan generated and saved: {plan_id}")
        
        return {
            "plan": plan,
            "plan_id": plan_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Generate plan error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")

# ============== ROOT ENDPOINT ==============
@app.get("/")
async def root():
    return {"message": "Workout API is running! 💪"}
