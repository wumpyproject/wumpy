import pytest
from wumpy.client import (
    Event, EventDispatcher, Extension, ExtensionFailure, ExtensionLoader
)
from wumpy.client.extension import _is_submodule


def test_is_submodule():
    # At the stage of when this is used all relative imports have been resolved
    # so this test only consists of absolute paths

    assert _is_submodule('wumpy', 'wumpy') is True
    assert _is_submodule('wumpy.extension', 'wumpy') is True
    assert _is_submodule('wumpy.interactions.commands.slash', 'wumpy.interactions') is True

    # Some of these are pretty stupid, but you need some tests that test the
    # obvious I guess..
    assert _is_submodule('wumpy', 'discord') is False
    assert _is_submodule('wumpy.models', 'discord.ext.commands') is False
    assert _is_submodule('wumpy.interactions', 'wumpy.commands') is False


def test_data_runtimeerror():
    ext = Extension()

    with pytest.raises(RuntimeError):
        # 'data' is not yet accessible because the extensions hasn't been given
        # it by being loaded.
        _ = ext.data


class TestExtensionTransfer:
    def test_callable(self):
        ext = Extension()
        dispatcher = EventDispatcher()

        unload = ext(dispatcher, {})
        unload(dispatcher)

    def test_data(self):
        ext = Extension()
        dispatcher = EventDispatcher()

        instance = object()
        ext.load(dispatcher, {'key': 'value', 'kwarg': 0, 'object': instance})

        assert ext.data == {'key': 'value', 'kwarg': 0, 'object': instance}


class TestExtensionLoader:
    def test_relative_no_package(self):
        loader = ExtensionLoader()

        with pytest.raises(TypeError):
            loader.load_extension('.abc:xyz')

    def test_relative_too_far(self):
        loader = ExtensionLoader()

        with pytest.raises(ValueError):
            loader.load_extension('......abc:xyz', __name__)

    def test_no_spec(self):
        loader = ExtensionLoader()

        with pytest.raises(ValueError):
            loader.load_extension('tests.wumpy.README:non_existant')

    def test_exec_exception(self):
        loader = ExtensionLoader()

        with pytest.raises(ExtensionFailure):
            loader.load_extension('tests.wumpy.extensions.raises:func')

    def test_bad_attribute(self):
        loader = ExtensionLoader()

        with pytest.raises(ValueError):
            loader.load_extension('tests.wumpy.extensions.empty:other')

    def test_non_callable(self):
        loader = ExtensionLoader()

        with pytest.raises(ExtensionFailure):
            loader.load_extension('tests.wumpy.extensions.non_callable:var')

    def test_loader_raises(self):
        loader = ExtensionLoader()

        with pytest.raises(ExtensionFailure):
            loader.load_extension('tests.wumpy.extensions.raises_load:loader')

    def test_data_passed(self):
        loader = ExtensionLoader()

        print('#' * 10, __name__)
        loader.load_extension('tests.wumpy.extensions.data_passed:loader', passed=True)
        # The test continues in that file

    def test_relative(self):
        loader = ExtensionLoader()

        loader.load_extension('.extensions.empty:ext', 'tests.wumpy')


class TestUnload:
    def test_relative_no_package(self):
        loader = ExtensionLoader()

        with pytest.raises(TypeError):
            loader.unload_extension('.abc:xyz')

    def test_relative_too_far(self):
        loader = ExtensionLoader()

        with pytest.raises(ValueError):
            loader.unload_extension('......abc:xyz', 'tests.wumpy')

    def test_raises_unload(self):
        loader = ExtensionLoader()
        loader.load_extension('tests.wumpy.extensions.raises_unload:loader')

        with pytest.raises(ExtensionFailure):
            loader.unload_extension('tests.wumpy.extensions.raises_unload')

    def test_unload_not_loaded(self):
        loader = ExtensionLoader()

        with pytest.raises(ValueError):
            loader.unload_extension('tests.wumpy.extensions.empty')
