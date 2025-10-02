# Working Booster Python Stuff
## Python Code
In booster-control theres examples of working python code.

The jupyter notebook has an example of doing arm commands. These use low level motor controls to move the arm. THE ROBOT MUST BE IN END EFFECTOR MODE ON THE GROUND TO USE THESE COMMANDS.

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