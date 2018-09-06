'''Python State Machine

Inspired by https://github.com/pgularski/yasm
Inspired by https://github.com/pytransitions/transitions

The goal of this library is to give you a close to the State Pattern
simplicity with much more flexibility. And, if needed, the full state machine
functionality, including
`FSM <https://en.wikipedia.org/wiki/Finite-state_machine>`_,
`HSM <https://en.wikipedia.org/wiki/UML_state_machine
#Hierarchically_nested_states>`_,
`PDA <https://en.wikipedia.org/wiki/Pushdown_automaton>`_ and other tasty
things.

Goals:
    - Provide a State Pattern-like behavior with more flexibility
    - Be explicit and don't add any code to objects
    - Handle directly any kind of event (not only strings) - parsing strings is
      cool again!
    - Keep it simple, even for someone who's not very familiar with the FSM
      terminology

----

.. |Machine| replace:: :class:`~yasm.Machine`
.. |State| replace:: :class:`~yasm.State`
.. |Hashable| replace:: :class:`~collections.Hashable`
.. |Iterable| replace:: :class:`~collections.Iterable`
.. |Callable| replace:: :class:`~collections.Callable`

'''

from .core import State, Machine, Event, state_machine
from .nested import NestedState, NestedMachine
from .utils import on_event, add_state, add_states, dispatch


__all__ = [
    'state_machine', 'add_states', 'add_state', 'on_event', 'dispatch',
    'State', 'Machine', 'Event', 'NestedState', 'NestedMachine',
]

__version__ = '0.1.0a1'
