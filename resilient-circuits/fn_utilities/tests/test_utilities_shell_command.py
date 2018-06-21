# -*- coding: utf-8 -*-
"""Tests using pytest_resilient_circuits"""

from __future__ import print_function
import pytest
from resilient_circuits.util import get_config_data, get_function_definition
from resilient_circuits import SubmitTestFunction, FunctionResult

PACKAGE_NAME = "fn_utilities"
FUNCTION_NAME = "utilities_shell_command"

# Read the default configuration-data section from the package
config_data = get_config_data(PACKAGE_NAME)

# Provide a simulation of the Resilient REST API (uncomment to connect to a real appliance)
resilient_mock = "pytest_resilient_circuits.BasicResilientMock"


def call_utilities_shell_command_function(circuits, function_params, timeout=10):
    # Fire a message to the function
    evt = SubmitTestFunction("utilities_shell_command", function_params)
    circuits.manager.fire(evt)
    event = circuits.watcher.wait("utilities_shell_command_result", parent=evt, timeout=timeout)
    assert event
    assert isinstance(event.kwargs["result"], FunctionResult)
    pytest.wait_for(event, "complete", True)
    return event.kwargs["result"].value


class TestUtilitiesShellCommand:
    """ Tests for the utilities_shell_command function"""

    def test_function_definition(self):
        """ Test that the package provides customization_data that defines the function """
        func = get_function_definition(PACKAGE_NAME, FUNCTION_NAME)
        assert func is not None

    @pytest.mark.parametrize("shell_command, shell_param1, shell_param2, shell_param3, expected_results", [
        ("text", "text", "text", "text", {"value": "xyz"}),
        ("text", "text", "text", "text", {"value": "xyz"})
    ])
    def test_success(self, circuits_app, shell_command, shell_param1, shell_param2, shell_param3, expected_results):
        """ Test calling with sample values for the parameters """
        function_params = { 
            "shell_command": shell_command,
            "shell_param1": shell_param1,
            "shell_param2": shell_param2,
            "shell_param3": shell_param3
        }
        results = call_utilities_shell_command_function(circuits_app, function_params)
        assert(expected_results == results)