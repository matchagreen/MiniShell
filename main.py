import sys
import re
import os


def change_directory(args):
    if len(args) != 2:
        print('Please provide exactly 1 directory when using command cd')
        return
    try:
        os.chdir(args[1])
    except FileNotFoundError as e:
        print(e)


# Executes an executable located in the indicated directory,
# or anywhere in the path.
def environ_exec(args):
    for dir in re.split(':', os.environ['PATH']):
        try:
            os.execv(dir + '/' + args[0], args)
        except FileNotFoundError:
            pass
    print(f"Could not execute '{args[0]}'. Command not found.")
    exit()


# Creates a child process that creates two grandchild executables
# and waits for them. The method returns the pid of the child
# process.
def child_pipe(args_read, args_write):
    rc = os.fork()
    if rc < -1:
        print('Fork failed')
        exit(1)
    elif rc == 0:
        fds = os.pipe()
        rc_read = grandchild_read(args_read, fds)
        rc_write = grandchild_write(args_write, fds)
        os.close(fds[0])
        os.close(fds[1])

        # Wait for grandchildren and pring error if necessary
        status = os.waitpid(rc_read, 0)
        if status[1] != 0:
            print(f'Program terminated: exit code {status[1]}')
        status = os.waitpid(rc_write, 0)
        if status[1] != 0:
            print(f'Program terminated: exit code {status[1]}')
        exit()
    return rc


def grandchild_read(args_read, fds):
    rc = os.fork()
    if rc < -1:
        print('Fork failed')
        exit(1)
    elif rc == 0:
        os.dup2(fds[0], 0)
        os.close(fds[1])
        environ_exec(args_read)
    return rc


def grandchild_write(args_write, fds):
    rc = os.fork()
    if rc < -1:
        print('Fork failed')
        exit()
    elif rc == 0:
        os.dup2(fds[1], 1)
        os.close(fds[0])
        environ_exec(args_write)
    return rc


def child_out_redirect(args, input_file):
    rc = os.fork()
    if rc < -1:
        print('Fork failed')
        exit()
    elif rc == 0:
        grandchild_out_redirect(args, input_file)
        status = os.wait()  # Always waits for grandchild
        if status[1] != 0:
            print(f'Program terminated: exit code {status[1]}')
        exit()
    return rc


def grandchild_out_redirect(args, input_file):
    rc = os.fork()
    if rc < 0:
        print('Fork failed')
        exit(1)
    elif rc == 0:   # Executed by grandchild
        fd = os.open(input_file, os.O_RDWR | os.O_CREAT)
        os.dup2(fd, 1)
        environ_exec(args)


def child_in_redirect(args, input_file):
    rc = os.fork()
    if rc < -1:
        print('Fork failed')
        exit()
    elif rc == 0:
        grandchild_in_redirect(args, input_file)
        status = os.wait()  # Always waits for grandchild
        if status[1] != 0:
            print(f'Program terminated: exit code {status[1]}')
        exit()

    return rc


def grandchild_in_redirect(args, input_file):
    rc = os.fork()
    if rc < 0:
        print('Fork failed')
        exit(1)
    elif rc == 0:   # Executed by grandchild
        fd = os.open(input_file, os.O_RDWR | os.O_CREAT)
        os.dup2(fd, 0)
        environ_exec(args)


# Creates a child process that creates a grandchild executable,and
# waits for it. The method returns the pid of the child process.
def child(args):
    rc = os.fork()
    if rc < 0:
        print('Fork failed')
        exit(1)
    elif rc == 0:   # Executed by child
        grandchild(args)
        status = os.wait()  # Always waits for grandchild
        if status[1] != 0:
            print(f'Program terminated: exit code {status[1]}')
        exit()
    return rc


# Creates a grandchild that becomes the executable indicated.
def grandchild(args):
    rc = os.fork()
    if rc < 0:
        print('Fork failed')
        exit(1)
    elif rc == 0:   # Executed by grandchild
        environ_exec(args)


os.environ['PATH'] += ':'  # Allows user to specify exact directory
while True:
    will_wait = True

    line = input('$$$$ ')

    # Look for indications
    if line and line[-1] == '&':
        will_wait = False
        line = line[:-1]    # Removes '&'
    if not line:
        continue
    elif line == 'quit':
        break

    # Handles piping
    if '|' in line:
        args = line.split('|')
        args_write = args[0].split()
        args_read = args[1].split()
        child_pid = child_pipe(args_read, args_write)

    # Handles output redirection
    elif '>' in line:
        args = line.split('>')
        input_file = args[-1].strip()
        args = args[0].split()
        child_pid = child_out_redirect(args, input_file)

    # Handles input redirection
    elif '<' in line:
        args = line.split('<')
        input_file = args[-1].strip()
        args = args[0].split()
        child_pid = child_in_redirect(args, input_file)

    # Handles everything else
    else:
        args = line.split()

        # If changing directory
        if args[0] == 'cd':
            change_directory(args)
            continue    # Ignore waiting if any

        child_pid = child(args)

    # Wait if indicated
    if will_wait:
        os.waitpid(child_pid, 0)
