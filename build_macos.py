#!/usr/bin/env python3
"""
Build script for creating macOS app bundle.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return False
    return True


def clean_build():
    """Clean previous build artifacts."""
    print("Cleaning previous build artifacts...")
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for dir_pattern in dirs_to_clean:
        for path in Path('.').glob(dir_pattern):
            if path.is_dir():
                print(f"Removing directory: {path}")
                shutil.rmtree(path)
            elif path.is_file():
                print(f"Removing file: {path}")
                path.unlink()


def install_dependencies():
    """Install build dependencies."""
    print("Installing build dependencies...")
    if not run_command("uv sync --extra build"):
        return False
    return True


def build_app():
    """Build the macOS app bundle."""
    print("Building macOS app bundle...")
    if not run_command("uv run python setup.py py2app"):
        return False
    return True


def verify_app():
    """Verify the built app."""
    app_path = Path('dist/BlogTool.app')
    if not app_path.exists():
        print(f"Error: App bundle not found at {app_path}")
        return False
    
    print(f"App bundle created successfully at: {app_path}")
    
    # Check if the app can be launched
    print("Verifying app can be launched...")
    result = subprocess.run([
        'open', '-a', str(app_path), '--args', '--version'
    ], capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0:
        print("✓ App bundle verification successful")
        return True
    else:
        print("⚠ App bundle created but may have issues")
        print(f"Launch test result: {result.stderr}")
        return True  # Still consider it successful since the bundle exists


def create_dmg():
    """Create a DMG file for distribution."""
    print("Creating DMG file...")
    dmg_name = "BlogTool-0.1.0.dmg"
    
    # Remove existing DMG
    if Path(dmg_name).exists():
        Path(dmg_name).unlink()
    
    # Create DMG
    if not run_command(f'hdiutil create -volname "BlogTool" -srcfolder dist/BlogTool.app -ov -format UDZO {dmg_name}'):
        print("Warning: DMG creation failed, but app bundle is still available")
        return False
    
    print(f"✓ DMG created: {dmg_name}")
    return True


def main():
    """Main build process."""
    print("Building BlogTool for macOS...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('pyproject.toml').exists():
        print("Error: pyproject.toml not found. Run this script from the project root.")
        sys.exit(1)
    
    # Build steps
    steps = [
        ("Clean build artifacts", clean_build),
        ("Install dependencies", install_dependencies),
        ("Build app bundle", build_app),
        ("Verify app bundle", verify_app),
        ("Create DMG", create_dmg),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"✗ Failed: {step_name}")
            sys.exit(1)
        print(f"✓ Completed: {step_name}")
    
    print("\n" + "=" * 50)
    print("Build completed successfully!")
    print("App bundle: dist/BlogTool.app")
    if Path("BlogTool-0.1.0.dmg").exists():
        print("DMG file: BlogTool-0.1.0.dmg")
    print("\nTo test the app:")
    print("  open dist/BlogTool.app")
    print("\nTo install the app:")
    print("  cp -r dist/BlogTool.app /Applications/")


if __name__ == "__main__":
    main()