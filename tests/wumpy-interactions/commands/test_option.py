import inspect
from enum import Enum
from typing import AnyStr, Literal, Optional, Union

import pytest
from typing_extensions import Annotated
from wumpy.interactions import ApplicationCommandOption
from wumpy.interactions.commands.option import OptionClass, OptionType
from wumpy.interactions.utils import MISSING
from wumpy.models import InteractionMember, User


def test_implicit_required():
    option = OptionClass(123)
    assert option.required is False


def test_choices_list():
    option = OptionClass(choices=['A', 'B', 'C', 'D', 'E'])
    assert option.choices == {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E'}


class TestDetermineType:
    def test_enum_value(self):
        for value in ApplicationCommandOption:
            option = OptionClass(type=value)

            assert option.type == OptionType(value)

    def test_primitive(self):
        for annotation in OptionClass.type_mapping:
            option = OptionClass(type=annotation)

            assert option.type == OptionClass.type_mapping[annotation]

    def test_enum(self):
        class Numbers(int, Enum):
            first = 1
            second = 2
            third = 3

        option = OptionClass(type=Numbers)
        assert option.type == ApplicationCommandOption.integer
        assert option.choices == {'first': 1, 'second': 2, 'third': 3}

    def test_enum_not_override(self):
        class Numbers(int, Enum):
            first = 1
            second = 2
            third = 3

        option = OptionClass(type=str, choices={'Answer A': 'a', 'Answer B': 'b'})

        option.determine_type(Numbers)
        assert option.type == ApplicationCommandOption.string
        assert option.choices == {'Answer A': 'a', 'Answer B': 'b'}

    def test_anystr(self):
        option = OptionClass(type=AnyStr)

        assert option.type == ApplicationCommandOption.string

    def test_union_optional(self):
        option = OptionClass(type=Optional[str])
        assert option.type == ApplicationCommandOption.string

        option = OptionClass(type=Union[str, None])
        assert option.type == ApplicationCommandOption.string

    def test_union_int_float(self):
        option = OptionClass(type=Union[int, float])
        assert option.type == ApplicationCommandOption.number

        option = OptionClass(type=Union[float, int])
        assert option.type == ApplicationCommandOption.number

    def test_union_user_member(self):
        option = OptionClass(type=Union[User, InteractionMember])
        assert option.type == ApplicationCommandOption.user

    def test_unknown_union(self):
        option = OptionClass(type=Union[frozenset, bool])
        assert option.type is MISSING

    def test_annotated(self):
        cases = [
            (Annotated[int, str], ApplicationCommandOption.string),
            (Annotated[int, frozenset, str], ApplicationCommandOption.string),
            (Annotated[int, str, bool], ApplicationCommandOption.string),
            (Annotated[int, frozenset, str, bool], ApplicationCommandOption.string)
        ]

        for annotated, expected in cases:
            option = OptionClass(type=annotated)
            assert option.type == expected

    def test_bad_annotated(self):
        option = OptionClass(type=Annotated[int, frozenset])

        assert option.type is MISSING

    def test_literal_typeerror(self):
        with pytest.raises(TypeError):
            _ = OptionClass(type=Literal['A', 'B', 'C', 4])

    def test_literal_args_choices(self):
        option = OptionClass(type=Literal['X', 'Y', 'Z'])

        assert option.type == ApplicationCommandOption.string
        assert option.choices == {'X': 'X', 'Y': 'Y', 'Z': 'Z'}

    def test_literal_not_override(self):
        option = OptionClass(type=str)

        option.determine_type(Literal[1, 2, 3])

        assert option.type == ApplicationCommandOption.string

    def test_literal_not_override_choices(self):
        option = OptionClass(choices={'A': 'alphabet', '1': 'numbers'})

        option.determine_type(Literal[1, 2, 3])

        assert option.choices == {'A': 'alphabet', '1': 'numbers'}


class TestUpdate:
    def test_other_default(self):
        def func(param=123): ...

        signature = inspect.signature(func)
        option = OptionClass()

        option.update(signature.parameters['param'])

        assert option.default == 123
        assert option.required is False

    def test_option_default(self):
        def func(param: str = OptionClass()): ...  # type: ignore

        signature = inspect.signature(func)
        option = signature.parameters['param']

        option.default.update(option)

        assert option.default.type == ApplicationCommandOption.string

    def test_not_override(self):
        option = OptionClass(123, name='arg', required=True, type=int)

        def func(param: str = 'default'): ...

        signature = inspect.signature(func)
        option.update(signature.parameters['param'])

        assert option.default == 123
        assert option.name == 'arg'
        assert option.required is True
        assert option.type == ApplicationCommandOption.integer


class TestToDict:
    def test_choices(self):
        option = OptionClass(
            name='param', description='Some form of parameter',
            required=True, choices=['Yes', 'No', 'Other'],
            type=ApplicationCommandOption.string
        )

        assert option.to_dict() == {
            'name': 'param',
            'type': ApplicationCommandOption.string.value,
            'description': 'Some form of parameter',
            'required': True,
            'choices': [
                {'name': 'Yes', 'value': 'Yes'},
                {'name': 'No', 'value': 'No'},
                {'name': 'Other', 'value': 'Other'}
            ]
        }

    def test_min_max(self):
        option = OptionClass(
            name='number', description='Some arbitrary number',
            required=False, min=0, max=10, type=int
        )

        assert option.to_dict() == {
            'name': 'number',
            'type': ApplicationCommandOption.integer.value,
            'description': 'Some arbitrary number',
            'required': False,
            'min_value': 0,
            'max_value': 10
        }
