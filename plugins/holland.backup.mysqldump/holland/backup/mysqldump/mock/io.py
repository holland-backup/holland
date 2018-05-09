"""Mock IO access"""
from .storage import replace_builtins

def mock_io(mocker):
    replace_builtins()
