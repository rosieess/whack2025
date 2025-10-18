from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from workout_scheduler import generate_workout_plan

app = FastAPI(title="AI Fitness Planner API")

# Allow mobile apps (Flutter) to call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input schema
class GoalRequest(BaseModel):
    user_input: str

@app.get("/")
def home():
    return {"message": "AI Fitness Planner API running"}

@app.post("/api/generate_plan")
async def generate_plan(req: GoalRequest):
    """
    Accepts user_input and returns a structured workout plan from Gemini.
    """
    print(f"\n🎯 Received goal from Flutter app: {req.user_input}\n")
    
    plan = generate_workout_plan(req.user_input)
    
    print(f"✅ Generated plan with {len(plan.get('weeks', []))} weeks\n")
    
    return {"plan": plan}