#!/usr/bin/python3

# Stdin: a Java program
# Stdout: the same Java program with all comments removed, tabified, no blank lines

import java_syntax, sys

print(java_syntax.java_parse(sys.stdin.read()).get_text(keep_comments = False, tabify = True), end="")
