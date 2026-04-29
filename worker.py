import redis
import json
import time
import random
import sys
import os
from database import SessionLocal, JobRecord

# Force logs to show up immediately in Docker terminal
print("🔄 Initializing Worker...", flush=True)

# 1. Connect to Redis (Using 'redis' host for Docker networking)
try:
    r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    # Ping to check if connection is actually live
    r.ping()
    print("✅ Connected to Redis", flush=True)
except Exception as e:
    print(f"❌ Redis Connection Error: {e}", flush=True)
    sys.exit(1)

print("🚀 Worker started. Listening for ANY job in 'jenkins_queue'...", flush=True)

while True:
    try:
        # 2. 'brpop' waits (blocks) until a job is available
        # It returns a tuple: (list_name, message)
        result = r.brpop("jenkins_queue", timeout=5)
        
        if not result:
            continue

        _, message = result
        job = json.loads(message)
        
        job_id = job.get('id')
        repo_name = job.get('repo')
        language = job.get('language', 'unknown')

        print(f"🛠️  [STARTING] Job {job_id} | Repo: {repo_name} | Type: {language}", flush=True)

        # 3. Update Database: Status -> RUNNING
        db = SessionLocal()
        try:
            db.query(JobRecord).filter(JobRecord.id == job_id).update({"status": "RUNNING"})
            db.commit()

            # 4. Simulate the Build Process (5 to 12 seconds)
            build_duration = random.randint(5, 12)
            time.sleep(build_duration) 

            # 5. Update Database: Status -> COMPLETED
            db.query(JobRecord).filter(JobRecord.id == job_id).update({"status": "COMPLETED"})
            db.commit()
            print(f"✅ [FINISHED] Job {job_id} in {build_duration}s", flush=True)
            
        except Exception as db_e:
            print(f"❌ Database Error during job {job_id}: {db_e}", flush=True)
            db.rollback()
        finally:
            db.close()

    except Exception as e:
        print(f"⚠️ Worker Loop Error: {e}", flush=True)
        time.sleep(2) # Prevent rapid-fire crashing

    #new changes made