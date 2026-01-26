# NetApp ONTAP formula test suite

These tests are intended to be run against a Salt master with access to an ONTAP simulator.
The workstation the test suite is run from needs HTTPS access to the same simulator in order to validate the results.
Configure the simulator with a `pytest` user and role in the correct SVM:

```
::> security login rest-role create -vserver mysvm -role pytest -api /api/storage -access readonly
Warning: ...

::> security login create -user-or-group-name pytest -application http -authentication-method password -role pytest -vserver mysvm
Please enter a password for user 'pytest': cats2023
Please enter it again: cats2023
```

Invocation:

`pytest -v -rx --hosts user@master --ssh-config /dev/null netapp_ontap-formula/tests/`
