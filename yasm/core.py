from collections import defaultdict
from copy import deepcopy
from six import string_types

from .error import InvalidTransition
from .error import NoState
from .error import InvalidState
from .error import AlreadyHasState
from .error import AlreadyHasInitialState
from .utils import get_event_handlers


class Event(object):

    def __init__(self, name, input=None, propagate=True,
                 raise_invalid_transition=False, **cargo):
        self.name = name
        self.input = input
        self.propagate = propagate
        self.raise_invalid_transition = raise_invalid_transition
        self.cargo = cargo

    def __repr__(self):
        return '<Event {}, input={!r}, cargo={}>'.format(
            self.name, self.input, self.cargo,
        )


class State(object):

    def __init__(self, name='', on_enter=None, on_exit=None):
        self.name = name or self.__class__.__name__
        self.handlers = get_event_handlers(self)
        self.on_enter = on_enter or self.__class__.on_enter
        self.on_exit = on_exit or self.__class__.on_exit

    def _on(self, event, instance):
        if event.name in self.handlers:
            self.handlers[event.name](self, event, instance)

    def on_enter(self, event, instance, from_state):
        pass

    def on_exit(self, event, instance, to_state):
        pass

    def __repr__(self):
        return '<State {}, handlers={}>'.format(
            self.name, self.handlers.keys()
        )


class Machine(object):

    StateClass = State

    def __init__(self, name):
        self.name = name
        self.initial = None
        self.states = {}
        self.transitions = defaultdict(list)
        self.wildcard_transitions = defaultdict(list)

    def _create_state(self, name, *args, **kwargs):
        return self.StateClass(name, *args, **kwargs)

    def _get_transition(self, state, event, instance):
        transitions = self.transitions[(state.name, event.name)]
        if not transitions and event.raise_invalid_transition:
            raise InvalidTransition('{} cannot handle event {}'.format(
                state, event
            ))
        for transition in transitions:
            for cond, target in transition['conditions']:
                if isinstance(cond, list):
                    predicate = instance
                    for pre in cond:
                        predicate = getattr(predicate, pre)
                else:
                    predicate = cond
                if callable(predicate):
                    predicate = predicate(state, event, instance)
                if predicate != target:
                    break
            else:
                return transition
        return None

    def _enter_state(self, state, event, instance, from_state):
        state.on_enter(state, event, instance, from_state)
        instance.state = state.name

    def _exit_state(self, state, event, instance, to_state):
        state.on_exit(state, event, instance, to_state)
        instance.state = None

    def _init_instance(self, instance):
        '''Initialize states in the state machine.

        After a state machine has been created and all states are added to it,
        :func:`initialize` has to be called when creating instance of host.

        Note: should not called from outside, this method would reset instance
        attributes
        '''
        state = self.get_state(self.initial)
        instance.state = state.name
        state.on_enter(state, Event('initialize'), instance, None)

    def _reset(self):
        self.initial = None
        self.states = {}
        self.transitions = defaultdict(list)
        self.wildcard_transitions = defaultdict(list)

    def _validate_add_state(self, state_name, state, force):
        if not isinstance(state, State):
            raise InvalidState('`%r` is not a valid State' % state)
        if self.has_state(state_name) and not force:
            raise AlreadyHasState(
                '`%s` already has state: %s' % (self, state_name)
            )

    def _validate_transition(self, from_state, to_state, event):
        if not self.has_state(from_state) and from_state != '*':
            raise NoState('unknown from state "{0}"'.format(from_state))
        if not self.has_state(to_state):
            raise NoState('unknown to state "{0}"'.format(to_state))

    def _validate_initial_state(self, state_name, force):
        if not self.has_state(state_name):
            raise NoState('unknown initial state: {}'.format(state_name))
        if self.initial is not None and not force:
            raise AlreadyHasInitialState(
                'multiple initial states, now: {}'.format(self.initial)
            )

    def _prepare_transition(self, from_state, to_state, event,
                            conditions=None, before=None, after=None):
        _conditions = []
        if conditions is not None:
            if not isinstance(conditions, list):
                conditions = [conditions]
        else:
            conditions = []
        if from_state == '*' and event == '__switch__':
            conditions.append(
                lambda state, event, instance: event.input == to_state
            )
        for cond in conditions:
            if isinstance(cond, string_types):
                if cond.startswith('!'):
                    predicate, target = cond[1:].split('.'), False
                else:
                    predicate, target = cond.split('.'), True
            else:
                predicate, target = cond, True
            _conditions.append((predicate, target))
        return {
            'from_state': from_state,
            'to_state': to_state,
            'conditions': _conditions,
            'before': before,
            'after': after,
        }

    def clone(self):
        ins = self.__class__(self.name)
        ins.name = self.name
        ins.initial = self.initial
        ins.states = deepcopy(self.states)
        ins.transitions = deepcopy(self.transitions)
        ins.wildcard_transitions = deepcopy(self.wildcard_transitions)
        return ins

    def add_state(self, name, state=None, force=False):
        state = state or self._create_state(name)
        self._validate_add_state(name, state, force)
        self.states[name] = state
        # for internal use only
        self.add_transition('*', name, '__switch__')

    def add_states(self, states, initial=None, force=False):
        for state in states:
            if isinstance(state, string_types):
                self.add_state(state, force=force)
            elif isinstance(state, dict):
                state = self._create_state(**state)
                self.add_state(state.name, state, force=force)
            elif isinstance(state, State):
                self.add_state(state.name, state, force=force)
            elif issubclass(state, State):
                state = state()
                self.add_state(state.name, state, force=force)
        if initial:
            self.set_initial_state(initial, force=force)

    def has_state(self, state_name):
        return state_name in self.states

    def get_state(self, state_name):
        if state_name not in self.states:
            raise NoState('{} has no such state: {}'.format(self, state_name))
        return self.states[state_name]

    def set_initial_state(self, state_name, force=False):
        if isinstance(state_name, State):
            state_name = state_name.name
        elif isinstance(state_name, type) and issubclass(state_name, State):
            state_name = state_name.__name__
        self._validate_initial_state(state_name, force)
        self.initial = state_name

    def add_transition(self, from_state, to_state, event,
                       conditions=None, before=None, after=None):
        '''Add a transition to a state machine.

        All callbacks take two arguments - `state` and `event`. See parameters
        description for details.

        It is possible to create conditional if/elif/else-like logic for
        transitions. To do so, add many same transition rules with different
        condition callbacks. First met condition will trigger a transition, if
        no condition is met, no transition is performed.

        :param from_state: Source state
        :type from_state: |string|

        :param to_state: Target state.
            If it is `from_state`, then it's an `internal transition
            <https://en.wikipedia.org/wiki/UML_state_machine
             #Internal_transitions>`_
        :type to_state: |string|

        :param event: event that trigger the transition
        :type event: |string|

        :param conditions: Condition callback - if all returns `True`
            transition may be initiated.

            `condition` callback takes two arguments:

                - state: State before transition
                - event: Event that triggered the transition
        :type conditions: |Iterable| of |Callable|

        :param before: Action callback that is called right before the
            transition.

            `before` callback takes two arguments:

                - state: State before transition
                - event: Event that triggered the transition
        :type before: |Callable|

        :param after: Action callback that is called just after the transition

            `after` callback takes two arguments:

                - state: State after transition
                - event: Event that triggered the transition
        :type after: |Callable|

        '''
        self._validate_transition(from_state, to_state, event)
        transition = self._prepare_transition(
            from_state, to_state, event, conditions, before, after
        )
        if from_state == '*':
            transitions = self.wildcard_transitions[event]
            transitions.append(transition)
            for from_state in self.states:
                self.transitions[(from_state, event)] = transitions
        else:
            self.transitions[(from_state, event)].append(transition)

    def add_transitions(self, transitions):
        for transition in transitions:
            if isinstance(transition, list):
                self.add_transition(*transition)
            elif isinstance(transition, dict):
                self.add_transition(**transition)

    def reinit_instance(self, instance):
        state = self.get_state(self.initial)
        instance.state = state.name
        state._on(Event('reinit'), instance)

    def __repr__(self):
        return '<Machine: {}, states: {}>'.format(
            self.name, self.states.keys()
        )


def state_machine(name, machine_class=None):

    def wrapper(cls):
        cls.initiated_yasm = True
        cls.machine = (machine_class or Machine)(name)

        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            cls.machine._init_instance(self)
            original_init(self, *args, **kwargs)
        cls.__init__ = new_init
        return cls
    return wrapper
