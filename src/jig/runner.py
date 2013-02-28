import json
import sys

from git import Repo

from jig.exc import GitRepoNotInitialized
from jig.gitutils import repo_jiginitialized
from jig.diffconvert import GitDiffIndex
from jig.plugins import get_jigconfig, PluginManager
from jig.commands import get_command, list_commands
from jig.output import ConsoleView

try:
    from collections import OrderedDict
except ImportError:   # pragma: no cover
    from ordereddict import OrderedDict


class Runner(object):

    """
    Runs jig in a Git repo.

    """
    def __init__(self, view=None):
        self.view = view or ConsoleView()

    def fromhook(self, gitrepo, interactive=True):
        """
        Main entry point for running, typically called from pre-commit hook.

        Where ``gitrepo`` is the file path to the Git repository.

        If ``interactive`` is True then the user will be prompted to commit or
        cancel when any messages are generated by the plugins.
        """
        results = self.results(gitrepo)

        report_counts = self.view.print_results(results)

        if interactive and report_counts and sum(report_counts):
            # Git will run a pre-commit hook with stdin pointed at /dev/null.
            # We will reconnect to the tty so that raw_input works.
            sys.stdin = open('/dev/tty')
            while True:
                try:
                    answer = raw_input(
                        '\nCommit anyway (hit "c"), or stop (hit "s"): ')
                except KeyboardInterrupt:
                    sys.exit(1)
                if answer and answer[0].lower() == 's':
                    sys.exit(1)
                elif answer and answer[0].lower() == 'c':
                    break

        sys.exit(0)

    def fromconsole(self, argv):
        """
        Console entry point for the jig script.

        Where ``argv`` is ``sys.argv``.
        """
        # Quick copy
        argv = argv[:]
        # Our script is the first element
        argv.pop(0)

        try:
            # Next argument is the command
            command = get_command(argv.pop(0))
            command(argv)   # pragma: no cover
        except (ImportError, IndexError):
            # If it's empty
            self.view.print_help(list_commands())

    def results(self, gitrepo):
        """
        Run jig in the repository and return results.

        Results will be a dictionary where the keys will be individual plugins
        and the value the result of calling their ``pre_commit()`` methods.
        """
        self.gitrepo = gitrepo

        # Is this repository initialized to use jig on?
        with self.view.out() as out:
            if not repo_jiginitialized(self.gitrepo):
                raise GitRepoNotInitialized('This repository has not been '
                    'initialized.')

        pm = PluginManager(get_jigconfig(self.gitrepo))

        # Check to make sure we have some plugins to run
        with self.view.out() as out:
            if len(pm.plugins) == 0:
                out.append('There are no plugins installed, '
                    'use jig install to add some.')
                return

            self.repo = Repo(gitrepo)

            try:
                diff = self.repo.head.commit.diff()
            except ValueError:
                # No diff on head, no commits have been written yet
                out.append('This repository is empty, jig needs at '
                    'least 1 commit to continue.')
                # Let execution continue so they *can* commit that first
                # changeset.
                return

            if len(diff) == 0:
                # There is nothing changed in this repository, no need for
                # jig to run
                out.append('No staged changes in the repository, skipping '
                    'jig.')
                return

        # Our git diff index is an object that makes working with the diff much
        # easier in the context of our plugins.
        gdi = GitDiffIndex(self.gitrepo, diff)

        # Go through the plugins and gather up the results
        results = OrderedDict()
        for plugin in pm.plugins:
            retcode, stdout, stderr = plugin.pre_commit(gdi)

            try:
                # Is it JSON data?
                data = json.loads(stdout)
            except ValueError:
                # Not JSON
                data = stdout

            results[plugin] = (retcode, data, stderr)

        return results
