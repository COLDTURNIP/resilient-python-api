#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import os
import re
import stat
import sys

import jinja2
import pkg_resources
import pytest
from mock import patch
from resilient import SimpleClient
from resilient_sdk.cmds import CmdCodegen, CmdValidate
from resilient_sdk.util import constants, sdk_helpers
from resilient_sdk.util.resilient_objects import ResilientObjMap
from resilient_sdk.util.sdk_exception import SDKException
from tests.shared_mock_data import mock_data, mock_paths


def test_get_resilient_client(fx_mk_temp_dir, fx_mk_app_config, caplog):
    res_client = sdk_helpers.get_resilient_client(path_config_file=fx_mk_app_config)
    assert isinstance(res_client, SimpleClient)
    assert "Connecting to IBM Security SOAR at: " in caplog.text


def test_setup_jinja_env(fx_mk_temp_dir):
    jinja_env = sdk_helpers.setup_jinja_env(mock_paths.TEST_TEMP_DIR)
    assert isinstance(jinja_env, jinja2.Environment)
    assert jinja_env.loader.package_path == mock_paths.TEST_TEMP_DIR


def test_read_write_file(fx_mk_temp_dir):
    temp_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_file.txt")
    sdk_helpers.write_file(temp_file, mock_data.mock_file_contents)
    assert os.path.isfile(temp_file)

    file_lines = sdk_helpers.read_file(temp_file)
    assert mock_data.mock_file_contents in file_lines


def test_read_json_file_success():
    export_data = sdk_helpers.read_json_file(mock_paths.MOCK_EXPORT_RES)
    assert isinstance(export_data, dict)
    assert "functions" in export_data


def test_read_json_file_fail(fx_mk_temp_dir):
    temp_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_file.txt")
    sdk_helpers.write_file(temp_file, mock_data.mock_file_contents)
    match_text = "Could not read corrupt JSON file at {0}".format(temp_file)

    with pytest.raises(SDKException, match=match_text):
        sdk_helpers.read_json_file(temp_file)


def test_rename_file(fx_mk_temp_dir):
    temp_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_file.txt")
    sdk_helpers.write_file(temp_file, mock_data.mock_file_contents)

    sdk_helpers.rename_file(temp_file, "new_file_name.txt")
    path_renamed_file = os.path.join(mock_paths.TEST_TEMP_DIR, "new_file_name.txt")

    assert os.path.isfile(path_renamed_file) is True

def test_read_zip_file():
    file_lines = sdk_helpers.read_zip_file(mock_paths.MOCK_ZIP, "mock_file.txt")
    assert mock_data.mock_file_contents in file_lines

def test_is_valid_package_name():
    assert sdk_helpers.is_valid_package_name("fn_mock_integration") is True
    assert sdk_helpers.is_valid_package_name("fnmockintegration") is True
    assert sdk_helpers.is_valid_package_name("fn-mock-integration") is True
    assert sdk_helpers.is_valid_package_name("get") is False
    assert sdk_helpers.is_valid_package_name("$%&(#)@*$") is False
    assert sdk_helpers.is_valid_package_name("fn-ځ ڂ ڃ ڄ څ-integration") is False
    assert sdk_helpers.is_valid_package_name("fn-MockIntegration") is False
    assert sdk_helpers.is_valid_package_name(None) is False

def test_is_valid_version_syntax():
    assert sdk_helpers.is_valid_version_syntax("1.0") is False
    assert sdk_helpers.is_valid_version_syntax("0") is False
    assert sdk_helpers.is_valid_version_syntax("1.0.0") is True
    assert sdk_helpers.is_valid_version_syntax("abc") is False


def test_is_valid_url():
    assert sdk_helpers.is_valid_url("www.example.com") is True
    assert sdk_helpers.is_valid_url("example.com") is True
    assert sdk_helpers.is_valid_url("http://www.example.com") is True
    assert sdk_helpers.is_valid_url("https://example.com") is True
    assert sdk_helpers.is_valid_url("https://www.example.com:8080") is True

    assert sdk_helpers.is_valid_url(None) is False
    assert sdk_helpers.is_valid_url("not a url") is False
    assert sdk_helpers.is_valid_url("https://www. example.com") is False


def test_is_valid_hash():
    assert sdk_helpers.is_valid_hash("dd2a1678b6e0fd1d1a1313f78785fd0c4fad0565ac9008778bdb3b00bdff4420") is True
    assert sdk_helpers.is_valid_hash("dd2a1678b6e0fd1d1a1313f78785fd0c4fad0565ac9008778bdb3b00bdff4420d") is False
    assert sdk_helpers.is_valid_hash("Xdd2a1678b6e0fd1d1a1313f78785fd0c4fad0565ac9008778bdb3b00bdff4420") is False
    assert sdk_helpers.is_valid_hash("") is False
    assert sdk_helpers.is_valid_hash(None) is False
    assert sdk_helpers.is_valid_hash("xxx") is False


def test_does_url_contain():
    assert sdk_helpers.does_url_contain("http://www.example.com", "example") is True
    assert sdk_helpers.does_url_contain("not a url", "example") is False
    assert sdk_helpers.does_url_contain("http://www.example.com", "abc") is False


def test_generate_uuid_from_string():
    the_string, the_uuid = "fn_test_package", "7627eab9-8500-cf1d-380d-14a2c4364acf"
    the_generated_uuid = sdk_helpers.generate_uuid_from_string(the_string)
    assert the_generated_uuid == the_uuid


def test_has_permissions(fx_mk_temp_dir):
    temp_permissions_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_permissions.txt")
    sdk_helpers.write_file(temp_permissions_file, mock_data.mock_file_contents)

    # Set permissions to Read only
    os.chmod(temp_permissions_file, stat.S_IRUSR)

    with pytest.raises(SDKException, match=r"User does not have WRITE permissions"):
        sdk_helpers.has_permissions(os.W_OK, temp_permissions_file)

    # Set permissions to Write only
    os.chmod(temp_permissions_file, stat.S_IWUSR)

    with pytest.raises(SDKException, match=r"User does not have READ permissions"):
        sdk_helpers.has_permissions(os.R_OK, temp_permissions_file)


def test_validate_file_paths(fx_mk_temp_dir):
    non_exist_file = "/non_exits/path/non_exist_file.txt"
    with pytest.raises(SDKException, match=r"Could not find file: " + non_exist_file):
        sdk_helpers.validate_file_paths(None, non_exist_file)

    exists_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_existing_file.txt")
    sdk_helpers.write_file(exists_file, mock_data.mock_file_contents)

    sdk_helpers.validate_file_paths(None, exists_file)


def test_validate_dir_paths(fx_mk_temp_dir):
    non_exist_dir = "/non_exits/path/"
    with pytest.raises(SDKException, match=r"Could not find directory: " + non_exist_dir):
        sdk_helpers.validate_dir_paths(None, non_exist_dir)

    exists_dir = mock_paths.TEST_TEMP_DIR

    sdk_helpers.validate_dir_paths(None, exists_dir)


def test_get_resilient_server_info(fx_mock_res_client):
    server_info = sdk_helpers.get_resilient_server_info(fx_mock_res_client, ["export_format_version", "locale", "non_exist"])
    assert len(server_info) == 3
    assert server_info.get("export_format_version") == 2
    assert server_info.get("locale") == "en"
    assert server_info.get("non_exist") == {}


def test_get_resilient_server_version(fx_mock_res_client):
    mock_version = 39.0
    assert sdk_helpers.get_resilient_server_version(fx_mock_res_client) == mock_version
    assert constants.CURRENT_SOAR_SERVER_VERSION == mock_version


def test_read_local_exportfile():
    export_data = sdk_helpers.read_local_exportfile(mock_paths.MOCK_EXPORT_RES)
    assert isinstance(export_data, dict)
    assert "functions" in export_data

def test_read_local_exportfile_resz():
    export_data = sdk_helpers.read_local_exportfile(mock_paths.MOCK_EXPORT_RESZ)
    assert isinstance(export_data, dict)
    assert "functions" in export_data

def test_get_obj_from_list():
    org_export = sdk_helpers.read_json_file(mock_paths.MOCK_EXPORT_RES)
    export_data = sdk_helpers.get_from_export(org_export, functions=["mock_function_one", "mock_function_two"])

    all_functions = export_data.get("functions")
    got_functions = sdk_helpers.get_obj_from_list("export_key", all_functions)

    assert isinstance(got_functions, dict)
    assert "mock_function_one" in got_functions
    assert "mock_function_two" in got_functions

    # Test lambda condition
    got_functions = sdk_helpers.get_obj_from_list("export_key", all_functions, lambda o: True if o.get("export_key") == "mock_function_one" else False)
    assert "mock_function_one" in got_functions
    assert "mock_function_two" not in got_functions


def test_get_object_api_names(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)
    export_data = sdk_helpers.get_from_export(org_export,
                                              functions=["mock_function_one", "mock_function_two"])

    func_api_names = sdk_helpers.get_object_api_names("x_api_name", export_data.get("functions"))

    assert all(elem in ["mock_function_one", "mock_function_two"] for elem in func_api_names) is True


def test_get_res_obj():
    org_export = sdk_helpers.read_json_file(mock_paths.MOCK_EXPORT_RES)

    artifacts_wanted = ["mock_artifact_2", "mock_artifact_type_one"]
    artifacts = sdk_helpers.get_res_obj("incident_artifact_types", "programmatic_name", "Custom Artifact", artifacts_wanted, org_export)

    assert all(elem.get("x_api_name") in artifacts_wanted for elem in artifacts) is True

def test_get_incident_types():
    org_export = sdk_helpers.read_json_file(mock_paths.MOCK_EXPORT_RES)

    incident_types_wanted = [u"mock_incidenttype_Āā", u"mock incident type one"]
    incident_types = sdk_helpers.get_res_obj("incident_types", "name", "Custom Incident Types", incident_types_wanted, org_export)

    assert all(elem.get("name") in incident_types_wanted for elem in incident_types) is True

def test_get_res_obj_corrupt_export():
    org_export = sdk_helpers.read_json_file(mock_paths.MOCK_EXPORT_RES_CORRUPT)

    artifacts_wanted = ["mock_artifact_2", "mock_artifact_type_one"]

    with pytest.raises(SDKException, match=r"'mock_artifact_2' not found in this export"):
        sdk_helpers.get_res_obj("incident_artifact_types", "programmatic_name", "Custom Artifact", artifacts_wanted, org_export)


def test_get_res_obj_dict_in_wanted_list(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    wfs_wanted = [{"identifier": "name", "value": u"mock workflow  ล ฦ ว ศ ษ ส ห ฬ อ two"}]
    wfs = sdk_helpers.get_res_obj("workflows", "programmatic_name", "Workflow", wfs_wanted, org_export)

    assert len(wfs) == 1
    assert wfs[0].get("programmatic_name") == "mock_workflow_two"


def test_get_res_obj_exception(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    functions_wanted = ["mock_function_one", "fn_does_not_exist"]

    with pytest.raises(SDKException, match=r"Mock Display Name: 'fn_does_not_exist' not found in this export"):
        sdk_helpers.get_res_obj("functions", "export_key", "Mock Display Name", functions_wanted, org_export)


def test_get_message_destination_from_export(fx_mock_res_client):
    # TODO: Add test for all resilient objects...
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    export_data = sdk_helpers.get_from_export(org_export,
                                              message_destinations=["fn_main_mock_integration"])

    assert export_data.get("message_destinations")[0].get("name") == "fn_main_mock_integration"


def test_get_playbooks_from_export(fx_mock_res_client):
    with patch("resilient_sdk.util.sdk_helpers.get_resilient_server_version") as mock_server_version:

        mock_server_version.return_value = 44.0
        constants.CURRENT_SOAR_SERVER_VERSION = 44.0
        org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)
        export_data = sdk_helpers.get_from_export(org_export, playbooks=["main_mock_playbook"])

        assert export_data.get("playbooks")[0].get(ResilientObjMap.PLAYBOOKS) == "main_mock_playbook"
        constants.CURRENT_SOAR_SERVER_VERSION = None # reset for other tests


def test_get_playbooks_from_export_incompatible_version(fx_mock_res_client):

    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    with pytest.raises(SDKException, match=r"Playbooks are only supported in resilient_sdk for SOAR >= 44"):
        sdk_helpers.get_from_export(org_export, playbooks=["main_mock_playbook"])


@pytest.mark.parametrize("get_related_param",
                         [(True), (False)])
def test_get_related_objects_when_getting_from_export(fx_mock_res_client, get_related_param):

    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    export_data = sdk_helpers.get_from_export(org_export,
                                              message_destinations=["fn_main_mock_integration"],
                                              functions=["mock_function__three"],
                                              get_related_objects=get_related_param)

    assert export_data.get("message_destinations")[0].get("name") == "fn_main_mock_integration"

    if get_related_param:
        assert len(export_data.get("functions", [])) > 0
        assert any(elem.get("name") in ("mock_function_one", "mock_function_two") for elem in export_data.get("functions")) is True

    else:
        assert all(elem.get("name") in ("mock_function_one", "mock_function_two") for elem in export_data.get("functions")) is False


def test_minify_export(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    minifed_export = sdk_helpers.minify_export(org_export, functions=["mock_function_one"], phases=["Mock Custom Phase One"], scripts=["Mock Incident Script"])
    minified_functions = minifed_export.get("functions")
    minified_fields = minifed_export.get("fields")
    minified_incident_types = minifed_export.get("incident_types")
    minified_phases = minifed_export.get("phases")
    minified_scripts = minifed_export.get("scripts")

    # Test it minified given function
    assert len(minified_functions) == 1
    assert minified_functions[0].get("export_key") == "mock_function_one"

    # Test it set a non-mentioned object to 'empty'
    assert minifed_export.get("roles") == []

    # Test phases + scripts
    assert minified_phases[0].get(ResilientObjMap.PHASES) == "Mock Custom Phase One"
    assert minified_scripts[0].get(ResilientObjMap.SCRIPTS) == "Mock Incident Script"

    # Test it added the internal field
    assert len(minified_fields) == 1
    assert minified_fields[0].get("export_key") == "incident/internal_customizations_field"
    assert minified_fields[0].get("uuid") == "bfeec2d4-3770-11e8-ad39-4a0004044aa1"

    # Test it added the default incident type
    assert len(minified_incident_types) >= 1
    assert minified_incident_types[0].get("export_key") == "Customization Packages (internal)"
    assert minified_incident_types[0].get("uuid") == "bfeec2d4-3770-11e8-ad39-4a0004044aa0"


def test_minify_export_default_keys_to_keep(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)

    minifed_export = sdk_helpers.minify_export(org_export)

    assert "export_date" in minifed_export
    assert "export_format_version" in minifed_export
    assert "id" in minifed_export
    assert "server_version" in minifed_export


def test_minify_export_with_playbooks(fx_mock_res_client):
    org_export = sdk_helpers.get_latest_org_export(fx_mock_res_client)
    minifed_export = sdk_helpers.minify_export(org_export)

    assert "export_date" in minifed_export
    assert "export_format_version" in minifed_export
    assert "id" in minifed_export
    assert "server_version" in minifed_export


def test_load_by_module():
    path_python_file = os.path.join(mock_paths.SHARED_MOCK_DATA_DIR, "mock_data.py")
    module_name = "mock_data"
    mock_data_module = sdk_helpers.load_py_module(path_python_file, module_name)

    assert mock_data_module.mock_loading_this_module == "yes you did!"


def test_rename_to_bak_file(fx_mk_temp_dir):
    temp_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_file.txt")
    sdk_helpers.write_file(temp_file, mock_data.mock_file_contents)

    sdk_helpers.rename_to_bak_file(temp_file)

    files_in_dir = os.listdir(mock_paths.TEST_TEMP_DIR)
    regex = re.compile(r'^mock_file\.txt-\d+\d+\d+\d+\d+\d+\d+\.bak$')
    matched_file_name = list(filter(regex.match, files_in_dir))[0]

    assert regex.match(matched_file_name)


def test_rename_to_bak_file_if_file_not_exist(fx_mk_temp_dir):
    temp_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_file.txt")
    path_to_backup = sdk_helpers.rename_to_bak_file(temp_file)
    assert temp_file == path_to_backup


def test_generate_anchor():
    anchor = sdk_helpers.generate_anchor(u"D מ ן נ ס עata Ta!@#$%^&*()__ble Utせ ぜ そ ぞ た だils: ✔✕✖✗✘✙✚✛ òDelete_Rowﻀ ﻁ ﻂ ﻃ ﻄ ﻅ ﻆ ﻇ ﻈ and 㐖 㐗 㐘 㐙 㐚 㐛 㐜 㐝")
    assert anchor == u"d-מ-ן-נ-ס-עata-ta__ble-utせ-ぜ-そ-ぞ-た-だils--òdelete_rowﻀ-ﻁ-ﻂ-ﻃ-ﻄ-ﻅ-ﻆ-ﻇ-ﻈ-and-㐖-㐗-㐘-㐙-㐚-㐛-㐜-㐝"


def test_simplify_string():
    assert "d-----ata-ta--ble-ut-----ils--delete-row---------and--------" == sdk_helpers.simplify_string("D מ ן נ ס עata Ta!@#$%^&*()__ble Utせ ぜ そ ぞ た だils: ✔✕✖✗✘✙✚✛ òDelete_Rowﻀ ﻁ ﻂ ﻃ ﻄ ﻅ ﻆ ﻇ ﻈ and 㐖 㐗 㐘 㐙 㐚 㐛 㐜 㐝")


def test_get_workflow_functions():
    # TODO: taken from docgen
    pass


def test_get_main_cmd(monkeypatch):
    mock_args = ["resilient-sdk", "codegen", "-p", "fn_mock_package"]
    monkeypatch.setattr(sys, "argv", mock_args)
    main_cmd = sdk_helpers.get_main_cmd()
    assert main_cmd == "codegen"


def test_get_timestamp():
    now = sdk_helpers.get_timestamp()
    assert re.match(r"\d\d\d\d\d\d\d\d\d\d\d\d\d\d", now)


def test_get_timestamp_from_timestamp():
    ts = sdk_helpers.get_timestamp(1579258053.728)
    assert ts == "20200117104733"


def test_str_to_bool():
    assert sdk_helpers.str_to_bool('True') is True
    assert sdk_helpers.str_to_bool('true') is True
    assert sdk_helpers.str_to_bool('YES') is True
    assert sdk_helpers.str_to_bool('truex') is False
    assert sdk_helpers.str_to_bool(1) is True
    assert sdk_helpers.str_to_bool(0) is False
    assert sdk_helpers.str_to_bool('0') is False


def test_is_env_var_set(fx_add_dev_env_var):
    assert sdk_helpers.is_env_var_set(constants.ENV_VAR_DEV) is True


def test_is_env_var_not_set():
    assert sdk_helpers.is_env_var_set(constants.ENV_VAR_DEV) is False


def test_get_resilient_libraries_version_to_use():
    assert sdk_helpers.get_resilient_libraries_version_to_use() == constants.RESILIENT_LIBRARIES_VERSION


def test_get_resilient_libraries_version_to_use_dev(fx_add_dev_env_var):
    assert sdk_helpers.get_resilient_libraries_version_to_use() == constants.RESILIENT_LIBRARIES_VERSION_DEV

def test_get_resilient_sdk_version():
    parsed_version = sdk_helpers.get_resilient_sdk_version()
    assert parsed_version is not None
    assert parsed_version >= pkg_resources.parse_version(constants.RESILIENT_LIBRARIES_VERSION)

def test_get_package_version_found_in_env():
    parsed_version = sdk_helpers.get_package_version("resilient-sdk")
    assert parsed_version is not None
    assert parsed_version >= pkg_resources.parse_version(constants.RESILIENT_LIBRARIES_VERSION)

def test_get_package_version_not_found():
    not_found = sdk_helpers.get_package_version("this-package-doesnt-exist")
    assert not_found is None

def test_is_python_min_supported_version(caplog):
    mock_log = "WARNING: this package should only be installed on a Python Environment >="

    is_supported = sdk_helpers.is_python_min_supported_version()

    if sys.version_info < constants.MIN_SUPPORTED_PY_VERSION:
        assert mock_log in caplog.text
        assert is_supported is False

    else:
        assert mock_log not in caplog.text
        assert is_supported is True


def test_parse_optionals_codegen(fx_get_sub_parser):
    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    optionals = cmd_codegen.parser._get_optional_actions()
    parsed_optionals = sdk_helpers.parse_optionals(optionals)

    assert """\n -re, --reload\t\t\tReload customizations and create new customize.py \n""" in parsed_optionals


def test_parse_optionals_validate(fx_get_sub_parser):
    cmd_validate = CmdValidate(fx_get_sub_parser)
    optionals = cmd_validate.parser._get_optional_actions()
    parsed_optionals = sdk_helpers.parse_optionals(optionals)

    assert """\n --pylint\t\t\tRun a pylint scan of all .py files under package directory. \'pylint\' must be installed) \n""" in parsed_optionals


def test_run_subprocess():

    args = ["echo", "testing sdk_helper.subprocess"]
    exitcode, details = sdk_helpers.run_subprocess(args)

    assert exitcode == 0
    assert args[1] in details


def test_run_subprocess_with_cwd():

    args = ["pwd"]
    path = os.path.expanduser("~")

    dir_before_cwd = os.getcwd()

    exitcode, details = sdk_helpers.run_subprocess(args, change_dir=path)

    assert exitcode == 0
    assert path in details
    assert dir_before_cwd == os.getcwd()


def test_scrape_results_from_log_file():

    results_scraped = sdk_helpers.scrape_results_from_log_file(mock_paths.MOCK_APP_LOG_PATH)
    mock_function_one_results = results_scraped.get("mock_function_one")

    assert isinstance(mock_function_one_results, dict)

    # There are two Results for mock_function_one
    # in the mock_app.log file, so this ensures we get the latest
    assert mock_function_one_results.get("version") == 2.1
    assert mock_function_one_results.get("reason") == None


def test_scrape_results_from_log_file_not_found():
    with pytest.raises(SDKException, match=constants.ERROR_NOT_FIND_FILE):
        sdk_helpers.scrape_results_from_log_file("mock_path_non_existent")


def test_handle_file_not_found_error(caplog):
    error_msg = u"mock error  ล ฦ ว message"

    try:
        sdk_helpers.validate_dir_paths(os.R_OK, "mock_path_no_existing")
    except SDKException as e:
        sdk_helpers.handle_file_not_found_error(e, error_msg)

    assert u"WARNING: {0}".format(error_msg) in caplog.text

    try:
        sdk_helpers.validate_file_paths(os.R_OK, "mock_path_no_existing")
    except SDKException as e:
        sdk_helpers.handle_file_not_found_error(e, error_msg)

    assert u"WARNING: {0}".format(error_msg) in caplog.text
