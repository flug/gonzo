from fabric.api import run, settings

from gonzo.tasks.release import (
    activate, list_releases, project_path, prune, push, usudo,
    virtualenv)


def test_separate_venv(container, test_repo):
    # small package with no requirements
    test_repo.files['requirements.txt'] = 'initools==0.2'
    pip_output = push()
    setup_output = 'Running setup.py install for initools'
    assert setup_output in pip_output
    activate()
    # trigger commit
    test_repo.files['dummy'] = 'a'
    pip_output = push()
    assert setup_output in pip_output


def test_push_same_commit(container, test_repo):
    push()
    push()


def test_pruning(container, test_repo):
    project_dir = project_path('releases')
    venv_dir = project_path('virtualenvs')

    test_repo.files['requirements.txt'] = 'initools==0.2'
    push()
    activate()
    # trigger commit
    test_repo.files['dummy'] = 'a'
    push()
    activate()

    history = list_releases()
    assert len(history) == 2

    def ls(path):
        return run('ls {}'.format(path)).split()

    releases = ls(project_dir)
    virtualenvs = ls(venv_dir)

    assert len(releases) == 3  # includes current
    assert len(virtualenvs) == 3  # includes current

    prune(keep=1)

    history = list_releases()
    assert len(history) == 1

    releases = ls(project_dir)
    virtualenvs = ls(venv_dir)

    assert len(releases) == 2  # includes current
    assert len(virtualenvs) == 2  # includes current

    # check that virtualenv still works
    with virtualenv():
        with settings(warn_only=True):
            res = usudo('pip freeze|grep -i initools')
        assert res.succeeded
