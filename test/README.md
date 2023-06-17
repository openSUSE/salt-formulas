# Testing

Formulas in this repository are planned to ship with integration tests using Pytest/Testinfra.

## Using Scullery

For easy automated testing using Vagrant virtual machines the experimental [Scullery](https://git.com.de/Georg/scullery) script can be used:

`$ scullery --config test/scullery.ini --suite <name of suite> --test`

The tool will take care of:
  - configuring a virtual machine
  - installing the example Salt pillar data
  - installing the Salt states
  - applying the Salt states
  - executing Pytest
  - cleaning up

Available suites can be found in the configuration file:

`$ grep suite. test/scullery.ini`

The idea is to have suites with the naming structure:

`suite.<formula>.<operating system>.<layout>`

## Manually

Of course, Pytest can be used directly by pointing it towards one or multiple hosts the tests should be performed against. Example using SSH:

`$ pytest --hosts=foo.example.com,bar.example.com some-formula/tests/test_example.py`

Visit the [Testinfra documentation](https://testinfra.readthedocs.io/en/latest/backends.html) for more connection options. By default, the tests will be performed against the local machine.
