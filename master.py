import os, json, redis, psycopg2, uuid, time
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

r = redis.Redis(host='redis', port=6379, db=0)
DB_CONFIG = {"host": "db", "database": "jenkins_db", "user": "user", "password": "password"}

def calculate_effective_priority(data, repo_name, branch):
    # 1. Branch Score: Production gets lower score (higher priority)
    branch_score = 10 if branch in ['main', 'master'] else 50
    
    # 2. File Impact Score: More changes = higher score (lower priority)
    # Counts modified, added, and removed files from the webhook
    files_changed = 0
    if 'commits' in data and len(data['commits']) > 0:
        commit = data['commits'][0]
        files_changed = len(commit.get('added', [])) + len(commit.get('modified', [])) + len(commit.get('removed', []))
    file_impact_score = files_changed * 2 # Penalty of 2 per file changed
    
    # 3. Aging Score: 0 for new arrivals. 
    # (In a real system, a background task would decrease this over time)
    aging_score = 0
    
    # 4. Conflict Score: Penalty if the repo is already busy
    conflict_score = 0
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM jobs WHERE repo = %s AND status IN ('QUEUED', 'RUNNING')",
            (repo_name,)
        )
        count = cur.fetchone()[0]
        if count > 0:
            conflict_score = 20 # Add penalty if a build for this repo is active
        cur.close()
        conn.close()
    except:
        pass # Fallback if DB is busy

    effective_priority = branch_score + file_impact_score + aging_score + conflict_score
    return int(effective_priority)

@app.post("/webhook")
async def github_webhook(request: Request):
    data = await request.json()
    if 'ref' not in data: return {"status": "success"}

    try:
        job_id = str(uuid.uuid4())[:8]
        repo_name = data['repository']['name']
        branch = data['ref'].split('/')[-1]
        
        # Calculate the new Effective Priority
        priority = calculate_effective_priority(data, repo_name, branch)
        
        task = {"id": job_id, "repo": repo_name, "branch": branch, "status": "QUEUED"}

        # Push to Redis with the new calculated priority
        r.zadd("jenkins_priority_queue", {json.dumps(task): priority})

        # Save to DB
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO jobs (id, repo, status, priority) VALUES (%s, %s, %s, %s)",
            (job_id, repo_name, "QUEUED", priority)
        )
        conn.commit()
        cur.close()
        conn.close()

        return {"status": "queued", "id": job_id, "effective_priority": priority}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error"}

@app.get("/api/build-history")
async def get_build_history():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 10;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"status": "success", "data": rows}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import asyncio

async def aging_daemon():
    """Background task that ages jobs in Redis every minute."""
    while True:
        try:
            jobs = r.zrange("jenkins_priority_queue", 0, -1)
            for job in jobs:
                # Decrease score by 2 every minute
                r.zincrby("jenkins_priority_queue", -2, job)
            if jobs:
                print(f"📉 Aged {len(jobs)} jobs in queue.")
        except Exception as e:
            print(f"Aging error: {e}")
        
        await asyncio.sleep(60) # Wait 1 minute

@app.on_event("startup")
async def startup_event():
    # Start the aging process in the background
    asyncio.create_task(aging_daemon())    