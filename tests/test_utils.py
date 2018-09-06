from unittest import TestCase

from yasm.core import Event, state_machine
from yasm import error
from yasm.utils import on_event, get_event_handlers, dispatch


@state_machine('test')
class Stuff(object):

    @on_event('off_duty')
    def off_duty(self):
        pass


class TestUtils(TestCase):

    def test_on_event(self):
        self.assertEqual(Stuff.off_duty.on_event, 'off_duty')

    def test_get_event_handlers(self):
        self.assertDictEqual(
            get_event_handlers(Stuff), {'off_duty': Stuff.off_duty}
        )

    def test_switch_state(self):
        # private handling
        states = ['A', 'B', 'C', 'D']
        transitions = [['A', 'C', 'go'], ['C', 'D', 'go']]

        m = Stuff.machine
        m.add_states(states=states, initial='A')
        m.add_transitions(transitions)

        s = Stuff()
        with self.assertRaises(error.InvalidTransition):
            dispatch(s, Event('run', raise_invalid_transition=True))

        dispatch(s, Event('__switch__', input='B'))
        self.assertEqual(s.state, 'B')
