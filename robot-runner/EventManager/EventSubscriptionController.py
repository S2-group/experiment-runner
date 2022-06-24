from typing import Callable, List, Tuple
from EventManager.Models.RunnerEvents import RunnerEvents

class EventSubscriptionController:
    __call_back_register: dict = dict()

    @staticmethod
    def subscribe_to_single_event(event: RunnerEvents, callback_method: Callable):
            EventSubscriptionController.__call_back_register[event] = callback_method

    @staticmethod
    def subscribe_to_multiple_events(subscriptions: List[Tuple[RunnerEvents, Callable]]):
        for sub in subscriptions:
            event, callback = sub[0], sub[1]
            EventSubscriptionController.subscribe_to_single_event(event, callback)

    @staticmethod
    def raise_event(event: RunnerEvents, runner_context=None):
        try:
            event_callback = EventSubscriptionController.__call_back_register[event]
        except KeyError:
            return None

        if runner_context:
            return event_callback(runner_context)
        else:
            return event_callback()

    @staticmethod
    def get_event_callback(event: RunnerEvents):
        try:
            return EventSubscriptionController.__call_back_register[event]
        except KeyError:
            return None
