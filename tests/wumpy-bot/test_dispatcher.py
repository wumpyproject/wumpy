import anyio
import pytest
from wumpy.bot import Event, EventDispatcher, Extension


# Helper event subclass
class DummyEvent(Event):
    NAME = 'DUMMY'

    def __init__(self) -> None:
        pass


def test_mixin():
    # EventDispatcher is a mixin and should forward arguments
    class Consumer:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

    class Parent(EventDispatcher, Consumer):
        ...

    args, kwargs = ('abc', 123, 987.0), {'name': 'Bob'}

    instance = Parent(*args, **kwargs)

    assert args == instance.args
    assert kwargs == instance.kwargs


def test_listener_decorator():
    dispatcher = EventDispatcher()

    # Test both with and without parenthesis

    @dispatcher.listener
    async def callback(event: DummyEvent):
        ...

    @dispatcher.listener()
    async def other_callback(other_event: DummyEvent):
        ...

    assert len(dispatcher.listeners.get(DummyEvent.NAME, [])) == 2


# We want to test that the tests work for both of these classes
@pytest.mark.parametrize('cls', [EventDispatcher, Extension])
class TestAddListener:
    """Test the various ways of adding listeners."""

    def test_correct_signatures(self, cls):
        dispatcher = cls()

        # Test various different correct signatures that should be
        # supported and added

        async def expected(event: DummyEvent):
            ...

        # async def pos_only(expected: DummyEvent, /):
        #     ...

        async def defaulted(event: DummyEvent = None):
            ...

        async def extra_defaulted(event: DummyEvent, other=None):
            ...

        async def extra_kwargs(event: DummyEvent, *, extra=None):
            ...

        dispatcher.add_listener(expected)
        # dispatcher.add_listener(pos_only)
        dispatcher.add_listener(defaulted)
        dispatcher.add_listener(extra_defaulted)
        dispatcher.add_listener(extra_kwargs)

        assert len(dispatcher.listeners.get(DummyEvent.NAME, [])) == 4

    def test_wrong_signatures(self, cls):
        dispatcher = cls()

        async def no_args():
            ...

        async def too_many_args(event: DummyEvent, other):
            ...

        async def kwargs(*, event: DummyEvent):
            ...

        async def wrong_order(other=None, event: DummyEvent = None):
            ...

        async def too_many_non_default(event: DummyEvent, other, another=None):
            ...

        with pytest.raises(TypeError):
            dispatcher.add_listener(no_args)

        with pytest.raises(TypeError):
            dispatcher.add_listener(too_many_args)

        with pytest.raises(TypeError):
            dispatcher.add_listener(kwargs)

        with pytest.raises(TypeError):
            dispatcher.add_listener(wrong_order)

        with pytest.raises(TypeError):
            dispatcher.add_listener(too_many_non_default)

    def test_non_async(self, cls):
        dispatcher = cls()

        def non_async(event: DummyEvent):
            ...

        with pytest.raises(TypeError):
            dispatcher.add_listener(non_async)  # type: ignore

    def test_not_event_subclass(self, cls):
        dispatcher = cls()

        async def incorrect(arg: int):
            ...

        with pytest.raises(TypeError):
            dispatcher.add_listener(incorrect)

    def test_same_name_events(self, cls):
        # Test that two different event subclasses with the same name
        # class variable gets added together
        shared_name = 'DUMB'

        class DumbEvent(Event):
            NAME = shared_name

        class DumberEvent(Event):  # Not a subclass of DumbEvent
            NAME = shared_name

        dispatcher = cls()

        async def dumb_callback(event: DumbEvent):
            ...

        async def dumber_callback(event: DumberEvent):
            ...

        dispatcher.add_listener(dumb_callback)
        dispatcher.add_listener(dumber_callback)

        assert len(dispatcher.listeners.get(shared_name, [])) == 2


@pytest.mark.parametrize('cls', [EventDispatcher, Extension])
class TestRemoveListener:
    def test_remove_no_event(self, cls):
        dispatcher = cls()

        @dispatcher.listener
        async def callback(event: DummyEvent):
            ...

        dispatcher.remove_listener(callback)

        assert len(dispatcher.listeners.get(DummyEvent.NAME, [])) == 0

    def test_remove_with_event(self, cls):
        dispatcher = cls()

        async def callback(event: DummyEvent):
            ...

        dispatcher.add_listener(callback)
        dispatcher.add_listener(callback)

        dispatcher.remove_listener(callback, event=DummyEvent.NAME)
        dispatcher.remove_listener(callback, event=DummyEvent)

        assert len(dispatcher.listeners.get(DummyEvent.NAME, [])) == 0

    def test_incorrect_event(self, cls):
        dispatcher = cls()

        @dispatcher.listener
        async def callback(event: DummyEvent):
            ...

        with pytest.raises(TypeError):
            dispatcher.remove_listener(callback, event=123)  # type: ignore

    def test_wrong_callback_signature(self, cls):
        dispatcher = cls()

        # This is a subset of the test_wrong_signatures() method in the
        # TestAddListener test group

        async def no_args():
            ...

        async def too_many_args(event: DummyEvent, other):
            ...

        with pytest.raises((TypeError, ValueError)):
            dispatcher.remove_listener(no_args)

        with pytest.raises((TypeError, ValueError)):
            dispatcher.remove_listener(too_many_args)

    def test_duplicate_not_removed(self, cls):
        dispatcher = cls()

        async def callback(event: DummyEvent):
            ...

        dispatcher.add_listener(callback)
        dispatcher.add_listener(callback)

        dispatcher.remove_listener(callback)

        # There should still be one reference of the callback in the dict
        assert len(dispatcher.listeners.get(DummyEvent.NAME, [])) == 1

    def test_not_registered(self, cls):
        dispatcher = cls()

        @dispatcher.listener
        async def registered(event: DummyEvent):
            ...

        # This one on the other hand isn't registered
        async def callback(event: DummyEvent):
            ...

        with pytest.raises(ValueError):
            dispatcher.remove_listener(callback)

    def test_bare_event(self, cls):
        dispatcher = cls()

        async def callback(event: Event):
            ...

        with pytest.raises(TypeError):
            dispatcher.add_listener(callback)


@pytest.mark.anyio
class TestDispatch:
    async def test_dispatched(self):
        dispatcher = EventDispatcher()

        # Test that multiple listeners are dispatched the correct
        # amount of times.

        expected = 5
        called = 0

        async def callback(event: DummyEvent):
            nonlocal called
            called += 1

        for _ in range(expected):
            dispatcher.add_listener(callback)

        async with anyio.create_task_group() as tg:
            dispatcher.dispatch(DummyEvent.NAME, tg=tg)

        assert called == expected

    async def test_correct_dispatched(self):
        # Test that the current event is dispatched
        class OtherEvent(Event):
            NAME = 'OTHER'

            def __init__(self) -> None:
                pass

        dispatcher = EventDispatcher()

        @dispatcher.listener
        async def callback(event: DummyEvent):
            pass

        @dispatcher.listener
        async def other_callback(event: OtherEvent):
            assert False, 'Wrong callback dispatched'

        async with anyio.create_task_group() as tg:
            dispatcher.dispatch(DummyEvent.NAME, tg=tg)

    async def test_correct_instance(self):
        # Test that the listener callback is dispatched with its
        # annotated subclass.
        shared_name = 'DUMB'

        class DumbEvent(Event):
            NAME = shared_name

            def __init__(self) -> None:
                pass

        class DumberEvent(Event):  # Not a subclass of DumbEvent
            NAME = shared_name

            def __init__(self) -> None:
                pass

        dispatcher = EventDispatcher()

        @dispatcher.listener
        async def dumb_callback(event: DumbEvent):
            assert isinstance(event, DumbEvent)

        @dispatcher.listener
        async def dumber_callback(event: DumberEvent):
            assert isinstance(event, DumberEvent)

        async with anyio.create_task_group() as tg:
            dispatcher.dispatch(shared_name, tg=tg)
