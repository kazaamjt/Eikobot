# Eikobot Quickstarts

The goal of this quickstart is to walk you through using Eikobot in
a fast and practical manner, while showing some of it's powerfull features.  
It _is_ recomended to read the [language overview](docs/language_overview.md) first.  

In this series of quickstarts, we'll look at several scenarios,
ranging from a simple docker deployment, to deploying a whole infrastructure
running kubernetes, databases, etc.  

You will need an Eikobot project to go through these quickstarts.  
Unless mentioned otherwise, setting up a new project for each quickstart is recommended.  

## Create a new project

Create a new directory `eikobot-quickstarts`.  
Inside this directory, set up a python3.10+ venv, and activate it:  

```sh
python3.10 -m venv .env
. .env/bin/activate
```

Install eikobot in the venv:

```sh
pip install -U pip wheel
pip install eikobot
```

Then, create the main model file named `main.eiko`.  
This will be the file in which we declare our resources.  

## Scenario index

- [Scenario 1: Deploying a docker host and containers](docs/quickstarts/scenario_1/scenario_1.md)
