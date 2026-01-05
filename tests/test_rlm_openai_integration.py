#!/usr/bin/env python3
"""Test if RLM library can connect to local OpenAI-compatible API."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_rlm_with_local_api():
    """Test RLM library with local OpenAI-compatible API."""
    print("=" * 60)
    print("Testing RLM with Local OpenAI-Compatible API")
    print("=" * 60)

    try:
        from rlm import RLM
        print("✓ RLM library imported")
    except ImportError as e:
        print(f"✗ RLM library not installed: {e}")
        return False

    # Check if server is running
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✓ API server is running at http://localhost:8000")
        else:
            print("✗ API server returned unexpected status")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ API server not running at http://localhost:8000")
        print("\nStart the server first:")
        print("  python -m uvicorn ai_lab.api.app:app")
        return False
    except Exception as e:
        print(f"✗ Error checking server: {e}")
        return False

    # Test RLM with OpenAI backend
    print("\nInitializing RLM with OpenAI backend...")
    try:
        rlm = RLM(
            backend="openai",
            backend_kwargs={
                "model_name": "qwen-1-5b",
                "base_url": "http://localhost:8000/v1",
                "api_key": "dummy",  # Not used for local server
            },
            environment="local",
            verbose=True,
        )
        print("✓ RLM initialized successfully")
    except Exception as e:
        print(f"✗ RLM initialization failed: {e}")
        return False

    # Test basic completion
    print("\nTesting basic completion...")
    try:
        result = rlm.completion(
            prompt="Say 'Hello, RLM integration works!'",
            root_prompt=None
        )
        print(f"✓ Completion successful!")
        print(f"\nResponse: {result.response[:200]}")
        return True
    except Exception as e:
        print(f"✗ Completion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rlm_with_local_api()
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! RLM can use your OpenAI-compatible API")
        print("\nNext: Create OpenAIRLMRouter class")
        sys.exit(0)
    else:
        print("❌ Tests failed. Please fix the issues above.")
        sys.exit(1)
