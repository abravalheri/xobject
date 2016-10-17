#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
"""Tests for sentinel"""
from six.moves import xrange  # pylint: disable=redefined-builtin

import pytest
from mock import MagicMock

from xobject.sentinel import Sentinel


@pytest.fixture
def sentinel():
    """Instantiate an Sentinel object"""
    return Sentinel()


@pytest.fixture
def callback():
    """Create a callable mock that knows when it was called"""
    return MagicMock()


def test_on(sentinel, callback):
    """Should register callback as listener"""
    sentinel.on('event', callback)
    event_listeners = sentinel.listeners.get('event')
    assert event_listeners
    assert isinstance(event_listeners, list)
    assert callback in event_listeners


def test_emit(sentinel, callback):
    """Should run callback"""
    test_on(sentinel, callback)
    args = (True, False, 'some string', [])
    kwargs = dict(test=True)
    sentinel.emit('event', *args, **kwargs)
    callback.assert_called_with(*args, **kwargs)


def test_off_without_args(sentinel, callback):
    """Should discard all registered listeners"""
    for i in xrange(4):
        sentinel.on('event_{}'.format(i), callback)

    listeners = sentinel.off()
    assert len(sentinel.listeners) == 0
    assert all(['event_{}'.format(i) in listeners for i in xrange(4)])


def test_off_with_just_event_name(sentinel, callback):
    """Should discard just listeners for the event"""
    for i in xrange(4):
        sentinel.on('event_{}'.format(i), callback)

    listeners = sentinel.off('event_0')
    assert len(listeners) == 1
    remaining = sentinel.listeners
    assert 'event_0' not in remaining
    assert all([remaining['event_{}'.format(i)] for i in xrange(1, 4)])


def test_off_with_callback(sentinel, callback):
    """Should discard just specific callback"""
    sentinel.on('event', callback)

    other_callback = MagicMock()
    for _ in xrange(4):
        sentinel.on('event', other_callback)

    listener = sentinel.off('event', callback)
    assert listener is callback
    remaining = sentinel.listeners['event']
    assert callback not in remaining
    assert other_callback in remaining


def test_once(sentinel, callback):
    """Should run callback just once"""
    sentinel.once('event', callback)
    sentinel.emit('event')
    callback.assert_called()
    sentinel.emit('event')
    callback.assert_called_once()


def test_silent(sentinel, callback):
    """Sould not run callbacks"""
    sentinel.on('event', callback)
    sentinel.silent = True
    sentinel.emit('event')
    callback.assert_not_called()
    sentinel.silent = False
    sentinel.emit('event')
    callback.assert_called_once()
