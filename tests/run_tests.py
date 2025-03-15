#!/usr/bin/env python
"""
Run all API tests
This script executes all the test files for the API
"""
import os
import sys
import pytest
import time
from importlib import import_module
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_tests_with_reporting():
    """Run tests with reporting"""
    # Start timer
    start_time = time.time()
    
    # Print header
    print("\n" + "=" * 80)
    print("RUNNING API TESTS".center(80))
    print("=" * 80)
    
    # Run pytest with coverage
    args = [
        "-v",  # Verbose output
        "--color=yes",  # Colored output
        "-xvs",  # Exit on first failure, verbose, no capture
        "--no-header",  # No pytest header
        # Add coverage if you have it installed
        # "--cov=app",  # Coverage for app directory
        # "--cov-report=term",  # Terminal coverage report
    ]
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Add all test files to args
    test_files = [
        str(f) for f in test_dir.glob("test_*.py")
        if f.is_file() and f.name != "test_all.py"
    ]
    
    if not test_files:
        print("No test files found!")
        return 1
    
    print(f"Found {len(test_files)} test files:")
    for tf in test_files:
        print(f"  - {os.path.basename(tf)}")
    print("-" * 80)
    
    # Run pytest
    result = pytest.main(args + test_files)
    
    # Print summary
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print(f"TEST RUN COMPLETED IN {duration:.2f}s")
    print(f"{'PASSED' if result == 0 else 'FAILED'} WITH EXIT CODE {result}")
    print("=" * 80 + "\n")
    
    return result


def run_tests_manually():
    """
    Run tests manually by importing and calling test functions directly
    This is useful when pytest is not available
    """
    # Start timer
    start_time = time.time()
    
    # Print header
    print("\n" + "=" * 80)
    print("RUNNING API TESTS MANUALLY".center(80))
    print("=" * 80)
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Import test modules
    test_files = [
        f.stem for f in test_dir.glob("test_*.py")
        if f.is_file() and f.name != "test_all.py"
    ]
    
    if not test_files:
        print("No test files found!")
        return 1
    
    print(f"Found {len(test_files)} test files:")
    for tf in test_files:
        print(f"  - {tf}.py")
    print("-" * 80)
    
    # Track success/failure
    success = True
    
    # Import and run test_users first (since other tests depend on it)
    if "test_users" in test_files:
        try:
            print("\nRunning user tests:")
            print("-" * 80)
            test_users = import_module(f"tests.test_users")
            if hasattr(test_users, "test_register_user"):
                test_users.test_register_user()
            test_files.remove("test_users")
        except Exception as e:
            print(f"Error in user tests: {e}")
            success = False
    
    # Import and run test_auth next (since many tests depend on authentication)
    if "test_auth" in test_files:
        try:
            print("\nRunning authentication tests:")
            print("-" * 80)
            test_auth = import_module("tests.test_auth")
            if hasattr(test_auth, "run_auth_tests"):
                test_auth.run_auth_tests()
            elif hasattr(test_auth, "test_login"):
                test_auth.test_login()
            test_files.remove("test_auth")
        except Exception as e:
            print(f"Error in authentication tests: {e}")
            success = False
    
    # Run remaining test files
    for tf in test_files:
        try:
            print(f"\nRunning {tf}:")
            print("-" * 80)
            module = import_module(f"tests.{tf}")
            
            # Look for a run_tests function first
            if hasattr(module, "run_tests"):
                module.run_tests()
            else:
                # Otherwise, find and run all test_* functions
                test_functions = [
                    f for f in dir(module) 
                    if f.startswith("test_") and callable(getattr(module, f))
                ]
                
                for func_name in test_functions:
                    try:
                        print(f"Running {func_name}...")
                        getattr(module, func_name)()
                    except Exception as e:
                        print(f"Error in {func_name}: {e}")
                        success = False
        except Exception as e:
            print(f"Error importing {tf}: {e}")
            success = False
    
    # Print summary
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print(f"TEST RUN COMPLETED IN {duration:.2f}s")
    print(f"{'PASSED' if success else 'FAILED'}")
    print("=" * 80 + "\n")
    
    return 0 if success else 1


if __name__ == "__main__":
    # Try to run with pytest first, fall back to manual execution
    try:
        sys.exit(run_tests_with_reporting())
    except ImportError:
        print("pytest not available, falling back to manual test execution")
        sys.exit(run_tests_manually()) 