"""
Basic parser tests for pcdswidgets-show to guard against obvious issues.

Check for stable keywords and check that these basic invocations don't immediatelly error out.
"""

import pytest

from pcdswidgets.show_screen import main


def test_help(capsys: pytest.CaptureFixture):
    capsys.readouterr()
    with pytest.raises(SystemExit):
        main(["--help"])
    output = capsys.readouterr()
    assert "usage" in output.out
    assert not output.err


def test_options(capsys: pytest.CaptureFixture):
    capsys.readouterr()
    rval = main(["--options"])
    assert rval == 0
    output = capsys.readouterr()
    assert "FeatureFinder" in output.out
    assert not output.err


def test_no_args_help(capsys: pytest.CaptureFixture):
    capsys.readouterr()
    rval = main([])
    assert rval == 1
    output = capsys.readouterr()
    assert "usage" in output.out
    assert output.err


def test_standard_help(capsys: pytest.CaptureFixture):
    capsys.readouterr()
    with pytest.raises(SystemExit):
        main(["FeatureFinder", "--help"])
    output = capsys.readouterr()
    assert "usage" in output.out
    assert "--detector" in output.out
    assert not output.err


def test_generated_widget_help(capsys: pytest.CaptureFixture):
    capsys.readouterr()
    with pytest.raises(SystemExit):
        main(["ApertureValve", "--help"])
    output = capsys.readouterr()
    assert "usage" in output.out
    assert "--channelsPrefix" in output.out
    assert not output.err


def test_generated_screen_help(capsys: pytest.CaptureFixture):
    capsys.readouterr()
    with pytest.raises(SystemExit):
        main(["GCCPLC_detailed", "--help"])
    output = capsys.readouterr()
    assert "usage" in output.out
    assert "--prefix" in output.out
    assert not output.err
