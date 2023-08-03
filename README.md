# Eikobot Desired State Engine

*The little Desired State Engine that made it so.*  

Eikobot is a desired state orchestrator.  
The basic idea is that you describe your infrastructure and eikobot
will make it happen.  

Eikobot is consists of the deployment engine and the Eiko language.  

The language is akin to python, as this is a commonly used language
and the language in which eikobot and eikobot plugins are written.  
It is an Object Oriented language that has some powerfull features.  
The most glaring thing is probably that the language has no functions,
but this is an omission by design.  

Some of it's notable features are:  

- Object oriented
- sees the infrastructure as a tree of resources, rather than a flatland
- completely stateless*

The quickest way to get started is probably by doing some of the [quickstarts](https://github.com/kazaamjt/Eikobot/blob/main/docs/quickstarts.md).  
For a more complete idea of how the language works,
please see the [language overview](https://github.com/kazaamjt/Eikobot/blob/main/docs/language_overview.md).  

(*If the model/modules are designed well.)  

## Installation

Eikobot requires python 3.10 or up and can be installed using pip.  

Here is an example of how to install Eikobot:  
(This should work on most platforms, although the python command is different if you are on windows)

```bash
python3.10 -m venv eikobot-venv
eikobot-venv/bin/pip install eikobot
```

You can now use the eikobot commands,
either by invoking them directly with their venv path:

```bash
eikobot-venv/bin/eikobot
```

Or by activating the venv first:

```bash
. eikobot-venv/bin/activate
eikobot
```
