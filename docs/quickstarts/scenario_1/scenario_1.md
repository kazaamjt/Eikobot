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

These instructions can handily be turned in to a handler:  

file: _docker.py_

```Python
"""
Models for deploying and managing Docker on a remote host.
"""
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

    async def _install(self, ctx: HandlerContext, host: HostModel) -> bool:
        """
        Install docker on a remote host.
        """
        apt_get_update = await host.execute_sudo("sudo apt-get update", ctx)
        if apt_get_update.failed():
            return False

        pre_req_installs = await host.execute_sudo(
            "sudo apt-get install -y ca-certificates curl gnupg lsb-release",
            ctx,
        )
        if pre_req_installs.failed():
            return False

        keyring_dir = await host.execute_sudo(
            "sudo mkdir -m 0755 -p /etc/apt/keyrings",
            ctx,
        )
        if keyring_dir.failed():
            return False

        gpg = await host.execute_sudo(
            "curl -fsSL https://download.docker.com/linux/debian/gpg | "
            "sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
            ctx,
        )
        if gpg.failed():
            return False

        docker_apt_file = await host.execute_sudo(
            'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] '
            'https://download.docker.com/linux/debian $(lsb_release -cs) stable" | '
            "sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
            ctx,
        )
        if docker_apt_file.failed():
            return False

        apt_get_update = await host.execute_sudo("sudo apt-get update", ctx)
        if apt_get_update.failed():
            return False

        docker_install = await host.execute_sudo(
            "sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
            ctx,
        )
        if docker_install.failed():
            return False

        return await self._verify_install(host, ctx)

    async def create(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, DockerHostModel):
            ctx.failed = True
            return

        if not await self._install(ctx, ctx.resource.host):
            ctx.failed = True
            return
```

Using the `host.execute` and `host.execute_sudo` functions, we can run
shell commands on the remote host.  
In many cases the `host.execute_sudo` version will be required,
as it sets up the ssh session in such a way that the sudo password prompt
doesn't break commands.  
Note that the sudo password prompt is not bypassed, it is simply surpressed
by providing the password in a different way.  
Nor is the password stored on the remote machine.  

We also pass the `HandlerContext` to every call to `host.execute` as
it allows for more acurate logging.  

Isolating the installation process to a seperate function,
allows us to keep the `create` method short, as it will grow more later.  

Let's add a verify install method that can be run to detect if instalation is required
and to see if the installation succeeded.  
Then let's call it from our read method and at the end of our install method:  

file: _docker.py_

```Python
    async def _verify_install(self, host: HostModel) -> bool:
        docker_version = await host.execute("docker --version")
        return docker_version.returncode == 0

    async def read(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, DockerHostModel):
            ctx.failed = True
            return

        if not self._verify_install(ctx.resource.host):
            return

        ctx.deployed = True
```

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
This process might take a while, depenging on the speed of the remote machines internet
and/or it's disks and CPU.  
