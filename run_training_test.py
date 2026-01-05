#!/usr/bin/env python3
"""Run and monitor a full training test."""
import httpx
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def format_duration(seconds):
    """Format duration in seconds to human readable."""
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}m {secs}s"

def run_training():
    """Run full training test with monitoring."""
    print("=" * 60)
    print("AI Lab - Full Training Test")
    print("=" * 60)
    print(f"\nStarting time: {datetime.now().strftime('%H:%M:%S')}")
    print("\nConfiguration:")
    print("  Base Model: qwen-1-5b")
    print("  Dataset: 10 Q&A samples")
    print("  Epochs: 3")
    print("  Batch Size: 2")
    print("  LoRA Rank: 8")
    print("  LoRA Layers: 16")
    print("  Learning Rate: 0.0001")
    print("\n" + "=" * 60)
    
    # Create training job
    print("\n[1/4] Creating training job...")
    start_time = time.time()
    
    response = httpx.post(
        f"{BASE_URL}/api/training/jobs",
        json={
            "base_model": "qwen-1-5b",
            "dataset_path": "datasets/sample_data",  # MLX expects directory with train.jsonl
            "output_name": "qwen-1-5b-finetuned-test",
            "epochs": 3,
            "batch_size": 2,
            "lora_rank": 8,
            "lora_layers": 16,
            "learning_rate": 0.0001
        },
        timeout=10.0
    )
    
    if response.status_code != 201:
        print(f"❌ Failed to create job: {response.text}")
        return
    
    job = response.json()
    job_id = job['id']
    print(f"✓ Job created: {job_id}")
    
    # Monitor progress
    print("\n[2/4] Training in progress...")
    print("=" * 60)
    
    last_progress = 0
    check_count = 0
    
    while True:
        check_count += 1
        time.sleep(5)  # Check every 5 seconds
        
        response = httpx.get(f"{BASE_URL}/api/training/jobs/{job_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get job status")
            break
        
        job = response.json()
        status = job['status']
        progress = job['progress']
        elapsed = time.time() - start_time
        
        # Show progress update if changed
        if progress != last_progress or check_count % 6 == 0:  # Every 30s minimum
            bar_length = 40
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            eta = ""
            if progress > 0.05:  # After 5% we can estimate
                total_time = elapsed / progress
                remaining = total_time - elapsed
                eta = f" | ETA: {format_duration(remaining)}"
            
            print(f"\r{bar} {progress:6.1%} | {format_duration(elapsed)}{eta}", end='', flush=True)
            last_progress = progress
        
        # Check if done
        if status in ['completed', 'failed', 'cancelled']:
            print()  # New line after progress bar
            print("=" * 60)
            
            if status == 'completed':
                print(f"\n✓ Training completed in {format_duration(elapsed)}")
                
                # Get final logs
                response = httpx.get(f"{BASE_URL}/api/training/jobs/{job_id}/logs?tail=10")
                if response.status_code == 200:
                    logs = response.json()
                    print("\n[3/4] Final training logs:")
                    for log in logs['logs'][-5:]:
                        if log.strip():
                            print(f"  {log}")
                
                # Show result
                if job.get('result'):
                    print("\n[4/4] Training result:")
                    result = job['result']
                    print(f"  Output path: {result.get('output_path')}")
                    print(f"  Base model: {result.get('base_model')}")
                    print(f"  Epochs: {result.get('epochs')}")
                
                print("\n" + "=" * 60)
                print("✅ TRAINING TEST SUCCESSFUL!")
                print("=" * 60)
                
            elif status == 'failed':
                print(f"\n❌ Training failed: {job.get('error')}")
                
                # Show error logs
                response = httpx.get(f"{BASE_URL}/api/training/jobs/{job_id}/logs?tail=20")
                if response.status_code == 200:
                    logs = response.json()
                    print("\nError logs:")
                    for log in logs['logs'][-10:]:
                        print(f"  {log}")
            
            break

if __name__ == "__main__":
    time.sleep(5)  # Wait for API server
    run_training()
