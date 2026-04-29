from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import redis
import uuid
import json
import hashlib
import random
from database import SessionLocal, JobRecord, engine, Base

# Initialize Tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS for the Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Redis
r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    job_id = str(uuid.uuid4())
    
    repo = data.get("repository", "unknown-repo")
    lang = data.get("language", "python")
    
    # 1. Importance (Priority 1, 2, or 3)
    priority = data.get("priority", random.randint(1, 3))
    
    # 2. Generate Code Hash and File Size (Simulating a commit)
    # We hash the repo name + job_id to create a unique fingerprint
    fake_payload = f"{repo}-{job_id}-{lang}"
    code_hash = hashlib.md5(fake_payload.encode()).hexdigest()
    file_size = random.randint(100, 5000) # Size in KB

    # 3. Save to Postgres
    db = SessionLocal()
    new_job = JobRecord(
        id=job_id,
        repo=repo,
        language=lang,
        status="QUEUED",
        priority=priority,
        file_size=file_size,
        code_hash=code_hash
    )
    db.add(new_job)
    db.commit()
    db.close()
    
    # 4. Push to Redis Queue
    r.lpush("jenkins_queue", json.dumps({"id": job_id, "language": lang, "repo": repo}))
    
    print(f"📦 Job {job_id[:8]} Queued | P:{priority} | Hash:{code_hash[:6]}")
    return {"status": "queued", "job_id": job_id, "hash": code_hash}

@app.get("/jobs")
async def get_jobs():
    db = SessionLocal()
    jobs = db.query(JobRecord).all()
    db.close()
    return jobs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)