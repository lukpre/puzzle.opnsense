# Copyright: (c) 2023, Fabio Bertagna <bertagna@puzzle.ch>, Puzzle ITC
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Tests for the plugins.module_utils.xml_utils module."""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from typing import Union, Optional
from xml.etree.ElementTree import Element

import pytest
from ansible_collections.puzzle.opnsense.plugins.module_utils import xml_utils


@pytest.mark.parametrize("input_data", [
    1,
    "foo",
    None
])
def test_dict_to_etree__primitive_values(input_data: Optional[Union[int, str]]) -> None:
    """
    Given a simple input dictionary, check that the xml tag takes the dict key
    value and the xml inner text is set as the dict value. E.g.:
    Given: {"test":1}
    Expected XML: <test>1</test>
    """
    test_tag: str = "test"
    output_etree: list[Element] = xml_utils.dict_to_etree(test_tag, input_data)

    assert len(output_etree) == 1
    assert output_etree[0].tag == test_tag
    assert output_etree[0].text == input_data


@pytest.mark.parametrize("input_data", [
    {"foo": 1},
    {"foo": "bar"},
    {"foo": 1, "bar": None},
])
def test_dict_to_etree__tags_on_simple_dicts(input_data: dict) -> None:
    """
    Given a simple input dictionary, check that the xml tag takes the dict key
    value and the xml inner text is set as the dict value. E.g.:
    Given: {"test":1}
    Expected XML: <test>1</test>
    """
    test_tag: str = "test"
    output_etree: list[Element] = xml_utils.dict_to_etree(test_tag, input_data)
    output_children: list[Element] = list(output_etree[0])
    assert len(output_etree) == 1
    assert output_etree[0].tag == test_tag
    assert output_etree[0].text is None
    assert len(output_children) == len(input_data)
    for out_child in output_children:
        assert out_child.tag in list(input_data.keys())


def test_dict_to_etree__dict_recursion() -> None:
    """
    Test that nested dict create elements recursively.
    {
        "foo" : {                   <foo>
            "bar" : {                   <bar>
                "test" : 1,                 <test>1</test>
                "john" : {                  <john>
                    "doe" : 1   =>              <doe>1</doe>
                }                           </john>
            }                           </bar>
        }                           </foo>
    }
    :return:
    """
    test_tag: str = "foo"
    input_dict: dict = {"bar": {"test": 1, "john": {"doe": 1}}}

    output_etree: list[Element] = xml_utils.dict_to_etree(test_tag, input_dict)

    assert len(output_etree) == 1
    assert output_etree[0].tag == test_tag
    assert output_etree[0].text is None
    children: list[Element] = list(output_etree[0])
    assert len(children) == 1
    assert children[0].tag == "bar"
    assert children[0].text is None
    children = list(children[0])
    assert len(children) == 2
    assert children[0].tag == "test"
    assert children[0].text == 1
    assert children[1].tag == "john"
    assert children[1].text is None
    children = list(children[1])
    assert len(children) == 1
    assert children[0].tag == "doe"
    assert children[0].text == 1


@pytest.mark.parametrize("input_data", [
    [1, 2, 3, 4],
    ["a", "b", "c", "d"]
])
def test_dict_to_etree__primitive_list(input_data: list) -> None:
    """
    A primitive input list (int/str) must return multiple elements.

                            <foo>1</foo>
    { "foo" : [1,2,3] } =>  <foo>2</foo>
                            <foo>3</foo>

    """
    test_tag: str = "foo"

    output_etree: list[Element] = xml_utils.dict_to_etree(test_tag, input_data)

    assert len(output_etree) == len(input_data)

    for actual_etree, expected_data in zip(output_etree, input_data):
        assert actual_etree.text == expected_data


def test_dict_to_etree__list_with_dicts_or_sub_lists() -> None:
    """
    An input list with dict elements must return multiple elements.

    {                                           <foo>
        "foo" : [                                   <bar>1</bar>
            {"bar":1},{"bar":2},{"bar":3}   =>      <bar>2</bar>
        ]                                           <bar>3</bar>
    }                                           </foo>

    """
    test_tag: str = "foo"
    input_list: list[dict] = [{"bar": 1}, {"bar": 2}, {"bar": 3}]
    output_etree: list[Element] = xml_utils.dict_to_etree(test_tag, input_list)

    assert len(output_etree) == 1
    children: list[Element] = list(output_etree[0])
    assert len(children) == 3
    for actual_etree, expected_data in zip(children, input_list):
        assert actual_etree.text == (expected_data[actual_etree.tag] or None)


def test_dict_to_etree__list_with_dicts_dict_flattening() -> None:
    """
    An input list with dict of which some could contain multiple items,
    must return a flattened xml structure.

    {                                           <foo>
        "foo" : [                                   <bar>1</bar>
            {"bar":1},{"bob":2, "cat":3}    =>      <bob>2</bob>
        ]                                           <cat>3</cat>
    }                                           </foo>

    """
    test_tag: str = "foo"
    input_list: list[dict] = [{"bar": 1}, {"bar": 2}, {"bar": 3}]
    output_etree: list[Element] = xml_utils.dict_to_etree(test_tag, input_list)

    assert len(output_etree) == 1
    children: list[Element] = list(output_etree[0])
    assert len(children) == 3
    assert children[0].text == 1
    assert children[1].text == 2
    assert children[2].text == 3
