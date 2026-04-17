"""Planted fixture for test_yaml_safe_load_discipline.

This file deliberately contains an unsafe yaml.load call; the discipline test's
walker must NOT scan tests/fixtures/, so the presence of this call must not
trip the ban. A separate tmp_path-based assertion in the discipline test proves
the widened walk catches such calls when they appear outside fixtures.
"""
# NOTE: This call is a bait-and-switch control. Do not import or execute.
# import yaml
# _ = yaml.load("foo: bar")
