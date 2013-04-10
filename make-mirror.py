#!/usr/bin/python3

# arguments: none
# effct: create a directory .nocomments which mirrors the .java files in the current one, but with all comments deleted

import java_syntax, sys, os

mode = "normal"
if sys.argv[1:] == ["--succinct"]:
    mode = "succinct"
if sys.argv[1:] == ["--quiet"]:
    mode = "quiet"


if mode == "succinct":
    print("Making a commentless copy of .java files into .nocomments", end="")

os.system("rm -rf .nocomments")
for (path, dirnames, filenames) in os.walk(".", followlinks=True):
    if path.startswith("./."): continue # skip "hidden" directories
    os.system("mkdir .nocomments" + path[1:])

    if mode == "normal":
        print("Making a comment-stripped copy in .nocomments" + path[1:] + " of: ", end="")
    elif mode == "succinct":
        print(".", end="")
        sys.stdout.flush()

    for filename in filenames:
        if not filename.endswith(".java"): continue

        fullpath = os.path.join(path, filename)
        newcopy = ".nocomments" + fullpath[1:] # replace . with .nocomments
        
        if mode == "normal":
            print(filename, end=" ")
        elif mode == "succinct":
            print(".", end="")
            sys.stdout.flush()
        
        fin = open(fullpath)
        original = fin.read()
        fin.close()
        
        fout = open(newcopy, 'w')
        nocomments = java_syntax.java_parse(original).get_text(keep_comments = False, tabify = True)
        print(nocomments, file=fout, end="")
    if mode == "normal": print()
if mode == "succinct": print()
