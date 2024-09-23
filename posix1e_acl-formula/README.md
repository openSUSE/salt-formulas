Formula to assist with POSIX.1e [0] ACLs, providing extension and state module alternatives to the `linux_acl` equivalents shipped with Salt.
The upstream Salt modules were deemed to miss features which were not easy to implement given the use of octal mathematics. The modules shipped with this formula utilize the [pyacl](https://github.com/tacerus/pyacl) library which aims to provide a simple, high level, abstraction over ACLs, utilizing the [pylibacl](https://github.com/iustin/pylibacl) low level library underneath.

[0] These are theoretically not a thing, as the associated standard was never approved, but they are widely implemented, for example in Linux.
