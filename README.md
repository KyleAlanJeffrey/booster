# Booster Robotics SDK
An adjust of the Booster Robotics SDK to support python binding and some examples.

Booster Robotics SDK aims to provide a simple and easy-to-use interface for developers to control the Booster Robotics products. 

## Installation
```bash
./install.sh
```
## Build C++ SDK and examples
```bash
./build.sh
```

## Run examples
### 1. run b1_arm_sdk_example_client locally
```
cd build
./b1_arm_sdk_example_client 127.0.0.1
```
### 2. run b1_7dof_arm_sdk_example_client locally
```
cd build
./b1_7dof_arm_sdk_example_client 127.0.0.1
```
### 3. run other example xxx locally
```
cd build
./xxx 127.0.0.1
```


## License

This project is licensed under the Apache License, Version 2.0. See the LICENSE file for details.

This project uses the following third-party libraries:
- fastDDS (Apache License 2.0)
- pybind11 (BSD 3-Clause License)
- pybind11-stubgen (MIT License)