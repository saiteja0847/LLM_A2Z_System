"""Training example using AI Lab SDK."""
from ai_lab_sdk import AILabClient

# Initialize client
client = AILabClient("http://localhost:8000")

# Start training job
print("Starting training job...")
job = client.training.train(
    base_model="qwen-1-5b",  # Replace with your base model
    output_name="my-finetuned-model",
    dataset_path="./training_data.jsonl",  # Path to your dataset
    epochs=3,
    batch_size=2,
    lora_rank=8,
    learning_rate=0.0001
)

print(f"Job ID: {job.id}")
print(f"Status: {job.status}")

# Wait for completion with progress updates
print("\nWaiting for training to complete...")
try:
    import time
    while True:
        job = client.training.get_job(job.id)
        print(f"Progress: {job.progress * 100:.1f}% - Status: {job.status}")

        if job.status in ["completed", "failed"]:
            break

        time.sleep(5)  # Poll every 5 seconds

    # Check result
    if job.status == "completed":
        print(f"\n✓ Training completed successfully!")
        print(f"Output: {job.result['output_path']}")
        print(f"Adapter name: {job.result['adapter_name']}")

        # Test the fine-tuned model
        print("\nTesting fine-tuned model...")
        response = client.chat.complete(
            model=job.result['adapter_name'],
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(f"Response: {response.content}")
    else:
        print(f"\n✗ Training failed: {job.error}")

except KeyboardInterrupt:
    print("\nTraining still running in background...")
    print(f"Check status with job ID: {job.id}")
