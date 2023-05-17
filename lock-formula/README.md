# Salt lock module

This only contains the `lock` state module which prevents simultaneous executions of states. Useful during orchestration runs.

Named like a formula for easier packaging.

## Available states

`lock(name, path=/var/lib/salt/)`

Write a lock file.

`unlock(name, path=/var/lib/salt/)`

Deletes a lock file.

`check(name, path=/var/lib/salt/)`

Checks whether a lock file is present (i.e. the operation is currently locked).

## Orchestration example

```
{%- set lock = 'my_important_operation' %}

check_lock:
  lock.check:
    - name: '{{ lock }}'
    - failhard: True

lock:
  lock.lock:
    - name: '{{ lock }}'
    - failhard: True

# some important states go here

unlock:
  lock.unlock:
    - name: '{{ lock }}'
```
