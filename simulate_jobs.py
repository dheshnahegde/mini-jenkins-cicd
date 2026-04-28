import requests
import random
import time
import uuid

# Configuration
API_URL = "http://localhost:8000/webhook"
LANGUAGES = ["python", "node"]
REPOS = ["alpha-project", "beta-service", "gamma-web", "delta-api", "epsilon-db"]

def create_random_jobs(num_jobs):
    print(f"🚀 Starting simulation for {num_jobs} random jobs...")
    
    for i in range(num_jobs):
        # 1. Pick a random language and repo
        lang = random.choice(LANGUAGES)
        repo = random.choice(REPOS)
        
        # 2. Create the payload
        payload = {
            "repository": f"{repo}-{i+1}",
            "language": lang
        }
        
        # 3. Send the request to our Master
        try:
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                print(f"✅ Sent {lang} job for {repo} (Status: {response.status_code})")
            else:
                print(f"❌ Failed to send job: {response.text}")
        except Exception as e:
            print(f"❌ Connection Error: {e}")

        # 4. RANDOMNESS: Wait between 1 to 4 seconds before the next "developer" pushes code
        wait_time = random.uniform(1, 4)
        time.sleep(wait_time)

    print("\n✨ All simulation jobs have been dispatched!")

if __name__ == "__main__":
    # Ask the user how many jobs they want to simulate
    try:
        count = int(input("How many jobs do you want to generate? "))
        create_random_jobs(count)
    except ValueError:
        print("Please enter a valid number.")