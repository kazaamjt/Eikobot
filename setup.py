"""
The setup.py file is widely used format.
Contains all the logic for making the packages.
"""
from pathlib import Path

import setuptools

this_directory = Path(__file__).parent
with open(this_directory / "README.md", encoding="utf-8") as f:
    long_description = f.read()

with open(this_directory / "requirements.txt", encoding="utf-8") as f:
    lines = f.read().splitlines(keepends=False)
    requires = []
    for line in lines:
        requires.append(line)

with open(this_directory / "VERSION", encoding="utf-8") as f:
    version = f.read()

setuptools.setup(
    name="eikobot",
    version=version,
    description="The eikobot desired state engine.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="kazaamjt",
    author_email="kazaamjt@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    package_data={"": ["**/*.eiko", "**/*.py"]},
    python_requires=">=3.10",
    install_requires=requires,
    entry_points={"console_scripts": ["eikobot=eikobot.__main__:cli"]},
)
