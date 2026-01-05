#!/usr/bin/env python3
"""Compare SimpleRLMRouter vs OpenAIRLMRouter."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_simple_router():
    """Test SimpleRLMRouter (direct MLX access)."""
    print("=" * 60)
    print("Testing SimpleRLMRouter")
    print("=" * 60)

    from ai_lab.core.rlm import SimpleRLMRouter, RLMConfig

    # Create router
    print("\nCreating SimpleRLMRouter...")
    router = SimpleRLMRouter("qwen-1-5b")
    print("✓ SimpleRLMRouter initialized")

    # Test with a document
    prompt = """
    Chapter 1: Introduction to AI
    Artificial Intelligence is transforming how we process information.
    Traditional language models have context limitations.

    Chapter 2: The Solution
    RLM (Recursive Language Models) enable near-infinite context handling
    by intelligently chunking and processing large documents.

    Chapter 3: Benefits
    This approach allows processing of documents of any size, making it
    possible to analyze entire books, research papers, and log files.
    """

    print("\nProcessing document (basic RLM)...")
    result = router.complete(
        prompt=prompt,
        root_prompt="Summarize the key benefits of RLM in 2-3 sentences"
    )

    print("\n✓ SimpleRLMRouter complete")
    print(f"\nResult:\n{result}\n")

    return True


def test_openai_router():
    """Test OpenAIRLMRouter (full RLM via API)."""
    print("=" * 60)
    print("Testing OpenAIRLMRouter")
    print("=" * 60)

    # Check if server is running
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code != 200:
            print("✗ API server not healthy")
            return False
    except Exception:
        print("✗ API server not running. Start with:")
        print("  python -m uvicorn ai_lab.api.app:app")
        return False

    from ai_lab.core.rlm import OpenAIRLMRouter, RLMConfig

    # Create router
    print("\nCreating OpenAIRLMRouter...")
    try:
        router = OpenAIRLMRouter("qwen-1-5b")
        print("✓ OpenAIRLMRouter initialized (connected to API)")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return False

    # Test with a document
    prompt = """
    Chapter 1: Introduction to AI
    Artificial Intelligence is transforming how we process information.
    Traditional language models have context limitations.

    Chapter 2: The Solution
    RLM (Recursive Language Models) enable near-infinite context handling
    by intelligently chunking and processing large documents.

    Chapter 3: Benefits
    This approach allows processing of documents of any size, making it
    possible to analyze entire books, research papers, and log files.
    """

    print("\nProcessing document (full RLM with code execution)...")
    print("(This will take longer - RLM performs multi-step reasoning)")

    try:
        result = router.complete(
            prompt=prompt,
            root_prompt="Summarize the key benefits of RLM in 2-3 sentences"
        )

        print("\n✓ OpenAIRLMRouter complete")
        print(f"\nResult:\n{result}\n")
        return True
    except Exception as e:
        print(f"✗ OpenAIRLMRouter failed: {e}")
        return False


def main():
    """Run comparison tests."""
    print("\n" + "=" * 60)
    print("RLM Router Comparison Test")
    print("=" * 60)

    # Test SimpleRLMRouter
    simple_ok = test_simple_router()

    print("\n" * 2)

    # Test OpenAIRLMRouter
    openai_ok = test_openai_router()

    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"SimpleRLMRouter:   {'✅ PASS' if simple_ok else '❌ FAIL'}")
    print(f"OpenAIRLMRouter:   {'✅ PASS' if openai_ok else '❌ FAIL'}")
    print()

    if simple_ok and openai_ok:
        print("🎉 Both routers working!")
        print("\nUsage:")
        print("  CLI: lab rlm qwen-1-5b -p '<doc>' -r '<task>'")
        print("       (Simple router - no server needed)")
        print()
        print("  CLI: lab rlm-full qwen-1-5b -p '<doc>' -r '<task>'")
        print("       (Full RLM - requires server)")
        print()
        print("  API: POST /api/v1/rlm/complete")
        print("       (Simple router)")
        print()
        print("  API: POST /api/v1/rlm/full")
        print("       (Full RLM)")
        return 0
    else:
        print("⚠ Some tests failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
