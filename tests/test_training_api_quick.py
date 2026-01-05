#!/usr/bin/env python3
"""Quick test of training API endpoints (no waiting for completion)."""
import httpx
import json

BASE_URL = "http://localhost:8000"

def test_quick():
    """Quick validation of training endpoints."""
    print("Quick Training API Validation...\n")
    
    # 1. List jobs
    print("✓ Testing GET /api/training/jobs")
    response = httpx.get(f"{BASE_URL}/api/training/jobs")
    assert response.status_code == 200
    print(f"  Status: {response.status_code}")
    
    # 2. Create job
    print("\n✓ Testing POST /api/training/jobs")
    response = httpx.post(
        f"{BASE_URL}/api/training/jobs",
        json={
            "base_model": "qwen-1-5b",
            "dataset_path": "datasets/sample_training.jsonl",
            "output_name": "qwen-test-ft",
            "epochs": 1,
            "batch_size": 2,
            "lora_rank": 4,
            "lora_layers": 8,
            "learning_rate": 0.0001
        }
    )
    assert response.status_code == 201
    job = response.json()
    job_id = job['id']
    print(f"  Status: {response.status_code}")
    print(f"  Job ID: {job_id}")
    print(f"  Initial status: {job['status']}")
    
    # 3. Get job status
    print(f"\n✓ Testing GET /api/training/jobs/{job_id}")
    response = httpx.get(f"{BASE_URL}/api/training/jobs/{job_id}")
    assert response.status_code == 200
    job = response.json()
    print(f"  Status: {response.status_code}")
    print(f"  Job status: {job['status']}")
    print(f"  Progress: {job['progress']:.1%}")
    
    # 4. Get job logs
    print(f"\n✓ Testing GET /api/training/jobs/{job_id}/logs")
    response = httpx.get(f"{BASE_URL}/api/training/jobs/{job_id}/logs")
    assert response.status_code == 200
    logs = response.json()
    print(f"  Status: {response.status_code}")
    print(f"  Log lines: {len(logs['logs'])}")
    if logs['logs']:
        print(f"  Latest: {logs['logs'][-1][:80]}...")
    
    # 5. Cancel job (if still running)
    if job['status'] in ['pending', 'running']:
        print(f"\n✓ Testing DELETE /api/training/jobs/{job_id} (cancel)")
        response = httpx.delete(f"{BASE_URL}/api/training/jobs/{job_id}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 204:
            print("  Job cancelled successfully")
    
    print("\n✅ All training API endpoints working correctly!")

if __name__ == "__main__":
    import time
    time.sleep(5)  # Wait for server to start
    test_quick()
