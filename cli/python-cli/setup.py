from setuptools import find_namespace_packages, setup

setup(
    name="boost",
    version="1.1.0",
    python_requires="~=3.8",
    install_requires=[
        "Click==8.1",
        "rich==14.0",
    ],
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "boost = boost.main:cli",
        ],
    },
)
