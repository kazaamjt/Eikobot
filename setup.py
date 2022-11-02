"""
The setup.py file is widely used format.
Contains all the logic for making the packages.
"""
from pathlib import Path

import setuptools

this_directory = Path(__file__).parent
with open(this_directory / "README.md", encoding="utf-8") as f:
    long_description = f.read()

VERSION = "0.2.1"
REQUIRES = [
    "click==8.0.2",
    "colorama==0.4.4",
    "jinja2==3.1.2",
]

setuptools.setup(
    name="eikobot",
    version=VERSION,
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
    package_data={"": ["**/*.eiko", "**/*.py", "requirements.xt"]},
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=REQUIRES,
    entry_points={"console_scripts": ["eikobot=eikobot.__main__:cli"]},
)
