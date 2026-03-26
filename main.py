#   
from fastapi import FastAPI, HTTPException  
from fastapi.middleware.cors import CORSMiddleware  
from pymongo import MongoClient  
from pydantic import BaseModel  
from datetime import datetime  
import os  
  
# ================= APP =================  
app = FastAPI(title="Smart Queue Management System")  
  
# ================= CORS =================  
app.add_middleware(  
    CORSMiddleware,  
    allow_origins=["*"],  # allow all (for production, restrict this)  
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)  
  
# ================= DATABASE =================  
MONGO_URL = os.getenv("mongodb+srv://ankushgupta4747_db_user:m7VD2QjSzpReH1kW@ankush7.o7ginho.mongodb.net/smart_queue_db?retryWrites=true&w=majority&appName=Ankush7")  
  
if not MONGO_URL:  
    raise Exception("MONGO_URL not set in environment variables")  
  
client = MongoClient(MONGO_URL)  
db = client["queue_db"]  
  
# ================= MODELS =================  
class User(BaseModel):  
    email: str  
    password: str  
    role: str = "user"  
  
class Token(BaseModel):  
    user_email: str  
    service: str  
  
  
# ================= ROOT =================  
@app.get("/")  
def root():  
    return {"message": "Backend Running Successfully"}  
  
  
# ================= REGISTER =================  
@app.post("/register")  
def register(user: User):  
  
    existing = db.users.find_one({"email": user.email})  
  
    if existing:  
        raise HTTPException(status_code=400, detail="User already exists")  
  
    db.users.insert_one(user.dict())  
  
    return {"message": "User Registered Successfully"}  
  
  
# ================= LOGIN =================  
@app.post("/login")  
def login(user: User):  
  
    existing_user = db.users.find_one({"email": user.email})  
  
    if not existing_user or existing_user["password"] != user.password:  
        raise HTTPException(status_code=401, detail="Invalid Credentials")  
  
    return {  
        "message": "Login Successful",  
        "role": existing_user.get("role", "user")  
    }  
  
  
# ================= BOOK TOKEN =================  
@app.post("/book")  
def book_token(token: Token):  
  
    total_tokens = db.tokens.count_documents({})  
  
    waiting_tokens = db.tokens.count_documents({  
        "service": token.service,  
        "status": "waiting"  
    })  
  
    token_number = total_tokens + 1  
    estimated_time = waiting_tokens * 5  # 5 mins per user  
  
    token_data = {  
        "user_email": token.user_email,  
        "service": token.service,  
        "token_number": token_number,  
        "status": "waiting",  
        "estimated_time": estimated_time,  
        "created_at": datetime.utcnow().isoformat()  
    }  
  
    db.tokens.insert_one(token_data)  
  
    return {  
        "message": "Token booked successfully",  
        "token_number": token_number,  
        "estimated_time": estimated_time  
    }  
  
  
# ================= GET ALL TOKENS =================  
@app.get("/tokens")  
def get_tokens():  
  
    tokens = list(db.tokens.find({}))  
  
    for token in tokens:  
        token["_id"] = str(token["_id"])  
  
    return tokens  
  
  
# ================= UPDATE TOKEN =================  
@app.put("/update/{token_number}")  
def update_token(token_number: int, status: str):  
  
    result = db.tokens.update_one(  
        {"token_number": token_number},  
        {"$set": {"status": status}}  
    )  
  
    if result.matched_count == 0:  
        raise HTTPException(status_code=404, detail="Token not found")  
  
    return {"message": "Token Updated Successfully"}  
  
  
# ================= NOW SERVING =================  
@app.get("/now-serving")  
def now_serving():  
  
    token = db.tokens.find_one(  
        {"status": "served"},  
        sort=[("token_number", -1)]  
    )  
  
    return {"now_serving": token["token_number"] if token else 0}  
  
  
# ================= QUEUE DISPLAY =================  
@app.get("/queue-display")  
def queue_display():  
  
    served = db.tokens.find_one(  
        {"status": "served"},  
        sort=[("token_number", -1)]  
    )  
  
    next_token = db.tokens.find_one(  
        {"status": "waiting"},  
        sort=[("token_number", 1)]  
    )  
  
    return {  
        "now_serving": served["token_number"] if served else 0,  
        "next_token": next_token["token_number"] if next_token else 0  
    }  
