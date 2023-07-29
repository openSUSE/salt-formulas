# Salt states for [Jenkins](https://www.jenkins.io/)

Expects packages from `isv:SUSEInfra:CI:Jenkins` and `devel:tools:building`.

## Available states

`jenkins.controller`

Installs and configures a Jenkins controller using [JCasC](https://github.com/jenkinsci/configuration-as-code-plugin).

`jenkins.agent`

Installs and configures a Jenkins agent.
