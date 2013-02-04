# coding=utf-8
from tempfile import mkdtemp
from contextlib import nested

from mock import patch

from jig.tests.testcase import CommandTestCase, PluginTestCase
from jig.plugins import set_jigconfig
from jig.exc import ForcedExit
from jig.commands import runnow


class TestRunNowCommand(CommandTestCase, PluginTestCase):

    """
    Test the runnow command.

    """
    command = runnow.Command

    def test_no_changes(self):
        """
        No changes have been made to the Git repository.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create the first commit
        self.commit(self.gitrepodir, 'a.txt', 'a')

        with self.assertRaises(SystemExit) as ec:
            self.run_command(self.gitrepodir)

        self.assertSystemExitCode(ec.exception, 0)

        self.assertEqual(u'No staged changes in the repository, '
            'skipping jig.\n', self.output)

    def test_changes(self):
        """
        Changes are made and the plugin runs and gives us output.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create staged changes
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        with nested(
            patch('jig.runner.sys'),
            self.assertRaises(SystemExit)
        ) as (r_sys, ec):
            # Raise the error to halt execution like the real sys.exit would
            r_sys.exit.side_effect = SystemExit

            self.run_command(self.gitrepodir)

        r_sys.exit.assert_called_once_with(0)

        self.assertResults(u"""
            ▾  plugin01

            ⚠  line 1: b.txt
                b is +

            Ran 1 plugin
                Info 0 Warn 1 Stop 0
            """, self.output)

    def test_handles_error(self):
        """
        An un-initialized jig Git repository provides an error message.
        """
        with self.assertRaises(ForcedExit):
            self.run_command(mkdtemp())

        self.assertIn(u'This repository has not been initialized. Run '
            'jig init GITREPO to set it up.\n', self.error)
