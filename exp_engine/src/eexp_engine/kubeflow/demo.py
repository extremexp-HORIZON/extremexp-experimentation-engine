#!/usr/bin/env python3
"""
Demo script to test the Kubeflow converter with an existing .xxp file
"""

import os
import sys
import logging

# Add the current directory to the path to import the converter
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from converter import KubeflowConverter
except ImportError:
    print("❌ Could not import KubeflowConverter. Make sure you're in the right directory.")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    """Test the converter with an existing .xxp file"""
    
    # Path to an existing .xxp file
    xxp_file_path = "../../../library-experiments/tests/simple_configurations/demo_wp5.xxp"
    
    if not os.path.exists(xxp_file_path):
        print(f"❌ .xxp file not found: {xxp_file_path}")
        print("Please run this script from the kubeflow directory")
        return 1
    
    # Read the .xxp file
    print(f"📖 Reading .xxp file: {xxp_file_path}")
    with open(xxp_file_path, 'r') as f:
        xxp_content = f.read()
    
    print(f"📄 File content preview:")
    print("-" * 50)
    print(xxp_content[:200] + "..." if len(xxp_content) > 200 else xxp_content)
    print("-" * 50)
    
    # Create output directory
    output_dir = "./demo_output"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Output directory: {os.path.abspath(output_dir)}")
    
    try:
        # Check if Kubeflow Pipelines is available
        try:
            import kfp
            print(f"✅ Kubeflow Pipelines SDK available (version: {kfp.__version__})")
        except ImportError:
            print("⚠️  Kubeflow Pipelines SDK not installed. Install with: pip install kfp")
            print("   The converter will still run but won't be able to compile pipelines.")
        
        # Create converter
        print("🔄 Creating converter...")
        converter = KubeflowConverter(config=None)
        
        # Convert the .xxp content to Kubeflow Pipeline
        print("🔄 Converting .xxp to Kubeflow Pipeline...")
        converter.convert_xxp_to_kubeflow(xxp_content, output_dir)
        
        print(f"✅ Conversion completed successfully!")
        print(f"📁 Generated files in: {os.path.abspath(output_dir)}")
        
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            if files:
                print("📄 Generated files:")
                for file in files:
                    file_path = os.path.join(output_dir, file)
                    file_size = os.path.getsize(file_path)
                    print(f"   - {file} ({file_size} bytes)")
            else:
                print("⚠️  No files were generated")
        
    except Exception as e:
        print(f"❌ Conversion failed: {str(e)}")
        import traceback
        print("📋 Full error traceback:")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
