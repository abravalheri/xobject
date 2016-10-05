.. image:: https://cloud.githubusercontent.com/assets/320755/19127648/3aa3d8ba-8b16-11e6-9c6e-4f63ce0c7379.png
    :align: center
    :alt:


**********************

=======
xobject
=======

Track mutations in python objects.

.. warning::

   Not fully featured yet.
   Until version 1.0.0, API should be considered unstable.


What's this all about?
======================

Establishing a save point for python objects and identifying which changes have
occurred since it can be super useful. For example, someone may wish to discard
all the modifications and reload the object state from save point.  Others can
try to perform some optimizations by adopting a lazy approach and just
triggering actions after a save point is created, based only on the
changed properties.

This project provides base classes and decorators to enable these features,
with minimal requirement. ``xobject`` also provides a *event-emitter*
mechanism (a synchronous pub/sub variation of the *observer* pattern) to
monitor changes and perform custom actions before and after they take place.


Installation
============

.. code-block:: bash

   sudo pip install xobject
   # drop sudo if you are using a local installation or virtualenv-like tools


Quickstart
==========

The example below shows a minimal ``xobject`` usage:

.. code-block:: python

    from __future__ import print_function
    from xobject import XObject

    class BankAccount(XObject):
       def __init__(self, owner):
           self.internal_state = {'owner': owner, 'balance': 0}
           super(User, self).__init__()

       def withdraw(self, amount):
           self.internal_state['balance'] -= amount
           return amount

       def deposit(self, amount):
           self.internal_state['balance'] += amount

       @property
       def balance(self):
           return self.internal_state['balance']

    account = BankAccount('John Doe')

    account.deposit(300)
    account.is_dirty
    # => True
    account.enumerate_changes()
    # => {update: {'balance': 300}}
    account.commit()
    account.is_dirty
    # => False
    account.enumerate_changes()
    # => {}

    account.withdraw(250)
    account.enumerate_changes()
    # => {update: {'balance': 50}}
    account.rollback()
    account.balance
    # => 300
    account.is_dirty
    # => False

In order to subclass ``XObject``, it is necessary to define a
``internal_state`` property, which value must be a primitive python dict
(by default, ``XObject`` uses and empty dict if ``internal_state`` not defined).
The method ``commit`` can be then used to save the object state and consolidate
the last changes. Before calling ``commit``, changes can be monitored using
``enumerate_changes`` method or the ``is_dirty`` property.
There is also a ``rollback`` method that discard all the uncommitted changes
and returns the object to the previous state.

It is important to always keep ``internal_state`` up-to-date.
For complex usages, a dynamic property may be suitable:

.. code-block:: python

    @property
    def internal_state(self):
        ...
        # returns a python primitive dict

    @internal_state.setter
    def internal_state(self, state_dict):
        ...
        # store the state

.. note::

    Internally ``XObject`` uses
    `jsondiff <https://github.com/ZoomerAnalytics/jsondiff>`_ package with
    ``explicit`` syntax to enumerate changes.


Sentinel
--------

A ``XObject`` instance has an especial ``sentinel`` property that implements
the `Event Emmiter pattern <https://gist.github.com/abravalheri/d137cf14652eb932f398cdffe06fc7c2#file-event-emitter-pattern-md>`_
and is used to monitor the object life cycle. By default, the following events
can be monitored:

+--------------------+---------------------------------------------------+
|     Event Name     |                 Handler Arguments                 |
+====================+===================================================+
| ``will_commit``    | ``instance``, ``saved_state``, ``pendding_state`` |
+--------------------+---------------------------------------------------+
| ``did_commit``     | ``instance``, ``current_state``                   |
+--------------------+---------------------------------------------------+
| ``will_rollback``  | ``instance``, ``saved_state``, ``pendding_state`` |
+--------------------+---------------------------------------------------+
| ``did_rollback``   | ``instance``, ``current_state``                   |
+--------------------+---------------------------------------------------+

.. code-block:: python

    def print_transition(account, old_state, new_state):
       old_balance = old_state['balance']
       new_balance = new_state['balance']
       print('balance will change from {} to {}', old_balance, new_balance)

    def print_balance(account, state):
       print('current ballance: ', state['balance'])

    account.sentinel.on('will_commit', print_transition)
    account.sentinel.on('did_commit', print_balance)
    money = account.withdraw(100)
    account.commit()
    # balance will change from 300 to 200
    # current ballance: 200

Sentinel events can be disabled/enabled by calling the ``silence`` method:

.. code-block:: python

    account.sentinel.silence()  # disable events
    ...  # perform some actions
    account.sentinel.silence(False)  # re-enable events


xproperties
-----------

The ``xproperties`` class decorator is a convenience tool that accepts
any number of string parameters and define them as tracked properties.
The ``XObject`` constructor will automatically accept keyword arguments for
``xproperties`` and set the initial internal state accordingly.

.. code-block:: python

    from xobject import XObject, xproperties

    @xproperties('name', 'email')
    class User(XObject):
       pass

    john = User(name='John Doe', email='john@doe.com')
    john.email
    # => 'john@doe.com'
    john.name = 'John Smith'
    john.enumerate_changes()
    # => {update: {'name': 'John Smith'}}

For each property, the following events will be automatically triggered:

+---------------------------------+---------------------------------+
|           Event Name            |        Handler Arguments        |
+=================================+=================================+
| ``<property_name>:will_access`` | ``instance``                    |
+---------------------------------+---------------------------------+
| ``<property_name>:did_access``  | ``instance``, ``current_value`` |
+---------------------------------+---------------------------------+
| ``<property_name>:will_change`` | ``instance``, ``new_value``     |
+---------------------------------+---------------------------------+
| ``<property_name>:did_change``  | ``instance``, ``new_value``     |
+---------------------------------+---------------------------------+

Additionally, it is possible to track custom computed properties using the
``xproperty`` decorator:

.. code-block:: python

    class ObjectWithProperties(XObject):
        @xproperty
        def custom_property(self):
            ...  # returns the computed value

        @custom_property.setter
        def custom_property(self, value):
            ...  # store the computed value

The overall effect of this decorator is wrap the function call with event
triggers. The previous example is roughly equivalent to:

.. code-block:: python

    class ObjectWithProperties(XObject):
        @property
        def custom_property(self):
            self.sentinel.emit('custom_property:will_access', self)
            value = ...  # custom computation
            self.sentinel.emit('custom_property:did_access', self, value)
            return value

        @custom_property.setter
        def custom_property(self, value):
            self.sentinel.emit('custom_property:will_change', self, value)
            ...  # compute and store the new value
            self.sentinel.emit('custom_property:did_change', self, value)


Note that using ``xproperties`` is equivalent to calling
``xproperty`` decorator for each argument:

.. code-block:: python

    @xproperties('some_property', ...)
    class SomeObject(XObject):
        pass

    # is equivalent to:

    class SomeObject(XObject):
        @xproperty
        def some_property(self, value):
            # just access internal dict
            return self.internal_state['custom_property']

        @custom_property.setter
        def some_property(self, value):
            # just store the new value in the internal dict
            self.internal_state['custom_property'] = value

        ...


Transactions
------------

Instances of ``XObject`` class are also equipped with the ``tansaction``
context manager. Using this method, it is possible to perform operations in
batch without all the intermediate event triggers. The following codes are
equivalent:


.. code-block:: python

    with user.transaction():
        ...
        user.name = 'Fulano da Silva'
        ...

.. code-block:: python

    try:
        user.sentinel.silence()
        try:
            ...
            user.name = 'Fulano da Silva'
            ...
        finally:
            user.sentinel.silence(False)
    except:
        user.rollback()
        raise
    else:
        user.commit()


Stuff Doesn't Work
==================

Any feedback you can give me on this would be gratefully received
(see section **Reporting a Bug** at |guidelines|_.).


Can I help?
===========

Yes, please! Contributions of any kind are welcome, and also feel free
to ask your questions!

Please take a look at the |guidelines|_.


.. |guidelines| replace:: Contribution Guidelines
.. _guidelines: http://xobject.readthedocs.io/en/latest/contributing.html
