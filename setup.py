from setuptools import setup, find_packages

setup(
    name="postgrados-chile",
    version="0.1.0",
    packages=find_packages(),
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={
        "console_scripts": [
            "postgrados=src.cli:cli",
        ]
    },
    python_requires=">=3.11",
)
