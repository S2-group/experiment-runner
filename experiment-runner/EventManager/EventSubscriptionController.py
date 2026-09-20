from typing import Callable, List, Tuple
from EventManager.Models.RunnerEvents import RunnerEvents
from ConfigValidator.CustomErrors.BaseError import BaseError

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
        try:
            if runner_context:
                return event_callback(runner_context)
            else:
                return event_callback()
        except Exception as e:
            raise BaseError(f"Error in event handler for {event.name}: {str(e)}")

    @staticmethod
    def get_event_callback(event: RunnerEvents):
        try:
            return EventSubscriptionController.__call_back_register[event]
        except KeyError:
            return None
