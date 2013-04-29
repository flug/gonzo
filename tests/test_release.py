from contextlib import contextmanager, nested
import copy

from mock import patch
import pytest

from gonzo.test_utils import assert_called_once_with, assert_has_calls
from gonzo.tasks.release import (
    append_to_history, get_previous_release, rollback, activate,
    purge_release)


@contextmanager
def disable_external_commands():
    with nested(
        patch('gonzo.tasks.release.local'),
        patch('gonzo.tasks.release.run'),
        patch('gonzo.tasks.release.sudo'),
    ) as (local, run, sudo):
        local.side_effect = RuntimeError("'local' called during testing")
        run.side_effect = RuntimeError("'run' called during testing")
        sudo.side_effect = RuntimeError("'sudo' called during testing")

        yield


@contextmanager
def mock_history(initial):
    """ intercept ``sudo`` and ``run`` commands, and match against
        a list of regexes, to fake history management
    """

    releases = copy.copy(initial)
    project = 'project'

    def list_releases():
        return releases

    def _append_to_history(release):
        releases.append(release)

    def rollback_history():
        if releases is None:
            raise RuntimeError("Trying to rollback with missing history file")
        if releases:  # sed is ok as long as the file exists
            releases.pop()

    def _replace_history(release_list):
        releases[:] = release_list

    with nested(
        patch('gonzo.tasks.release.list_releases', list_releases),
        patch('gonzo.tasks.release._append_to_history', _append_to_history),
        patch('gonzo.tasks.release.rollback_history', rollback_history),
        patch('gonzo.tasks.release._replace_history', _replace_history),
        patch('gonzo.tasks.release.get_project'),
    ) as (_, _, _, _, get_project):

        get_project.return_value = project

        with disable_external_commands():
            yield releases


@patch('gonzo.tasks.release.list_releases')
def test_get_previous_release(list_releases):
    releases = [
        'aaa',
        'bbb',
        'ccc',
        'ddd',
    ]

    list_releases.return_value = releases

    assert get_previous_release('ccc') == 'bbb'
    assert get_previous_release(None) is None
    assert get_previous_release('aaa') is None
    assert get_previous_release('xxx') is None


@patch('gonzo.tasks.release.list_releases')
def test_get_previous_release_ho_history(list_releases):
    releases = []

    list_releases.return_value = releases

    assert get_previous_release(None) is None
    assert get_previous_release('xxx') is None


def test_append_to_history():
    with mock_history(initial=['aaa']) as releases:
        append_to_history('bbb')
        assert releases == ['aaa', 'bbb']


def test_append_to_history_empty():
    with mock_history(initial=[]) as releases:
        append_to_history('aaa')
        assert releases == ['aaa']


def test_append_to_history_noop():
    with mock_history(initial=['aaa']) as releases:
        append_to_history('aaa')
        assert releases == ['aaa']


def test_append_to_history_repeat():
    with mock_history(initial=['aaa', 'bbb']) as releases:
        append_to_history('aaa')
        assert releases == ['aaa', 'bbb', 'aaa']


@patch('gonzo.tasks.release.set_current')
@patch('gonzo.tasks.release.get_current')
def test_rollback(get_current, set_current):
    get_current.return_value = 'bbb'
    with mock_history(initial=['aaa', 'bbb']) as releases:
        rollback()
        assert releases == ['aaa']
    assert_called_once_with(set_current, 'aaa')


@patch('gonzo.tasks.release.set_current')
@patch('gonzo.tasks.release.get_current')
def test_rollback_nowhere_to_go(get_current, set_current):
    get_current.return_value = 'aaa'
    with mock_history(initial=['aaa']) as releases:
        with pytest.raises(RuntimeError):
            rollback()
        assert releases == ['aaa']
    assert_has_calls(set_current, [])


@patch('gonzo.tasks.release.get_commit')
@patch('gonzo.tasks.release.set_current')
@patch('gonzo.tasks.release.get_current')
def test_activate(get_current, set_current, get_commit):
    get_current.return_value = 'bbb'
    get_commit.return_value = 'ccc'
    with mock_history(initial=['aaa', 'bbb']) as releases:
        activate()
        assert releases == ['aaa', 'bbb', 'ccc']
    assert_called_once_with(set_current, 'ccc')


@patch('gonzo.tasks.release.exists')
@patch('gonzo.tasks.release.get_current')
def test_purge_release(get_current, exists):
    get_current.return_value = 'ccc'
    exists.return_value = True
    with mock_history(initial=['aaa', 'bbb', 'ccc']) as releases:
        with patch('gonzo.tasks.release.sudo'):
            purge_release('aaa')
    assert releases == ['bbb', 'ccc']


@patch('gonzo.tasks.release.exists')
@patch('gonzo.tasks.release.get_current')
def test_purge_release_current(get_current, exists):
    get_current.return_value = 'bbb'
    exists.return_value = True
    with mock_history(initial=['aaa', 'bbb']) as releases:
        with pytest.raises(RuntimeError):
            purge_release('ccc')
    assert releases == ['aaa', 'bbb']
