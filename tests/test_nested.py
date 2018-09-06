# -*- coding: utf-8 -*-
from unittest import TestCase
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from yasm.core import Event, state_machine
from yasm.nested import NestedState, NestedMachine
from yasm import error
from yasm.utils import dispatch

state_separator = NestedState.separator


@state_machine('test', machine_class=NestedMachine)
class Stuff(object):
    pass


class TestNested(TestCase):

    def setUp(self):
        Stuff.machine._reset()

    def tearDown(self):
        NestedState.separator = state_separator

    def test_initial(self):
        # Define with list of dictionaries
        states = ['A', 'B', {'name': 'C', 'children': ['1', '2', '3']}, 'D']
        m = Stuff.machine
        m.add_states(states, 'A', force=True)

        self.assertIsNotNone(m.initial)
        self.assertEqual(m.initial, 'A')

        with self.assertRaises(error.AlreadyHasInitialState):
            m.set_initial_state('C')
        m.set_initial_state('C', force=True)
        self.assertEqual(m.initial, 'C')

        m.set_initial_state('C.1', force=True)
        self.assertEqual(m.initial, 'C.1')
        with self.assertRaises(error.NoState):
            m.set_initial_state('C.0', force=True)

    def test_add_state(self):
        m = Stuff.machine
        self.assertDictEqual(m.states, {})

        states = ['A', 'B', {'name': 'C', 'children': ['1', '2']}, 'D']
        m.add_states(states)
        self.assertTrue(len(m.states) == 6, m.states)

        with self.assertRaises(error.AlreadyHasState):
            m.add_state('C.1')

    def test_get_state(self):
        states = ['A', 'B', {'name': 'C', 'children': ['1', '2']}, 'D']
        m = Stuff.machine
        m.add_states(states, initial='A', force=True)
        self.assertIsNotNone(m.get_state('A'))
        self.assertIsNotNone(m.get_state('C.1'))

        with self.assertRaises(error.NoState):
            m.get_state('C.0')

    def test_add_transition(self):
        states = ['A', 'B', {'name': 'C', 'children': ['1', '2', '3']}, 'D']
        # Define with list of dictionaries
        transitions = [
            {'event': 'walk', 'from_state': 'A', 'to_state': 'B'},
            {'event': 'run', 'from_state': 'B', 'to_state': 'C'},
            {'event': 'sprint', 'from_state': 'C', 'to_state': 'D'},
            {'event': 'run', 'from_state': 'C', 'to_state': 'C.1'},
        ]
        m = Stuff.machine
        m.add_states(states, initial='A', force=True)
        m.add_transitions(transitions)
        self.assertEqual(len(m.transitions), 11)

        # Define with list of lists
        transitions = [
            ['A', 'B', 'walk'],
            ['B', 'C', 'run'],
            ['C', 'D', 'sprint']
        ]
        m._reset()
        m.add_states(states, initial='A')
        m.add_transitions(transitions)

        with self.assertRaises(error.NoState):
            m.add_transition('C.0', 'B', 'walk')

        with self.assertRaises(error.NoState):
            m.add_transition('A', 'C.0', 'walk')

    def test_dispatch(self):
        mock = MagicMock()

        def callback(state, event, instance):
            mock()

        def master(state, event, instance):
            return instance.is_manager

        state = NestedState('A')
        state.handlers['advance'] = callback
        states = [state, 'B', {'name': 'C', 'children': ['1', '2']}]
        transitions = [
            {'event': 'advance', 'from_state': 'A', 'to_state': 'B',
             'conditions': '!is_manager', 'after': callback},
            {'event': 'advance', 'from_state': 'A', 'to_state': 'C.1',
             'conditions': 'is_manager', 'after': 'on_advance'},
            {'event': 'advance', 'from_state': 'B', 'to_state': 'C.2',
             'conditions': master},
        ]
        m = Stuff.machine
        m.add_states(states)
        m.add_transitions(transitions)
        m.set_initial_state('A')

        s = Stuff()
        s.is_manager = False
        dispatch(s, Event('advance'))
        self.assertEqual(s.state, 'B')
        self.assertTrue(mock.called)
        self.assertEqual(mock.call_count, 2)

        s.is_manager = True
        dispatch(s, Event('advance'))
        self.assertEqual(s.state, 'C.2')

        s = Stuff()
        s.is_manager = True
        s.on_advance = callback
        dispatch(s, Event('advance'))
        self.assertEqual(s.state, 'C.1')

    # def test_add_custom_state(self):
    #     s = self.stuff
    #     s.machine.add_states([{'name': 'E', 'children': ['1', '2', '3']}])
    #     s.machine.add_transition('go', '*', 'E%s1' % State.separator)
    #     s.machine.add_transition('run', 'E', 'C.3.a')
    #     s.go()
    #     s.run()

    def test_enter_exit_nested_state(self):
        mock = MagicMock()

        def callback(state, event, instance, other_state):
            mock()
        states = [
            'A', 'B',
            {'name': 'C', 'on_enter': callback, 'on_exit': callback,
             'children': [{'name': '1', 'on_exit': callback}, '2', '3']},
            'D'
        ]
        transitions = [['A', 'C.1', 'go'], ['C', 'D', 'go']]

        m = Stuff.machine
        m.add_states(states=states, initial='A')
        m.add_transitions(transitions)
        s = Stuff()
        dispatch(s, Event('go'))
        self.assertEqual(s.state, 'C.1')
        self.assertTrue(mock.called)
        self.assertEqual(mock.call_count, 1)
        dispatch(s, Event('go'))
        self.assertEqual(s.state, 'D')
        self.assertEqual(mock.call_count, 3)

    def test_example_one(self):
        states = [
            'standing', 'walking',
            {'name': 'caffeinated', 'children': ['dithering', 'running']}
        ]
        transitions = [['standing', 'walking', 'walk'],
                       ['walking', 'standing', 'stop'],
                       ['*', 'caffeinated', 'drink'],
                       ['caffeinated', 'caffeinated.running', 'walk'],
                       ['caffeinated', 'standing', 'relax']]
        machine = Stuff.machine
        machine.add_states(states=states, initial='standing')
        machine.add_transitions(transitions)

        s = Stuff()
        dispatch(s, Event('walk'))
        dispatch(s, Event('stop'))
        dispatch(s, Event('drink'))
        self.assertEqual(s.state, 'caffeinated')
        dispatch(s, Event('walk'))
        self.assertEqual(s.state, 'caffeinated.running')
        with self.assertRaises(error.InvalidTransition):
            dispatch(s, Event('stop', raise_invalid_transition=True))
        dispatch(s, Event('relax'))
        self.assertEqual(s.state, 'standing')
