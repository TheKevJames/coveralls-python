from subprocess import Popen, PIPE


def run_command(*args, **kwargs):
    _args = list(args)
    if kwargs.get('shell'):
        _args = " ".join(_args)
    cmd = Popen(_args, stdout=PIPE, stderr=PIPE, **kwargs)
    stdout, stderr = cmd.communicate()
    assert cmd.returncode == 0, ('command return code %d, STDOUT: "%s"\n'
                                 'STDERR: "%s"' % (cmd.returncode, stdout, stderr))
    try:
        output = stdout.decode()
    except UnicodeDecodeError:
        output = stdout.decode('utf-8')
    return output
