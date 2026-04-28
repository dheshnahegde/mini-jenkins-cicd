import redis
import json
import time
import random
import sys
from database import SessionLocal, JobRecord

# 1. Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    print("✅ Connected to Redis")
except Exception as e:
    print(f"❌ Redis Connection Error: {e}")
    sys.exit(1)

# 2. Get Worker Type from Command Line (e.g., python worker.py python)
worker_type = sys.argv[1] if len(sys.argv) > 1 else "python"
print(f"🚀 Worker started. Specialization: {worker_type.upper()}")
print("Waiting for jobs...")

while True:
    # 3. 'brpop' waits (blocks) until a job is available in the list
    # Result is a tuple: (list_name, message)
    result = r.brpop("jenkins_queue")
    if not result:
        continue

    _, message = result
    job = json.loads(message)
    
    # 4. Criteria-based assignment (Check if this worker should handle this job)
    if job['language'] == worker_type:
        job_id = job['id']
        repo_name = job['repo']

        print(f"🛠️  [STARTING] Job {job_id} for {repo_name}")

        # 5. Update Database: Status -> RUNNING
        db = SessionLocal()
        db.query(JobRecord).filter(JobRecord.id == job_id).update({"status": "RUNNING"})
        db.commit()

        # 6. Simulate the Build Process
        # Adding randomness in execution time as per requirements
        build_duration = random.randint(5, 12)
        time.sleep(build_duration) 

        # 7. Update Database: Status -> COMPLETED
        db.query(JobRecord).filter(JobRecord.id == job_id).update({"status": "COMPLETED"})
        db.commit()
        db.close()

        print(f"✅ [FINISHED] Job {job_id} in {build_duration}s")
    
    else:
        # 8. Not my language? Put it back in the queue for another worker!
        print(f"⏭️  [SKIPPING] {job['language']} job. Returning to queue...")
        r.lpush("jenkins_queue", message)
        # Small sleep to prevent this worker from immediately re-grabbing the same job
        time.sleep(1)