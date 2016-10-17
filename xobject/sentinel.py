# -*- coding: utf-8 -*-
"""``EventEmitter`` pattern implementation.

Reference `<https://git.io/vPKRJ>`_
"""
import logging


class Sentinel(object):
    """``Subject`` equivalent class according to the ``Observer`` pattern.

    Attributes
    ----------
    listeners : dict
        Events associated with respective lists of callbacks.
    silent : boolean
        When ``True`` no event will be emitted.

    Examples
    --------
    The following code illustrates minimal usage::

        sentinel = Sentinel()
        sentinel.on('login', lambda: sentinel.logger.log('User logged in!'))
        sentinel.emit('login')
        # User logged in!
        sentinel.silent = True
        sentinel.emit('login')
        # (nothing happens)
        sentinel.off('login')
        # (all callbacks for event 'login' are removed)
    """

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.listeners = {}
        self.silent = False
        self.logger.debug('New sentinel created.')

    def on(self, event, callback):  # pylint: disable=invalid-name
        """Register a callback that will run every time an event is emitted.

        Arguments
        ---------
        event : str
            Name of the event to be monitored.
        callback : function
            Will be triggered when the event is emitted.
            The arguments for function may differ for each event.
        """
        event_listeners = self.listeners.get(event, [])
        event_listeners.append(callback)
        self.listeners[event] = event_listeners
        self.logger.debug('New listener for %s.', repr(event))

        return self

    def once(self, event, callback):
        """Register a callback to run just the first time an event is emitted.

        See Also
        --------
        on
        """
        def _self_destructible(*args, **kwargs):
            self.logger.debug('Call once listener for %s.', event)
            self.off(event, _self_destructible)
            return callback(*args, **kwargs)

        return self.on(event, _self_destructible)

    def off(self, event=None, callback=None):
        """Remove the callback for event.

        - `off(event, callback)` - Removes the callback for event;
        - `off(event)` - Removes all callbacks for event;
        - `off()` - Removes all callbacks for all events.
        """
        if event is None:
            stored, self.listeners = self.listeners, {}
            self.logger.debug('All listeners removed.')
            return stored

        if callback is None:
            event_listeners = self.listeners.pop(event, [])
            self.logger.debug('All listeners for %s removed.', repr(event))
            return event_listeners

        event_listeners = self.listeners.get(event, [])
        if callback in event_listeners:
            i = event_listeners.index(callback)
            removed = event_listeners[i]
            # Avoid remove in place
            self.listeners[event] = event_listeners[:i] + event_listeners[i+1:]
            self.logger.debug('Listener for %s removed.', repr(event))
            return removed

    def emit(self, event, *args, **kwargs):
        """Run all callbacks registered for event.

        Arguments
        ---------
        event : str
            Name associated with event
        *args : list
            Arguments which will be used to run callback.
        **kwargs : dict
            Keyword arguments which will be used to run callback.
        """
        if not self.silent and event in self.listeners:
            self.logger.debug('Call listeners for %s.', event)
            event_listeners = self.listeners[event]
            for callback in event_listeners:
                callback(*args, **kwargs)
        else:
            self.logger.debug('No listener for %s.', event)

        return self
