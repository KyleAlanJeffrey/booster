# Working Booster Python Stuff
The `booster_robotics_sdk-main` is the sdk supplied by the manufacturer. The `booster_python_client` is a my custom wrapper written around the sdk to make usage of the robot easier. To use the current standard fight mode you can either run:

`python3 -m booster_python_client`

or if that fails run:

`python3 scripts/fight_mode.py`

The booster.ipynb has some simple use cases for changing the modes and such.


You NEED TO MAKE SURE TO EXIT THE PROGRAM AFTER RUNNING IT AS THERE WILL BE A LINGERING CONTROLLER SUBSCRIBER IF YOU DO NOT.

# Auxiliary Stuff (PROBABLY NOT IMPORTANT TO YOU)
## Getting Docker Container Working(Experimenntal)
In the booster_robotics_sdk directory, run the following command to install the dependencies:

```bash
./install.sh
```
## Build C++ SDK and examples
```bash
./build.sh

```

## Using w/ Simulator
Use this guide to install the webbots simulator. Download their robot files and interface using this project with the correct network interface. 
https://booster.feishu.cn/wiki/DtFgwVXYxiBT8BksUPjcOwG4n4f#doxcnVlUn0say5S45a17WO5efPd


# Developing:
All the Python API is defined in booster_robotics_sdk-main/python/binding.cpp. I've tried to outline the usable functions in bot.ipynb. 