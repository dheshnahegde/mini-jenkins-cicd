import redis
import json
import time
import subprocess
from database import SessionLocal, JobRecord

# 1. Initialize Redis (Fixed 'r' not defined error)
r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

print("🚀 Worker started. Waiting for priority jobs...", flush=True)

while True:
    # 2. Pull the lowest score (highest priority) from the Sorted Set
    # Matches the queue name used in master.py
    result = r.bzpopmin("jenkins_priority_queue", timeout=5)
    
    if result:
        _, job_data, score = result
        job = json.loads(job_data)
        job_id = job['id']
        
        print(f"🛠️ [WORKING] Job ID: {job_id} | Repo: {job['repo']} | Priority: {score}", flush=True)
        
        # 3. Update Database to RUNNING
        db = SessionLocal()
        # We use .update() because master.py already created the row
        db.query(JobRecord).filter(JobRecord.id == job_id).update({"status": "RUNNING"})
        db.commit()

        # 4. ACTUAL TESTING LOGIC (Replacing 'chumma' time.sleep)
        # We run a syntax check on the project files as a real test
        try:
            print(f"📦 Running tests for {job_id}...", flush=True)
            
            # This executes 'python3 -m py_compile' on the main files.
            # If there is a syntax error, it returns a non-zero exit code.
            test_process = subprocess.run(
                ["python3", "-m", "py_compile", "master.py", "worker.py", "database.py"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if test_process.returncode == 0:
                final_status = "COMPLETED"
                print(f"✅ Tests Passed for {job_id}", flush=True)
            else:
                final_status = "FAILED"
                print(f"❌ Tests Failed: {test_process.stderr}", flush=True)

        except Exception as e:
            final_status = "ERROR"
            print(f"🚨 Execution Error: {str(e)}", flush=True)

        # 5. Save Final Status to Database
        db.query(JobRecord).filter(JobRecord.id == job_id).update({"status": final_status})
        db.commit()
        db.close()
        
        print(f"🏁 [FINISHED] Job {job_id} is now {final_status}.", flush=True)