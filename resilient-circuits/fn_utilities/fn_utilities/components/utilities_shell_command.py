# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
"""Function implementation"""

import logging
from resilient_circuits import ResilientComponent, function, handler, StatusMessage, FunctionResult, FunctionError


class FunctionComponent(ResilientComponent):
    """Component that implements Resilient function 'utilities_shell_command"""

    def __init__(self, opts):
        """constructor provides access to the configuration options"""
        super(FunctionComponent, self).__init__(opts)
        self.options = opts.get("fn_utilities", {})

    @handler("reload")
    def _reload(self, event, opts):
        """Configuration options have changed, save new values"""
        self.options = opts.get("fn_utilities", {})

    @function("utilities_shell_command")
    def _utilities_shell_command_function(self, event, *args, **kwargs):
        """Function: Runs a shell command."""
        try:
            # Get the function parameters:
            shell_command = kwargs.get("shell_command")  # text
            shell_param1 = kwargs.get("shell_param1")  # text
            shell_param2 = kwargs.get("shell_param2")  # text
            shell_param3 = kwargs.get("shell_param3")  # text

            log = logging.getLogger(__name__)
            log.info("shell_command: %s", shell_command)
            log.info("shell_param1: %s", shell_param1)
            log.info("shell_param2: %s", shell_param2)
            log.info("shell_param3: %s", shell_param3)

            # PUT YOUR FUNCTION IMPLEMENTATION CODE HERE
            #  yield StatusMessage("starting...")
            #  yield StatusMessage("done...")

            results = {
                "value": "xyz"
            }

            # Produce a FunctionResult with the results
            yield FunctionResult(results)
        except Exception:
            yield FunctionError()