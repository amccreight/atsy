# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import io
import mozinfo
import os
import psutil
import subprocess

from subprocess import Popen, PIPE

class ProcessNotFoundException(Exception):
    """
    Indicates the desired process tree was not found.
    """
    pass


class ProcessStats:
    """
    Wrapper for psutil that provides a cross-platform way of tallying up
    the RSS of a parent process and the USS of its children.
    """

    def __init__(self, path_filter, parent_filter):
        self.path_filter = path_filter
        self.parent_filter = parent_filter

    def get_cmdline(self, proc):
        if mozinfo.os == "win":
            # The psutil.cmdline() implementation on Windows is pretty busted,
            # in particular it doesn't handle getting the command line of a
            # 64-bit process from a 32-bit python process very well.
            #
            # Instead we just shell out the WMIC command which works rather
            # well.
            cmd = "WMIC path win32_process where handle='%d' get Commandline" % (
                proc.pid)
            process = Popen(cmd.split(), stdout=PIPE)
            (output, err) = process.communicate()
            process.wait()

            # The output of WMIC is something like:
            #   Commandline
            #
            #
            #   path/to/exe --args etc

            buf = io.StringIO(output)
            buf.readline()  # header
            for line in buf:
                if line.strip():
                    return line.strip()

            # If all else fails, just return the executable path.
            return p.exe()
        else:
            return " ".join(proc.cmdline())

    def print_stats(self, verbose=False):
        """
        Prints out stats for each matched process and a sum of the RSS of the
        parent process and the USS of its children.

        :param verbose: Set true to see the full command-line. This is useful
         when deciding on a parent filter.
        """
        def wrapped_path_filter(x):
            try:
                return self.path_filter(x.exe())
            except (psutil.AccessDenied, psutil.ZombieProcess):
                return False

        parent_rss = 0
        children_uss = 0

        for p in filter(wrapped_path_filter, psutil.process_iter()):
            info = p.memory_full_info()
            rss = info.rss
            uss = info.uss
            cmdline = self.get_cmdline(p)
            exe = cmdline if verbose else p.exe()

            if self.parent_filter(cmdline):
                print(("[%d] - %s\n  * RSS - %d\n    USS - %d" % (p.pid, exe, rss, uss)))
                parent_rss += rss
            else:
                print(("[%d] - %s\n    RSS - %d\n  * USS - %d" % (p.pid, exe, rss, uss)))
                children_uss += uss

        if not parent_rss:
            if not children_uss:
                raise ProcessNotFoundException(
                    "No processes matched the path filter")
            else:
                raise ProcessNotFoundException(
                    "No process matched the parent filter")

        print(("\nTotal: {:,} bytes\n".format(parent_rss + children_uss)))

class ProcessStatsHelper:
    """
    Helper class to run ProcessStats in a separate process, because it needs to
    be run with sudo (maybe only in OSX?) and we can't run Firefox with sudo.
    """

    def __init__(self, conf_file):
        self.browser = None
        self.conf_file = conf_file

        # XXX Only needed on OSX?
        self.need_sudo = mozinfo.os == "mac"

        # Update the cached credentials before we start the browser.
        if self.need_sudo:
            print("Requesting sudo now so we can use it later without prompting when we're measuring memory.")
            subprocess.run(["sudo", "-v"])

    def set_browser(self, browser):
        self.browser = browser

    def print_stats(self):
        # XXX We don't need to use subprocess.run unless sudo is required, but maybe
        # leave it like this for simplicity?

        if self.need_sudo:
            commands = ["sudo", "-n"]
        else:
            commands = []

        # Need to call set_browser first.
        assert self.browser

        commands.extend(["python", os.path.realpath(__file__),
                         "-b", self.browser,
                         "-c", self.conf_file])

        result = subprocess.run(commands, capture_output=True)
        print(result.stdout.decode("utf-8"))
        if result.stderr:
            print("Subprocess error:")
            print(result.stderr.decode("utf-8"))


if __name__ == "__main__":

    # Default path to the config file containing the SETUP var.
    default_config = os.path.join(
            os.path.dirname(__file__), 'comp_analysis_conf_simple.py')

    # Default browser to test.
    default_browser = 'Firefox'

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', action='store', dest='browser',
                        default=default_browser,
                        help='Adds a browser to the list of browsers to test.')
    parser.add_argument('-c', action='store', dest='conf_file',
                        default=default_config,
                        help='A Python file containing the test configuration.')

    cmdline = parser.parse_args()

    # This loads |SETUP|.
    out = {}
    exec(compile(open(cmdline.conf_file, "rb").read(), cmdline.conf_file, 'exec'), {}, out)

    config = out['SETUP'][mozinfo.os][cmdline.browser]
    stats = ProcessStats(config['path_filter'], config['parent_filter'])
    stats.print_stats()
