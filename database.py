# database.py
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Optional, Dict, List
import os
import json

# Initialize Firebase
cred_json = os.getenv("FIREBASE_CREDENTIALS")

if cred_json:
    # Production: credentials from environment variable
    cred_dict = json.loads(cred_json)
    cred = credentials.Certificate(cred_dict)
else:
    # Local development: credentials from file
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
    cred = credentials.Certificate(cred_path)

firebase_admin.initialize_app(cred)
db = firestore.client()

class Database:
    """
    This class handles ALL database operations.
    Think of it as your app's memory - it remembers everything.
    """
   
    # ============== USER OPERATIONS ==============
   
    @staticmethod
    def create_user(username: str, email: str, hashed_password: str) -> Dict:
        """
        Save a new user to Firestore
       
        Creates structure:
        users/
          └── user_abc123/
              ├── username: "john_doe"
              ├── email: "john@example.com"
              ├── password: "hashed_password_here"
              └── created_at: timestamp
        """
        user_ref = db.collection('users').document()
        user_data = {
            'user_id': user_ref.id,
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        user_ref.set(user_data)
        print(f"✅ Created user: {username}")
        return user_data
   
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict]:
        """Find a user by their username"""
        users = db.collection('users').where('username', '==', username).limit(1).get()
        if users:
            user = users[0]
            return {**user.to_dict(), 'doc_id': user.id}
        return None
   
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Find a user by their email"""
        users = db.collection('users').where('email', '==', email).limit(1).get()
        if users:
            user = users[0]
            return {**user.to_dict(), 'doc_id': user.id}
        return None
   
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Find a user by their ID (used for auth token verification)"""
        user = db.collection('users').document(user_id).get()
        if user.exists:
            return {**user.to_dict(), 'doc_id': user.id}
        return None
   
    # ============== GOAL OPERATIONS ==============
   
    @staticmethod
    def save_goal(user_id: str, goal_text: str, context: Dict) -> str:
        """
        Save a user's fitness goal
       
        Example: User types "I want to do a pull-up in 3 months"
        This saves it under their account:
       
        users/
          └── user_abc123/
              └── goals/
                  └── goal_xyz789/
                      ├── goal_text: "I want to do a pull-up..."
                      ├── context: {days_per_week: 3, ...}
                      └── created_at: timestamp
        """
        goal_ref = db.collection('users').document(user_id).collection('goals').document()
        goal_data = {
            'goal_id': goal_ref.id,
            'goal_text': goal_text,
            'context': context,
            'created_at': datetime.now(),
            'status': 'active'
        }
        goal_ref.set(goal_data)
        print(f"✅ Saved goal for user {user_id}: {goal_text[:50]}...")
        return goal_ref.id
   
    @staticmethod
    def get_user_goals(user_id: str) -> List[Dict]:
        """Get ALL goals a user has ever set (newest first)"""
        goals = db.collection('users').document(user_id).collection('goals')\
                  .order_by('created_at', direction=firestore.Query.DESCENDING)\
                  .get()
       
        result = [{**goal.to_dict(), 'doc_id': goal.id} for goal in goals]
        print(f"📋 Retrieved {len(result)} goals for user {user_id}")
        return result
   
    @staticmethod
    def get_goal_by_id(user_id: str, goal_id: str) -> Optional[Dict]:
        """Get a specific goal"""
        goal = db.collection('users').document(user_id)\
                 .collection('goals').document(goal_id).get()
        if goal.exists:
            return {**goal.to_dict(), 'doc_id': goal.id}
        return None
   
    # ============== WORKOUT PLAN OPERATIONS ==============
   
    @staticmethod
    def save_workout_plan(user_id: str, goal_id: str, plan: Dict) -> str:
        """
        Save the workout plan JSON from Gemini
       
        This saves the ENTIRE JSON response from Gemini AI:
       
        users/
          └── user_abc123/
              └── workout_plans/
                  └── plan_def456/
                      ├── goal_id: "goal_xyz789"
                      ├── plan: {
                      │     weeks: [...],
                      │     exercises: [...],
                      │     ... (full Gemini response)
                      │   }
                      └── created_at: timestamp
        """
        plan_ref = db.collection('users').document(user_id)\
                     .collection('workout_plans').document()
        plan_data = {
            'plan_id': plan_ref.id,
            'goal_id': goal_id,
            'plan': plan,  # This is the full JSON from Gemini
            'created_at': datetime.now()
        }
        plan_ref.set(plan_data)
       
        weeks_count = len(plan.get('weeks', []))
        print(f"✅ Saved workout plan ({weeks_count} weeks) for user {user_id}")
        return plan_ref.id
   
    @staticmethod
    def get_workout_plans_for_goal(user_id: str, goal_id: str) -> List[Dict]:
        """Get all workout plans for a specific goal"""
        plans = db.collection('users').document(user_id)\
                  .collection('workout_plans')\
                  .where('goal_id', '==', goal_id)\
                  .order_by('created_at', direction=firestore.Query.DESCENDING)\
                  .get()
       
        result = [{**plan.to_dict(), 'doc_id': plan.id} for plan in plans]
        print(f"📋 Retrieved {len(result)} plans for goal {goal_id}")
        return result
   
    @staticmethod
    def get_all_user_plans(user_id: str) -> List[Dict]:
        """Get ALL workout plans for a user (across all goals)"""
        plans = db.collection('users').document(user_id)\
                  .collection('workout_plans')\
                  .order_by('created_at', direction=firestore.Query.DESCENDING)\
                  .get()
       
        result = [{**plan.to_dict(), 'doc_id': plan.id} for plan in plans]
        print(f"📋 Retrieved {len(result)} total plans for user {user_id}")
        return result
   
    # ============== SESSION TRACKING ==============
   
    @staticmethod
    def log_session(user_id: str, plan_id: str, session_data: Dict) -> str:
        """
        Track when user completes or skips a workout
       
        users/
          └── user_abc123/
              └── session_logs/
                  └── session_ghi789/
                      ├── plan_id: "plan_def456"
                      ├── completed: true/false
                      ├── date: timestamp
                      └── notes: "Felt great!"
        """
        session_ref = db.collection('users').document(user_id)\
                        .collection('session_logs').document()
        log_data = {
            'session_id': session_ref.id,
            'plan_id': plan_id,
            'date': datetime.now(),
            **session_data
        }
        session_ref.set(log_data)
       
        status = "completed" if session_data.get('completed') else "skipped"
        print(f"✅ Logged session ({status}) for user {user_id}")
        return session_ref.id
   
    @staticmethod
    def get_user_sessions(user_id: str, plan_id: Optional[str] = None) -> List[Dict]:
        """Get session history (optionally filter by plan)"""
        query = db.collection('users').document(user_id).collection('session_logs')
       
        if plan_id:
            query = query.where('plan_id', '==', plan_id)
       
        sessions = query.order_by('date', direction=firestore.Query.DESCENDING).get()
        result = [{**session.to_dict(), 'doc_id': session.id} for session in sessions]
        print(f"📋 Retrieved {len(result)} sessions for user {user_id}")
        return result