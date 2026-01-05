#!/usr/bin/env python3
"""Test training API endpoints."""
import httpx
import time
import json

BASE_URL = "http://localhost:8000"

def test_training_api():
    """Test training endpoints."""
    print("Testing Training API...\n")
    
    # 1. List existing jobs
    print("1. Listing training jobs...")
    response = httpx.get(f"{BASE_URL}/api/training/jobs")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Total jobs: {data['total']}\n")
    
    # 2. Create a training job
    print("2. Creating training job...")
    response = httpx.post(
        f"{BASE_URL}/api/training/jobs",
        json={
            "base_model": "qwen-1-5b",
            "dataset_path": "datasets/sample_training.jsonl",
            "output_name": "qwen-1-5b-finetuned",
            "epochs": 1,  # Just 1 epoch for quick test
            "batch_size": 2,
            "lora_rank": 8,
            "learning_rate": 0.0001
        },
        timeout=10.0
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        job = response.json()
        job_id = job['id']
        print(f"   Job ID: {job_id}")
        print(f"   Status: {job['status']}\n")
        
        # 3. Monitor job progress
        print("3. Monitoring job progress...")
        for i in range(10):  # Check for up to 1 minute
            time.sleep(6)
            response = httpx.get(f"{BASE_URL}/api/training/jobs/{job_id}")
            if response.status_code == 200:
                job = response.json()
                print(f"   [{i+1}/10] Status: {job['status']}, Progress: {job['progress']:.1%}")
                
                if job['status'] in ['completed', 'failed']:
                    print(f"\n   Final status: {job['status']}")
                    if job['error']:
                        print(f"   Error: {job['error']}")
                    if job['result']:
                        print(f"   Result: {json.dumps(job['result'], indent=2)}")
                    break
        
        # 4. Get job logs
        print("\n4. Fetching job logs (last 20 lines)...")
        response = httpx.get(f"{BASE_URL}/api/training/jobs/{job_id}/logs?tail=20")
        if response.status_code == 200:
            logs_data = response.json()
            print(f"   Total log lines: {len(logs_data['logs'])}")
            for log in logs_data['logs'][-5:]:  # Show last 5
                print(f"   {log}")
    else:
        print(f"   Error: {response.text}\n")
    
    print("\n✅ Training API test complete!")

if __name__ == "__main__":
    test_training_api()
