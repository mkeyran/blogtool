"""Entry point for PyInstaller-built app."""

# Use absolute import since PyInstaller bundles everything properly
from blogtool.cli import main

if __name__ == "__main__":
    main()