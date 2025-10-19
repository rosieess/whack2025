# database.py
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Optional, Dict, List
import os
import json

# Initialize Firebase - ONLY ONCE
if not firebase_admin._apps:
    cred_json = os.getenv("FIREBASE_CREDENTIALS")
    
    if cred_json:
        # Production: credentials from environment variable
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # Local development: credentials from file
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
        
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase credentials file not found at {cred_path}. "
                "Please download it from Firebase Console."
            )
        
        cred = credentials.Certificate(cred_path)
    
    firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized successfully")

db = firestore.client()

class Database:
    """
    This class handles ALL database operations.
    """
   
    # ============== USER OPERATIONS ==============
   
    @staticmethod
    def create_user(username: str, email: str, hashed_password: str) -> Dict:
        """Save a new user to Firestore"""
        try:
            user_ref = db.collection('users').document()
            user_data = {
                'user_id': user_ref.id,
                'username': username,
                'email': email,
                'password': hashed_password,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            user_ref.set(user_data)
            print(f"✅ Created user: {username} with ID: {user_ref.id}")
            
            # Return the data with the ID
            user_data['user_id'] = user_ref.id
            return user_data
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            raise
   
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict]:
        """Find a user by their username"""
        try:
            users = db.collection('users').where('username', '==', username).limit(1).get()
            if users:
                user = users[0]
                user_data = user.to_dict()
                user_data['doc_id'] = user.id
                return user_data
            return None
        except Exception as e:
            print(f"❌ Error getting user by username: {e}")
            raise
   
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Find a user by their email"""
        try:
            users = db.collection('users').where('email', '==', email).limit(1).get()
            if users:
                user = users[0]
                user_data = user.to_dict()
                user_data['doc_id'] = user.id
                return user_data
            return None
        except Exception as e:
            print(f"❌ Error getting user by email: {e}")
            raise
   
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Find a user by their ID"""
        try:
            user = db.collection('users').document(user_id).get()
            if user.exists:
                user_data = user.to_dict()
                user_data['doc_id'] = user.id
                return user_data
            return None
        except Exception as e:
            print(f"❌ Error getting user by ID: {e}")
            raise
   
    # ============== GOAL OPERATIONS ==============
   
    @staticmethod
    def save_goal(user_id: str, goal_text: str, context: Dict) -> str:
        """Save a user's fitness goal"""
        try:
            goal_ref = db.collection('users').document(user_id).collection('goals').document()
            goal_data = {
                'goal_id': goal_ref.id,
                'goal_text': goal_text,
                'context': context,
                'created_at': firestore.SERVER_TIMESTAMP,
                'status': 'active'
            }
            goal_ref.set(goal_data)
            print(f"✅ Saved goal for user {user_id}: {goal_text[:50]}...")
            return goal_ref.id
        except Exception as e:
            print(f"❌ Error saving goal: {e}")
            raise
   
    @staticmethod
    def get_user_goals(user_id: str) -> List[Dict]:
        """Get ALL goals a user has set"""
        try:
            goals = db.collection('users').document(user_id).collection('goals')\
                      .order_by('created_at', direction=firestore.Query.DESCENDING)\
                      .get()
           
            result = [{**goal.to_dict(), 'doc_id': goal.id} for goal in goals]
            print(f"📋 Retrieved {len(result)} goals for user {user_id}")
            return result
        except Exception as e:
            print(f"❌ Error getting goals: {e}")
            raise
   
    @staticmethod
    def get_goal_by_id(user_id: str, goal_id: str) -> Optional[Dict]:
        """Get a specific goal"""
        try:
            goal = db.collection('users').document(user_id)\
                     .collection('goals').document(goal_id).get()
            if goal.exists:
                goal_data = goal.to_dict()
                goal_data['doc_id'] = goal.id
                return goal_data
            return None
        except Exception as e:
            print(f"❌ Error getting goal by ID: {e}")
            raise
   
    # ============== WORKOUT PLAN OPERATIONS ==============
   
    @staticmethod
    def save_workout_plan(user_id: str, goal_id: str, plan: Dict) -> str:
        """Save the workout plan JSON from Gemini"""
        try:
            plan_ref = db.collection('users').document(user_id)\
                         .collection('workout_plans').document()
            plan_data = {
                'plan_id': plan_ref.id,
                'goal_id': goal_id,
                'plan': plan,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            plan_ref.set(plan_data)
           
            weeks_count = len(plan.get('weeks', []))
            print(f"✅ Saved workout plan ({weeks_count} weeks) for user {user_id}")
            return plan_ref.id
        except Exception as e:
            print(f"❌ Error saving workout plan: {e}")
            raise