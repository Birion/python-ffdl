#  The MIT License (MIT)
#
#  Copyright (c) 2016-2019 Birion
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

#  The MIT License (MIT)
#
#  Copyright (c) 2016-2019 Birion
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import pytest
from pyffdl.utilities.misc import *


def test_list2text():
    assert list2text(["foo"]) == "foo"
    assert list2text(["foo", "bar"]) == "foo and bar"
    assert list2text(["foo", "bar", "baz"]) == "foo, bar, and baz"


def test_turn_into_dictionary():
    with pytest.raises(TypeError):
        turn_into_dictionary(7)
    with pytest.raises(TypeError):
        turn_into_dictionary([7])
    with pytest.raises(TypeError):
        turn_into_dictionary("Chapter: 7")
    assert turn_into_dictionary(["English"]) == {"Language": "English"}
    assert turn_into_dictionary(["Updated: 12.2.2019"]) == {"Updated": "12.2.2019"}
    assert turn_into_dictionary(["Pages: 173"]) == {"Pages": 173}


def test_in_dictionary():
    dic = {"foo": "bar", "baz": None, "1": 1, 1: "1"}
    assert in_dictionary(dic, "foo") == "bar"
    assert not in_dictionary(dic, "bar")
    assert in_dictionary(dic, "1") == 1
    assert in_dictionary(dic, 1) == "1"


def test_get_url_from_file():
    pass


def test_strlen():
    assert strlen([]) == 1
    assert strlen(list(range(10))) == 2
    with pytest.raises(TypeError):
        strlen(10)


def test_clean_text():
    with pytest.raises(TypeError):
        clean_text("string")
    with pytest.raises(TypeError):
        clean_text(7)
    with pytest.raises(TypeError):
        clean_text(18.7)
    assert clean_text({x for x in range(10)}) == "0123456789"
    assert clean_text([x for x in range(10)]) == "0123456789"
    assert clean_text(["foo", "bar"]) == "foobar"
    assert clean_text(["fo o", "ba          r"]) == "fo oba r"
    assert clean_text((" foo      ", " bar")) == "foobar"
