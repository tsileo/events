# todos

<a href="https://github.com/tsileo/events/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-ISC-red.svg?style=flat" alt="License"></a>
<a href="https://github.com/ambv/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

Manage events from the command line.
Talks to a remote CalDAV server.

## Install

    $ pip install git+https://github.com/tsileo/events
    # Create the config file
    $ vim ~/.config/events.yaml

### Config

```yaml
url: 'https://user@pass:mycal.dav'
```

## Usage

See the help.

    $ events -h
