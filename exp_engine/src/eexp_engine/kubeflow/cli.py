"""
Command-line interface for the Kubeflow converter
"""
import click
import os
import sys
import logging
from .converter import KubeflowConverter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """ExtremeXP DSL to Kubeflow Pipelines Converter"""
    pass


@cli.command()
@click.argument('xxp_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='./kubeflow_pipelines', 
              help='Output directory for generated pipelines')
@click.option('--config', '-c', 
              help='Configuration file path (Python file)')
@click.option('--verbose', '-v', is_flag=True, 
              help='Enable verbose logging')
def convert(xxp_file, output, config, verbose):
    """
    Convert .xxp DSL file to Kubeflow Pipeline
    
    XXP_FILE: Path to the .xxp DSL file to convert
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        # Load configuration
        config_module = None
        if config:
            # Load config from specified file
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", config)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            logger.info(f"Loaded configuration from: {config}")
        else:
            # Try to load from default locations
            config_paths = [
                'eexp_config.py',
                '../eexp_config.py',
                '../../eexp_config.py'
            ]
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("config", config_path)
                    config_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config_module)
                    logger.info(f"Loaded configuration from: {config_path}")
                    break
                    
            if not config_module:
                logger.warning("No configuration file found. Using default settings.")
        
        # Read the .xxp file
        logger.info(f"Reading .xxp file: {xxp_file}")
        with open(xxp_file, 'r') as f:
            experiment_specification = f.read()
        
        # Create output directory
        os.makedirs(output, exist_ok=True)
        logger.info(f"Output directory: {os.path.abspath(output)}")
        
        # Convert
        converter = KubeflowConverter(config_module)
        converter.convert_xxp_to_kubeflow(experiment_specification, output)
        
        click.echo(f"✅ Successfully converted {xxp_file} to Kubeflow Pipeline in {output}")
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--check-kfp', is_flag=True, help='Check if Kubeflow Pipelines SDK is installed')
@click.option('--check-config', is_flag=True, help='Check configuration file')
def validate(check_kfp, check_config):
    """Validate the converter setup and dependencies"""
    
    all_valid = True
    
    if check_kfp:
        try:
            import kfp
            from kfp.v2 import compiler
            click.echo(f"✅ Kubeflow Pipelines SDK is installed (version: {kfp.__version__})")
        except ImportError:
            click.echo("❌ Kubeflow Pipelines SDK not found. Install with: pip install kfp")
            all_valid = False
    
    if check_config:
        config_found = False
        config_paths = ['eexp_config.py', '../eexp_config.py', '../../eexp_config.py']
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                click.echo(f"✅ Configuration file found: {config_path}")
                config_found = True
                break
                
        if not config_found:
            click.echo("⚠️  No configuration file found in standard locations")
            click.echo("   You can specify a config file with --config option")
    
    if not check_kfp and not check_config:
        # Run all checks by default
        validate.callback(check_kfp=True, check_config=True)
        return
        
    if all_valid:
        click.echo("✅ All validations passed!")
    else:
        click.echo("❌ Some validations failed. Please check the errors above.")
        sys.exit(1)


@cli.command()
def install_deps():
    """Install required dependencies for the converter"""
    
    click.echo("Installing Kubeflow Pipelines SDK...")
    
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "kfp>=2.0.0"])
        click.echo("✅ Successfully installed Kubeflow Pipelines SDK")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)


@cli.command()
@click.argument('pipeline_file', type=click.Path(exists=True))
@click.option('--endpoint', help='Kubeflow Pipelines endpoint URL')
@click.option('--experiment', default='Default', help='Experiment name')
@click.option('--run-name', help='Pipeline run name')
def submit(pipeline_file, endpoint, experiment, run_name):
    """Submit a compiled pipeline to Kubeflow Pipelines"""
    
    try:
        import kfp
        
        # Create client
        if endpoint:
            client = kfp.Client(host=endpoint)
        else:
            client = kfp.Client()
            
        # Submit the pipeline
        run_name = run_name or f"run-{os.path.basename(pipeline_file)}-{int(__import__('time').time())}"
        
        run = client.run_pipeline(
            experiment_id=client.create_experiment(experiment).id,
            job_name=run_name,
            pipeline_package_path=pipeline_file
        )
        
        click.echo(f"✅ Pipeline submitted successfully!")
        click.echo(f"   Run ID: {run.id}")
        click.echo(f"   Run Name: {run_name}")
        
    except Exception as e:
        click.echo(f"❌ Failed to submit pipeline: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
