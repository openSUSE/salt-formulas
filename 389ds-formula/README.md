# Salt formula for the 389 Directory Server

## Available states

`389ds.server`

Installs and configures 389-DS instances.

`389ds.data`

Manages a tree of LDAP objects.

## Available modules

The formula ships with various `389ds` execution and state modules. These contain various functions, intended primarily for supporting the states, but partially also useful for general administration. Reference the function comments for details.

## Passphrases

For managing user, passphrases should be provided in a hashed format, the same way as in a LDIF file. Hashes can be generated through standard means, for example:

- `/usr/sbin/slappasswd -h '{PBKDF2-SHA512}' -o module-load=pw-pbkdf2` from the `openldap2` and `openldap2-contrib` packages
- `pwdhash` from the `389-ds` package (discouraged, as this one forces one to pass the plain text secret on the command line)
- `ldap_pbkdf2_sha512.hash(...)` from the `passlib.hash` library in Python (`python3-passlib`)

## Caveats

Currently there are some known limitations.

- Base configuration (the `config` part of the pillar) is only considered during initial bootstrapping. Upon changes to the `config` pillar, the template for `dscreate` will be updated on disk, but changes will not be automatically loaded.
- The module for managing data will connect to the LDAP server through the default UNIX domain socket opened by 389-DS and authenticate using SASL EXTERNAL authentication, meaning the Salt minion has the same level of LDAP access as the system user it is running under.
- Attributes listed under objects in the `data` pillar must be listed in the same order as later ordered by 389-DS. This is particularly relevant for attributes such as `objectClass`, where 389-DS will not respect the insertion order, causing the state to loose idempotency by always reporting changes (and the problem might not immediately be obvious, because Salt currently sorts both new and old attributes in the changes output).
  * https://github.com/saltstack/salt/pull/68628
  * https://github.com/python-ldap/python-ldap/pull/604
