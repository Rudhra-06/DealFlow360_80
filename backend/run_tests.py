import sys
import pytest

if __name__ == "__main__":
    args = sys.argv[1:] if len(sys.argv) > 1 else ["-q"]
    sys.exit(pytest.main(args))
