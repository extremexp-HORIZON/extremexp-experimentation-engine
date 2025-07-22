#!/usr/bin/env python3
"""
Test script for the Kubeflow converter from the root directory
"""

import os
import sys

# Add the exp_engine src to the path
sys.path.insert(0, 'exp_engine/src')

def test_basic_import():
    """Test basic imports"""
    print("🔄 Testing basic imports...")
    
    try:
        from eexp_engine.kubeflow import KubeflowConverter
        print("✅ Successfully imported KubeflowConverter")
        return True
    except Exception as e:
        print(f"❌ Failed to import KubeflowConverter: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_real_xxp():
    """Test with a real .xxp file"""
    print("\n🔄 Testing with real .xxp file...")
    
    # Path to an existing .xxp file
    xxp_file = "exp_engine/library-experiments/tests/simple_configurations/demo_wp5.xxp"
    
    if not os.path.exists(xxp_file):
        print(f"❌ .xxp file not found: {xxp_file}")
        return False
    
    # Read the file
    with open(xxp_file, 'r') as f:
        xxp_content = f.read()
    
    print(f"📖 Read .xxp file: {xxp_file}")
    print(f"📄 Content preview:\n{xxp_content[:200]}...")
    
    try:
        from eexp_engine.kubeflow import KubeflowConverter
        
        # Load configuration
        try:
            import eexp_config
            config = eexp_config
            print("✅ Loaded eexp_config.py")
        except ImportError:
            print("⚠️  Could not load eexp_config.py, using None")
            config = None
        
        # Create converter
        converter = KubeflowConverter(config=config)
        
        # Create output directory
        output_dir = "./test_kubeflow_output"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"📁 Output directory: {os.path.abspath(output_dir)}")
        
        # Convert (this will test the parsing)
        converter.convert_xxp_to_kubeflow(xxp_content, output_dir)
        
        print("✅ Conversion completed!")
        
        # List generated files
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
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Testing ExtremeXP Kubeflow Converter")
    print("=" * 50)
    
    # Test basic import
    if not test_basic_import():
        return 1
    
    # Test with real file
    if not test_with_real_xxp():
        return 1
    
    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
