import subprocess

import click
from .console import console

############## CLI COMMANDS ##############

@click.group()
def cli():
    pass

@click.command()
def version():
    """Show the Booster Robot Version"""    
    subprocess.run(["cat", "/opt/booster/version.txt"])

cli.add_command(version)