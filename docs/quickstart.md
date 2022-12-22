# Eikobot Quickstarts

The goal of this quickstart is to walk you through using Eikobot in
a fast and practical manner, while showing you some of it's powerfull features
and some of it's weirder sides.  

In this series of quickstarts, we'll look at several scenarios,
ranging from a simple database deployment, to deploying a whole infrastructure
running kubernetes, a database, etc.  

You will need an Eikobot project to go through these quickstarts.  
This guide however, assumes you will rease the same project
and thus the project only needs to be set up once.  

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

## Scenario 1: Deploying Postgres

For our first scenario, we will use Eikobot to deploy and configure
the postgres server software on a target machine.  

This scenario covers the following topics:

- Creating a basic Eikobot model
- Compiling a model
- writing handlers
- deploying a model

And it assumes you have the following:  

- A target machine running Debian*
- Sudo access on said machine

*Make sure that your user has passwordless sudo rights on the target machine

### Step 1: Deploying postgres

While a module could be provided for you to easily deploy postgres,
the goal of this quickstart is to go through the creation of a model in its entirety.  

First, let's analyse the install instructions for postgres on debian:

```sh
# Create the file repository configuration:
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# Import the repository signing key:
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Update the package lists:
sudo apt-get update

# Install the latest version of PostgreSQL.
# If you want a specific version, use 'postgresql-12' or similar instead of 'postgresql':
sudo apt-get -y install postgresql
```
