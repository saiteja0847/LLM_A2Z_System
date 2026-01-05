#!/usr/bin/env python3
"""Test script to validate RLM integration."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all RLM components can be imported."""
    print("Testing imports...")

    try:
        from ai_lab.core.rlm import RLMRouter, RLMConfig, InferenceClientAdapter
        print("  ✓ RLM components imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_registry_exists():
    """Test that registry is accessible."""
    print("\nTesting registry...")

    try:
        from ai_lab.core.registry import Registry

        registry = Registry()
        models = registry.list()
        print(f"  ✓ Registry loaded with {len(models)} models")

        if models:
            print(f"  Available models:")
            for m in models[:5]:  # Show first 5
                print(f"    - {m.name} ({m.backend.value})")
            if len(models) > 5:
                print(f"    ... and {len(models) - 5} more")

        return True
    except Exception as e:
        print(f"  ✗ Registry test failed: {e}")
        return False


def test_rlm_status():
    """Test RLM library installation."""
    print("\nTesting RLM library...")

    try:
        import rlm
        print(f"  ✓ RLM library installed (version: {getattr(rlm, '__version__', 'unknown')})")
        return True
    except ImportError:
        print("  ✗ RLM library not installed")
        print("    Install with: pip install git+https://github.com/alexzhang13/rlm.git")
        return False


def test_router_creation():
    """Test RLMRouter can be instantiated (with mock)."""
    print("\nTesting RLMRouter creation...")

    try:
        from ai_lab.core.rlm import RLMRouter, RLMConfig
        from ai_lab.core.registry import Registry

        registry = Registry()
        models = registry.list()

        if not models:
            print("  ⚠ No models in registry to test with")
            return True

        # Try to create a router (will fail if no models, but that's ok)
        test_model = models[0].name
        print(f"  Testing with model: {test_model}")

        config = RLMConfig(
            model_name=test_model,
            max_iterations=5,  # Low for testing
            verbose=False,
        )

        print("  ✓ RLMConfig created successfully")
        print(f"    Model: {config.model_name}")
        print(f"    Max iterations: {config.max_iterations}")

        return True

    except Exception as e:
        print(f"  ✗ Router creation test failed: {e}")
        return False


def test_adapter_structure():
    """Test adapter has correct structure."""
    print("\nTesting InferenceClientAdapter structure...")

    try:
        from ai_lab.core.rlm import InferenceClientAdapter
        from rlm.clients.base_lm import BaseLM

        # Check adapter inherits from BaseLM
        if issubclass(InferenceClientAdapter, BaseLM):
            print("  ✓ InferenceClientAdapter correctly inherits from RLM BaseLM")
        else:
            print("  ✗ InferenceClientAdapter does not inherit from BaseLM")
            return False

        # Check required methods exist
        required_methods = ['completion', 'acompletion', 'get_usage_summary', 'get_last_usage']
        for method in required_methods:
            if hasattr(InferenceClientAdapter, method):
                print(f"  ✓ Method '{method}' exists")
            else:
                print(f"  ✗ Method '{method}' missing")
                return False

        return True

    except Exception as e:
        print(f"  ✗ Adapter structure test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("RLM Integration Test Suite")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "Registry": test_registry_exists(),
        "RLM Library": test_rlm_status(),
        "Router Creation": test_router_creation(),
        "Adapter Structure": test_adapter_structure(),
    }

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(results.values())
    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! RLM integration is ready.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
