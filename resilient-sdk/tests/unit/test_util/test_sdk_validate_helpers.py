#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import difflib
import os

import mock
import pkg_resources
from mock import patch
from resilient_sdk.util import (constants, sdk_validate_configs,
                                sdk_validate_helpers)
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue
from tests.shared_mock_data import mock_paths


def test_selftest_validate_resilient_circuits_installed():

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.get_package_version") as mock_package_version:
        mock_package_version.return_value = pkg_resources.parse_version(constants.RESILIENT_LIBRARIES_VERSION)
        
        result = sdk_validate_helpers.selftest_validate_resilient_circuits_installed(sdk_validate_configs.selftest_attributes[0])
        assert isinstance(result[0], bool)
        assert isinstance(result[1], SDKValidateIssue)

        assert len(result) == 2
        assert result[0]
        assert result[1].solution is ""
        assert "selftest" in result[1].name


def test_valid_selftest_validate_package_installed():

    mock_package_name = "resilient-sdk"
    # path_to_package is only used for outputting a solution to install
    mock_path_to_package = "fake/path/to/package"

    # positive case
    attr_dict = sdk_validate_configs.selftest_attributes[1]
    result = sdk_validate_helpers.selftest_validate_package_installed(attr_dict, mock_package_name, mock_path_to_package)

    assert len(result) == 2
    assert result[0]
    assert result[1].solution is ""


def test_invalid_selftest_validate_package_installed():

    mock_package_name = "fake-package-not-found"
    # path_to_package is only used for outputting a solution to install
    mock_path_to_package = "fake/path/to/package"

    # negative case
    attr_dict = sdk_validate_configs.selftest_attributes[1]
    result = sdk_validate_helpers.selftest_validate_package_installed(attr_dict, mock_package_name, mock_path_to_package)

    assert len(result) == 2
    assert result[0] is False
    assert mock_path_to_package in result[1].solution
    assert "is not installed" in result[1].description

def test_valid_selftest_validate_selftestpy_file_exists(fx_copy_fn_main_mock_integration):

    attr_dict = sdk_validate_configs.selftest_attributes[2]

    path_selftest = os.path.join(mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_UTIL, "selftest.py")

    result = sdk_validate_helpers.selftest_validate_selftestpy_file_exists(attr_dict, path_selftest)

    assert len(result) == 2
    assert result[0]
    assert "selftest.py file found" in result[1].description

def test_invalid_selftest_validate_selftestpy_file_exists():

    attr_dict = sdk_validate_configs.selftest_attributes[2]

    path_selftest = "pacakge/with/no/util/selftest.py"

    result = sdk_validate_helpers.selftest_validate_selftestpy_file_exists(attr_dict, path_selftest)

    assert len(result) == 2
    assert result[0] is False
    assert "selftest.py is a required file" in result[1].description
    
def test_sefltest_run_selftestpy_valid():

    attr_dict = sdk_validate_configs.selftest_attributes[3]

    package_name = "fake_package_name"

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_subprocess:
        
        mock_subprocess.return_value = 0, "Success"

        result = sdk_validate_helpers.selftest_run_selftestpy(attr_dict, package_name)

        assert len(result) == 2
        assert result[0]
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_sefltest_run_selftestpy_invalid(fx_copy_fn_main_mock_integration):

    attr_dict = sdk_validate_configs.selftest_attributes[3]

    package_name = "fake_package_name"

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_subprocess:
        
        mock_subprocess.return_value = 1, "failure {'state': 'failure', 'reason': 'failed for test reasons'} and more text here..."

        result = sdk_validate_helpers.selftest_run_selftestpy(attr_dict, package_name)

        assert len(result) == 2
        assert result[0] is False
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert "failed for test reasons" in result[1].description and package_name in result[1].description

def test_sefltest_run_selftestpy_rest_error(fx_copy_fn_main_mock_integration):

    attr_dict = sdk_validate_configs.selftest_attributes[3]

    package_name = "fake_package_name"

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_subprocess:
        
        error_msg = u"ERROR: (fake) issue connecting to SOAR with some unicode: ล ฦ ว"
        mock_subprocess.return_value = 20, error_msg

        result = sdk_validate_helpers.selftest_run_selftestpy(attr_dict, package_name)

        assert len(result) == 2
        assert result[0] is False
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert error_msg in result[1].description

def test_pass_package_files_manifest(fx_copy_fn_main_mock_integration):

    filename = "MANIFEST.in"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    package_name = fx_copy_fn_main_mock_integration[0]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return a match, which will pass the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.get_close_matches") as mock_close_matches:
        mock_close_matches.return_value = ["match"]

        result = sdk_validate_helpers.package_files_manifest(package_name, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_package_files_manifest(fx_copy_fn_main_mock_integration):

    filename = "MANIFEST.in"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    package_name = fx_copy_fn_main_mock_integration[0]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return an empty list, which will fail the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.get_close_matches") as mock_close_matches:
        mock_close_matches.return_value = []

        result = sdk_validate_helpers.package_files_manifest(package_name, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN

def test_pass_package_files_apikey_pem(fx_copy_fn_main_mock_integration):

    filename = "apikey_permissions.txt"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    result = sdk_validate_helpers.package_files_apikey_pem(path_file, attr_dict)

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, SDKValidateIssue)
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_package_files_apikey_pem(fx_copy_fn_main_mock_integration):

    filename = "apikey_permissions.txt"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the file reading
    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.read_file") as mock_read_file:

        mock_read_file.return_value = ["#mock_commented_permissions\n", "mock_non_base_permission\n"]

        result = sdk_validate_helpers.package_files_apikey_pem(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_fail_package_files_template_match_dockerfile(fx_copy_fn_main_mock_integration):

    filename = "Dockerfile"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    package_name = fx_copy_fn_main_mock_integration[0]
    package_version = "fake.version"
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return an empty list, which will fail the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.SequenceMatcher.ratio") as mock_ratio:
        mock_ratio.return_value = 0.0

        result = sdk_validate_helpers.package_files_template_match(package_name, package_version, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN

def test_pass_package_files_template_match_dockerfile(fx_copy_fn_main_mock_integration):

    filename = "Dockerfile"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    package_name = fx_copy_fn_main_mock_integration[0]
    package_version = "fake.version"
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return an empty list, which will fail the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.SequenceMatcher.ratio") as mock_ratio:
        mock_ratio.return_value = 1.0

        result = sdk_validate_helpers.package_files_template_match(package_name, package_version, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_package_files_template_match_entrypoint(fx_copy_fn_main_mock_integration):

    filename = "entrypoint.sh"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    package_name = fx_copy_fn_main_mock_integration[0]
    package_version = "fake.version"
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return an empty list, which will fail the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.SequenceMatcher.ratio") as mock_ratio:
        mock_ratio.return_value = 0.0

        result = sdk_validate_helpers.package_files_template_match(package_name, package_version, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN

def test_pass_package_files_template_match_entrypoint(fx_copy_fn_main_mock_integration):

    filename = "entrypoint.sh"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    package_name = fx_copy_fn_main_mock_integration[0]
    package_version = "fake.version"
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return an empty list, which will fail the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.SequenceMatcher.ratio") as mock_ratio:
        mock_ratio.return_value = 1.0

        result = sdk_validate_helpers.package_files_template_match(package_name, package_version, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_difflib_unified_diff_used_in_template_match():
    """A quick test to check that difflib.unified_diff works the same as when we wrote
    code that uses it. If this test fails, make sure that all logic using this difflib output format
    is updated to reflect that change in difflib. Specifically, check that 
    package_file_helpers.color_diff_output is updated."""

    mock_fromfile_data = ["line 2"]
    mock_tofile_data = ["line 1"]
    
    diff = difflib.unified_diff(mock_fromfile_data, mock_tofile_data, n=0)

    # check that the lines are still the same that we'd expect when this was originally written
    for i, line in enumerate(diff):
        if i == 0:
            assert line.startswith("---")
        if i == 1:
            assert line.startswith("+++")
        if i == 2:
            assert line.startswith("@@ -1 +1 @@")

def test_pass_package_files_validate_config_py(fx_copy_fn_main_mock_integration):
    
    filename = "config.py"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock config parsing - return valid config
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_configs_from_config_py") as mock_config:

        mock_config.return_value = ("[fake_config]\nfake=fake", [{'name': 'fake', 'placeholder': 'fake'}])

        result = sdk_validate_helpers.package_files_validate_config_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG
        assert "fake=fake" in result.solution

def test_warn_package_files_validate_config_py(fx_copy_fn_main_mock_integration):
    
    filename = "config.py"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock config parsing - return no config
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_configs_from_config_py") as mock_config:

        mock_config.return_value = ("", [])

        result = sdk_validate_helpers.package_files_validate_config_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_INFO

def test_fail_package_files_validate_config_py(fx_copy_fn_main_mock_integration):
    
    filename = "config.py"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock config parsing - mock raising an exception
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_configs_from_config_py") as mock_config:

        mock_config.side_effect = SDKException("failed")

        result = sdk_validate_helpers.package_files_validate_config_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_pass_package_files_validate_customize_py(fx_copy_fn_main_mock_integration):
    
    filename = "customize.py"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock import def parsing - given a valid dict (actual validation of the import def happens)
    # in the get_import_definition_from_customize_py which is tested in 
    # test_package_file_helpers.test_load_customize_py_module
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_import_definition_from_customize_py") as mock_config:

        mock_config.return_value = {"action_order": [], "actions": [ {} ]}

        result = sdk_validate_helpers.package_files_validate_customize_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_package_files_validate_customize_py(fx_copy_fn_main_mock_integration):
    
    filename = "customize.py"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock import definition parsing - mock raising an exception
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_import_definition_from_customize_py") as mock_import_def:

        mock_import_def.side_effect = SDKException("failed")

        result = sdk_validate_helpers.package_files_validate_customize_py(path_file, attr_dict)
        
        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_package_files_validate_readme(fx_copy_fn_main_mock_integration):

    filename = "README.md"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    result = sdk_validate_helpers.package_files_validate_readme(fx_copy_fn_main_mock_integration[1], path_file, filename, attr_dict)

    assert len(result) == 1
    result = result[0]
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    assert "Cannot find the following screenshot(s) referenced in the README" in result.description
