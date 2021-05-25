import os
import sys
import pytest

# make src visible to pytest
module_path = os.path.abspath(os.path.join('../src'))
if module_path not in sys.path:
    sys.path.insert(1, module_path)


from src.utils import *

def test_any_none():
    """
    pytest for the any_none function. The any_none is 
    function expected to return an empty list if there
    are no None arguments passed, otherwise a populated 
    list of as many Nones are passed.
    """
    # test arguments
    args = None, "a", 1, 1.1, [], {}, True 

    assert len(any_none(*args)) > 0 
    assert len(any_none(*args[1:])) == 0