#!/bin/sh
pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb --disable-warnings -v -rx -x --hosts=test --ssh-config=ssh_config apache_httpd-formula/tests/ "$@"
