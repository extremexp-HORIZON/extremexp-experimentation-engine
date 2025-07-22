"""
Example usage of the Kubeflow converter
"""

import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter import KubeflowConverter

def main():
    """Example conversion of a .xxp file to Kubeflow Pipeline"""
    
    # Sample .xxp DSL content (you would normally read this from a file)
    sample_xxp_content = """
    main_experiment:
        tasks:
            - name: data_preprocessing
              type: python
              implementation: preprocessing_task.py
              order: 1
              outputs:
                - preprocessed_data
                
            - name: model_training
              type: python
              implementation: training_task.py
              order: 2
              dependencies:
                - data_preprocessing
              inputs:
                - preprocessed_data
              outputs:
                - trained_model
                
            - name: model_evaluation
              type: python
              implementation: evaluation_task.py
              order: 3
              dependencies:
                - model_training
              inputs:
                - trained_model
              outputs:
                - evaluation_results
    """
    
    # Create converter (you would normally pass your config here)
    converter = KubeflowConverter(config=None)
    
    # Create output directory
    output_dir = "./generated_pipelines"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Convert the .xxp content to Kubeflow Pipeline
        converter.convert_xxp_to_kubeflow(sample_xxp_content, output_dir)
        
        print(f"✅ Conversion completed successfully!")
        print(f"📁 Generated files in: {os.path.abspath(output_dir)}")
        print("📄 Files generated:")
        
        for file in os.listdir(output_dir):
            print(f"   - {file}")
            
    except Exception as e:
        print(f"❌ Conversion failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
