==============
grains-formula
==============

A formula that handles /etc/salt/grains (in order to create custom grains), and
populates its content based on pillars. For more information on custom grains
(and grains in general) please consult the `grains documentation
<https://docs.saltstack.com/en/latest/topics/grains/#grains-in-etc-salt-grains>`_.

.. note::

    See the full `Salt Formulas installation and usage instructions
    <http://docs.saltstack.com/en/latest/topics/development/conventions/formulas.html>`_.

Available states
================

.. contents::
    :local:

``grains``
----------

Installs the /etc/salt/grains file and manages its content.
