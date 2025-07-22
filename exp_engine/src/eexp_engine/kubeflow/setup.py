#!/usr/bin/env python3
"""
Setup script for the Kubeflow converter
"""

import subprocess
import sys
import os


def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    """Install required dependencies for the Kubeflow converter"""
    
    print("🚀 Setting up ExtremeXP Kubeflow Converter")
    print("=" * 50)
    
    # Required packages
    packages = [
        "kfp>=2.0.0",
        "click>=8.0.0", 
        "pyyaml>=6.0"
    ]
    
    failed_packages = []
    
    for package in packages:
        print(f"📦 Installing {package}...")
        if install_package(package):
            print(f"✅ Successfully installed {package}")
        else:
            print(f"❌ Failed to install {package}")
            failed_packages.append(package)
    
    print("\n" + "=" * 50)
    
    if not failed_packages:
        print("✅ All dependencies installed successfully!")
        print("\n🎉 Setup complete! You can now use the Kubeflow converter:")
        print("   python xxp_to_kubeflow.py --help")
        print("   python demo.py")
        return 0
    else:
        print(f"❌ Failed to install: {', '.join(failed_packages)}")
        print("Please install them manually:")
        for package in failed_packages:
            print(f"   pip install {package}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
