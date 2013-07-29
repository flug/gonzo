from fabric.contrib.console import confirm
from fabric.utils import abort, warn

from gonzo.helpers.git import get_current_branch, diff_branch

ASSERT_RELEASE_BRANCH_WARNING = """
Trying to release a branch that is not {0}: "{1}"

Checkout {0} and merge in topic branch before releasing:

    $ git co {0}
    $ git merge {1}

"""

ASSERT_AHEAD_OF_CURRENT_RELEASE_WARNING = """
Trying to release a branch that is behind {0}.

"""


def continue_check():
    confirmation_message = (
        'Checks failed with the above warnings. Do you wish to continue '
        'anyway?')
    if not confirm(confirmation_message, default=False):
        abort('Aborted with the above warnings')


def assert_release_branch(release_branch='master'):
    """ Checks the currently checked out branch is `release_branch`
    """
    branch = get_current_branch()
    if branch != release_branch:
        warn(ASSERT_RELEASE_BRANCH_WARNING.format(release_branch, branch))
        continue_check()


def assert_ahead_of_current_release(current_release='origin/master'):
    """ Checks the local branch is ahead of `current_release`
    """
    upstream_ahead, local_ahead = diff_branch(current_release)
    if upstream_ahead > 0:
        warn(ASSERT_AHEAD_OF_CURRENT_RELEASE_WARNING.format(current_release))
        continue_check()
