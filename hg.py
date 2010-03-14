import re
import os
import sys
import time
import contextlib
from StringIO import StringIO

import mercurial.commands
import mercurial.ui
import mercurial.hg

from Chandra.Time import DateTime

ui = mercurial.ui.ui()

def ctime_date(date):
    return time.ctime(DateTime(date).unix)

@contextlib.contextmanager
def stdout_stderr():
    try:
        buf1 = StringIO()
        buf2 = StringIO()
        orig_sys_stdout = sys.stdout
        orig_sys_stderr = sys.stderr
        sys.stdout = buf1
        sys.stderr = buf2
        yield buf1, buf2
    finally:
        sys.stdout = orig_sys_stdout
        sys.stderr = orig_sys_stderr

class Hg(object):
    def __init__(self, repo_dir='.', create=False):
        try:
            self.repo = mercurial.hg.repository(ui, repo_dir)
        except mercurial.error.RepoError:
            if create:
                mercurial.commands.init(ui, repo_dir)
                self.repo = mercurial.hg.repository(ui, repo_dir)
                mercurial.commands.add(ui, self.repo)
            else:
                raise
            
    def commit(self, *args, **kwargs):
        kwargs.setdefault('message', '')
        mercurial.commands.commit(ui, self.repo, *args, **kwargs)

    def logs(self, *args, **kwargs):
        kwargs.setdefault('rev', None)
        kwargs.setdefault('date', None)
        kwargs.setdefault('user', None)

        changelog = {}
        logs = []
        re_keyval = re.compile(r'([a-z]+) : \s* (\S.*)', re.VERBOSE)

        with stdout_stderr() as (buf, buferr):
            mercurial.commands.log(ui, self.repo, *args, **kwargs)

        for line in buf.getvalue().split(os.linesep):
            line = line.strip()
            if not line:
                if changelog:
                    logs.append(changelog)
                changelog = {}
            else:
                key, val = re_keyval.match(line).groups()
                if key == 'changeset':
                    val = re.sub(r'\d+:', '', val)
                changelog[key] = val

        return logs

    def cat(self, filename, date=None, rev=None):
        if date is not None:
            date = ctime_date(date)
            logs = self.logs(date="< %s" % date)
            if logs:
                logs0 = logs[0]
            else:
                print date
                logs0 = self.logs(date="> %s" % date)[-1]
            rev = logs0['changeset']

        with stdout_stderr() as (buf, buferr):
            mercurial.commands.cat(ui, self.repo, filename, rev=rev)

        return buf.getvalue()
    
            



        
