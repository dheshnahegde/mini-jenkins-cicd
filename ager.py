import redis
import time

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

QUEUE_NAME = "jenkins_priority_queue"
AGING_FACTOR = -1  # Subtract 1 from the score every cycle

def age_jobs():
    print(f"⏰ Aging cycle started...")
    # Get all jobs currently in the queue
    jobs = r.zrange(QUEUE_NAME, 0, -1)
    
    if not jobs:
        print("Queue empty, nothing to age.")
        return

    for job in jobs:
        # ZINCRBY adds the value to the current score
        # Adding -1 effectively lowers the score (increases priority)
        new_score = r.zincrby(QUEUE_NAME, AGING_FACTOR, job)
        print(f"Aged job to new priority: {new_score}")

if __name__ == "__main__":
    while True:
        age_jobs()
        time.sleep(30)  # Run every 30 seconds