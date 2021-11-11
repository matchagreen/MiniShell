# MiniShell
A runnable shell build using Python. This shell was made for my Operating Systems class.

Here are some of the things the shell is capable of doing:
- Read unix command from the user and execute it
- Supports background tasks when the last character in the input is '&'
- Run commands that name a program anywhere in the PATH
- Change current directory using the cd command
- Support redirection of input and output using '<' and '>', respectively
- Support simple pipes with '|'
- Print 'Program terminated: exit code n' when a program fails
- Print an error message when a command is not found

To run the mini-shell, simply run the script as:
    python3 main.py
    
