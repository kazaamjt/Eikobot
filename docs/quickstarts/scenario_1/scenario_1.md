# Scenario 1: Deploying a docker host and containers

For our first scenario, we will use Eikobot to deploy and configure
docker on a target machine.  

This scenario covers the following topics:

- Creating a basic Eikobot model
- Compiling a model
- writing handlers
- deploying a model

And it assumes you have the following:  

- A target machine running Debian*
- SSH access with an ssh key
- Sudo rights (password enabled sudo)

NOTE: that at the end of this quickstart you will have a machine
with dockers HTTP API exposed.  
It is therefore recommended to do this on Virtual machines on a private network.  
Under no circumstance should this type of setup run in production.  
Instead HTTPS and server/client certificates should be used.  

*If not using debian, some minor changes to the code might be needed.  

## Step 1: Installing docker

While a module could be provided for you to easily deploy docker,
the goal of this quickstart is to go through the creation of a model in its entirety.  

First we'll create a resource that represents a docker instance.  
It'll take `std.Host` as an argument, and optionally a port.  

file: _docker.eiko_

```Python
import std

resource DockerHost:
    host: std.Host
    port: int = 2375
```

This resource will just install docker on the given host and expose its HTTP port.  
Next, let's analyse the steps needed to install docker:

```bash
# Install prerequisits
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg lsb-release

# Add dockers GPG key
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add the docker upstream
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

With some small tweaks, this gives us something a bit more appropriate for automation:

```bash
# Install prerequisits
sudo apt update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add dockers GPG key
sudo mkdir -m 0755 -p /etc/apt/keyrings
sudo rm -f /etc/apt/keyrings/docker.gpg
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# # Add the docker upstream
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/debian $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# # Install
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Save this as `install.sh`.  

We'll use the `HostModel.script` method to run the install script in a CRUDHandler.  
This allows us for trying to detect if docker is already installed in the `read` method,
speeding up subsequent deploys.  


file: _docker.py_

```Python
"""
Models for deploying and managing Docker on a remote host.
"""
from pathlib import Path

from eikobot.core.handlers import CRUDHandler, HandlerContext
from eikobot.core.helpers import EikoBaseModel
from eikobot.core.lib.std import HostModel


class DockerHostModel(EikoBaseModel):
    """
    Model that represents a machine that has docker installed
    """

    __eiko_resource__ = "DockerHost"

    host: HostModel
    port: int = 2357


class DockerHostHandler(CRUDHandler):
    """
    Installs docker on a remote host.
    """

    __eiko_resource__ = "DockerHost"

    async def _verify_install(self, ctx: HandlerContext, host: HostModel) -> bool:
        docker_version = await host.execute("sudo docker --version", ctx)
        return docker_version.returncode == 0

    async def _install(self, ctx: HandlerContext, host: HostModel) -> bool:
        """
        Install docker on a remote host.
        """
        script = (Path(__file__).parent / "install.sh").read_text()
        result = await host.script(script, "bash", ctx)
        if result.failed():
            return False

        return await self._verify_install(ctx, host)

    async def create(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, DockerHostModel):
            ctx.failed = True
            return

        if not await self._install(ctx, ctx.resource.host):
            ctx.failed = True
            return

        ctx.deployed = True

    async def read(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, DockerHostModel):
            ctx.failed = True
            return

        if not await self._verify_install(ctx, ctx.resource.host):
            return

        ctx.deployed = True
```

Using the `host.script` functions we can run whole scripts commands on the remote host.  
Note that the sudo password prompt is not bypassed, it is simply surpressed
by providing the password in a different way.  
Nor is the password stored on the remote machine.  

We also pass the `HandlerContext` to every call to `host.execute` asn `host.script`
as it allows for more acurate logging.  

We also added a verify install method that can be run to detect if instalation is required
and to see if the installation succeeded.  

At the end of the read method we set `ctx.deployed` to `True`
because if we're past the install verification the resource has been deployed.  

Now technically we already have everything required to just install docker
over ssh on a remote host.  

Before continuing to the next step, make sure of the following:

- You can access the required host
- You have sudo rights
- Optional: that you can create snapshots/save states of said machine

The last point comes in handy when testing models as it allows
for a quick reset if something doesn't work.  

Once you've made sure these things are set up, we'll create a `main.eiko` file.  
This file will be where we actually fill in the required info:

file: _main.eiko_

```Python
import std

from docker import DockerHost

docker_1 = DockerHost(
    std.Host(
        "192.168.123.123",
        password=std.get_pass("sudo password: "),
    )
)
```

We simply import `std` to use `Host`.
(Host is a model for a machine that can be remotely connected to using ssh)  
Then we use `std.get_pass` to get a password at compile time.  
(This allows us to not store the password in the model in case we want to save it in GIT)  

Now we can deploy the model:  

```bash
eiko@workstation:~/scenario_1$ eikobot deploy -f main.eiko
```

If one of the commands fails, it will be logged to the console,
although everything should deploy correctly.  
This process might take a while, depending on the speed of the remote machines internet
connection and/or it's disks and CPU.  

When trying to deploy this again, you'll note that it will deploy a lot faster.  

## Step 2: configuring Docker

Next we'll configure docker so we can access it over HTTP.  
Using HTTP will be easier as the responses will be structured json,
rather than CLI responses we have to manually parse ourselves.  
