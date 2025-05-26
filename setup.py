"""
The setup.py file is widely used format.
Contains all the logic for making the packages.
"""
from pathlib import Path

import setuptools

this_directory = Path(__file__).parent
with open(this_directory / "README.md", encoding="utf-8") as f:
    long_description = f.read()

VERSION = "0.7.8"
REQUIRES = [
    "aiohttp>=3.12.1",
    "asyncssh>=2.21.0",
    "click>=8.2.1",
    "colorama>=0.4.6",
    "jinja2>=3.1.6",
    "packaging>=25.0",
    "pydantic>=2.11.5",
    "setuptools>=80.8.0",
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
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Development Status :: 4 - Beta",
    ],
    packages=setuptools.find_packages(),
    package_data={"": ["**/*.eiko", "**/*.py", "py.typed"]},
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=REQUIRES,
    entry_points={"console_scripts": ["eikobot=eikobot.__main__:main"]},
)
