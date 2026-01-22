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

@click.command()
def volume():
    """Show the Booster Robot Volume Level"""    
    subprocess.run(["alsamixer"])

cli.add_command(version)
cli.add_command(volume)