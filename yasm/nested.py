from six import string_types

from .core import State, Machine
from .error import InvalidTransition


class NestedState(State):

    separator = '.'

    def __init__(self, name, on_enter=None, on_exit=None, parent=None,
                 initial=None):
        super(NestedState, self).__init__(name, on_enter, on_exit)
        self.parent = parent
        if parent:
            parent.children[self.name] = self
            self.name = parent.name + self.separator + self.name
        self.children = {}
        self.initial = initial

    def _on(self, event, instance):
        if event.name in self.handlers:
            self.handlers[event.name](self, event, instance)
        if self.parent and event.propagate:
            self.parent._on(event, instance)

    def __repr__(self):
        return '<NestedState {}, handlers={}>'.format(
            self.name, self.handlers.keys()
        )


class NestedMachine(Machine):

    StateClass = NestedState
    STACK_SIZE = 32

    def _get_transition(self, state, event, instance):
        target = state
        while 1:
            transitions = self.transitions[(target.name, event.name)]
            if transitions:
                break
            if not target.parent:
                raise InvalidTransition('{} cannot handle event {}'.format(
                    state, event
                ))
            target = target.parent
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

    def _get_top_state(self, state, other_state):
        ancestors = []
        other_ancestors = []
        while state.parent:
            ancestors.append(state.parent)
            state = state.parent
        while other_state.parent:
            other_ancestors.append(other_state.parent)
            other_state = other_state.parent

        top = None
        for ancestor, other_ancestor in zip(reversed(ancestors),
                                            reversed(other_ancestors)):
            if ancestor is other_ancestor:
                top = ancestor
            else:
                break
        return top

    def _enter_state(self, state, event, instance, from_state):
        instance.state = state.name
        top_state = event.cargo.get('top_state') or \
            self._get_top_state(state, from_state)
        path = [state]
        while state.parent and state.parent != top_state:
            path.append(state.parent)
            state = state.parent
        for state in reversed(path):
            state.on_enter(state, event, instance, from_state)

    def _exit_state(self, state, event, instance, to_state):
        state.on_exit(state, event, instance, to_state)
        top_state = self._get_top_state(state, to_state)
        while state.parent and state.parent != top_state:
            state = state.parent
            state.on_exit(state, event, instance, to_state)
        instance.state = None
        event.cargo['top_state'] = top_state

    def traverse(self, states, parent=None, remap={}):
        new_states = []
        for state in states:
            tmp_states = []
            # other state representations are handled almost like in the
            # base class but a parent parameter is added
            if isinstance(state, string_types):
                if state in remap:
                    continue
                tmp_states.append(self._create_state(state, parent=parent))
            elif isinstance(state, dict):
                if state['name'] in remap:
                    continue

                children = []
                if 'children' in state:
                    children = state.pop('children')
                p = self._create_state(parent=parent, **state)
                tmp_states.append(p)
                if children:
                    # Concat the state names with the current scope.
                    # The scope is the concatenation of all # previous parents.
                    # Call traverse again to check for more nested states.
                    tmp_states.extend(self.traverse(children, parent=p))
            elif isinstance(state, NestedState):
                tmp_states.append(state)
            else:
                raise ValueError(
                    "{} is not an instance of NestedState "
                    "required by NestedMachine.".format(state)
                )
            new_states.extend(tmp_states)

        duplicate_check = set()
        for s in new_states:
            name = s.name
            if name in duplicate_check:
                raise ValueError(
                    "State %s cannot be added since it is already in "
                    "state list %s.".format(name, [n.name for n in new_states])
                )
            duplicate_check.add(name)
        return new_states

    def add_states(self, states, initial=None, force=False):
        states = self.traverse(states)
        super(NestedMachine, self).add_states(states, initial, force)

    # def set_previous_leaf_state(self, event=None):
    #     '''Transition to a previous leaf state. This makes a dynamic transition  # noqa
    #     to a historical state. The current `leaf_state` is saved on the stack
    #     of historical leaf states when calling this method.

    #     :param event: (Optional) event that is passed to states involved in the  # noqa
    #         transition
    #     :type event: :class:`.Event`

    #     '''
    #     if event is not None:
    #         event.state_machine = self
    #     from_state = self.leaf_state
    #     try:
    #         to_state = self.state_stack[-1]
    #     except IndexError:
    #         return
    #     top_state = self._exit_states(event, from_state, to_state)
    #     self._enter_states(event, top_state, to_state)

    # def revert_to_previous_leaf_state(self, event=None):
    #     '''Similar to :func:`set_previous_leaf_state`
    #     but the current leaf_state is not saved on the stack of states. It
    #     allows to perform transitions further in the history of states.

    #     '''
    #     self.set_previous_leaf_state(event)
    #     try:
    #         self.state_stack.pop()
    #     except IndexError:
    #         return
