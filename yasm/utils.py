from six import string_types


def on_event(name):
    def wrapper(func):
        func.on_event = name
        return staticmethod(func)
    return wrapper


def get_event_handlers(obj):
    handlers = {}
    for attr in dir(obj):
        if attr.startswith('__'):
            continue
        value = getattr(obj, attr)
        if getattr(value, 'on_event', ''):
            handlers[value.on_event] = value
    return handlers


# add_state/add_states can used as decorator
def add_state(obj, name, state=None, force=False, clone_machine=False):
    def wrapper(obj):
        if not hasattr(obj, 'machine'):
            raise TypeError('need init state obj first')
        if clone_machine:
            obj.machine = obj.machine.clone()
        obj.machine.add_state(name, state, force)
        return obj
    return wrapper


def add_states(states, initial=None, force=False, clone_machine=False):
    def wrapper(obj):
        if not hasattr(obj, 'machine'):
            raise TypeError('need init state obj first')
        if clone_machine:
            obj.machine = obj.machine.clone()
        obj.machine.add_states(states, initial, force)
        return obj
    return wrapper


def dispatch(instance, event):
    '''Dispatch an event to a state machine.

    If using nested state machines (HSM), it has to be called on a root
    state machine in the hierarchy.

    :param event: Event to be dispatched
    :type event: :class:`.Event`

    '''
    machine = instance.machine
    state = machine.get_state(instance.state)
    state._on(event, instance)
    transition = machine._get_transition(state, event, instance)
    if transition is None:
        return
    to_state = machine.get_state(transition['to_state'])

    before = transition['before']
    if isinstance(before, string_types):
        before = getattr(instance, before)
    if before:
        before(state, event, instance)
    machine._exit_state(state, event, instance, to_state)
    machine._enter_state(to_state, event, instance, state)
    after = transition['after']
    if isinstance(after, string_types):
        after = getattr(instance, after)
    if after:
        after(to_state, event, instance)
