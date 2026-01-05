#!/usr/bin/env python3
"""Test the fine-tuned model."""
import subprocess
import sys

def test_model(prompt: str, use_adapter: bool = True):
    """Test model with or without adapter."""
    print("=" * 70)
    print(f"Testing {'WITH' if use_adapter else 'WITHOUT'} adapter")
    print("=" * 70)
    print(f"Prompt: {prompt}")
    print("-" * 70)

    cmd = [
        "python3", "-m", "mlx_lm.generate",
        "--model", "/Users/saiteja/Downloads/My-Projects/Claude-Optimized/Projects/models/qwen2.5-1.5b-instruct-4bit",
        "--prompt", prompt,
        "--max-tokens", "150",
        "--temp", "0.3",  # Lower temperature for more focused responses
    ]

    if use_adapter:
        cmd.extend(["--adapter-path", "models/qwen-1-5b-finetuned-test"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            response = result.stdout.strip()
            print(f"Response:\n{response}")
        else:
            print(f"Error: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("Error: Generation timed out")
    except Exception as e:
        print(f"Error: {e}")

    print()

def main():
    """Run tests."""
    print("\n" + "=" * 70)
    print("Fine-tuned Model Test")
    print("=" * 70)
    print("\nTesting on questions similar to training data...\n")

    # Test prompts - similar to training data
    test_prompts = [
        "Question: What is machine learning?\nAnswer:",
        "Question: What is a neural network?\nAnswer:",
        "Question: What is deep learning?\nAnswer:",
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_prompts)}")
        print(f"{'='*70}\n")

        # Test with adapter (fine-tuned)
        test_model(prompt, use_adapter=True)

        # Uncomment to compare with base model:
        # test_model(prompt, use_adapter=False)

    print("=" * 70)
    print("Testing complete!")
    print("=" * 70)
    print("\nThe fine-tuned model should provide clear, concise answers")
    print("about AI/ML concepts based on the training data.\n")

if __name__ == "__main__":
    main()
