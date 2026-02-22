"""Pytest fixtures and shared setup."""
import os
import sys

# Ensure project root is on path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)
# Ensure src/python is on path so test imports resolve
sys.path.insert(0, os.path.join(_project_root, 'src', 'python'))
