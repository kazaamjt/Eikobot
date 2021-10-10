# type: ignore
# flake8: noqa
from pathlib import Path
import setuptools

this_directory = Path(__file__).parent
with open(this_directory / "README.md", encoding="utf-8") as f:
	long_description = f.read()

with open(this_directory / "requirements.txt", encoding="utf-8") as f:
	lines = f.read().splitlines(keepends=False)
	requires = []
	for line in lines:
		if line == "# Dev dependencies":
			break
		requires.append(line)

setuptools.setup(
	name="eikobot",
	version="0.0.0",
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
	python_requires=">=3.10",
	install_requires=requires,
)
