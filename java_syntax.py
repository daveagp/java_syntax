#!/usr/bin/python3
import re
def java_parse(rawtext):
    tabwidth = 4
    """
    Procedure to check whether a snippet of Java 7 text represents
    a single line, a properly nested {} block structure, or none of the above.
     
    A single line is defined as having no newline or semicolon outside of
    comments/quotes. This is not the absolute best definition as you could
    write something like
       do {} while (true)   or   if (x == y++) {} else if (y == z++) {}
    but it does eliminate for-loops and therefore all comma-delimeted
    expression sequences. If you solve an exercise in such a crazy way,
    props to you!
    
    The text is said to be well-terminated if the last non-comment character
    is ; or }. Otherwise it returns a 'terminated badly' flag. This is
    mostly to avoid students doing sneaky things where we ask them to
    fill in a spot and then they get it to interact with surrounding fixed
    text. E.g., 'x =' on one line followed by our 'y = input()' on the next.
    
    Reference:
    http://docs.oracle.com/javase/specs/jls/se7/html/index.html
    
    About preprocessing:
    
    We convert all \r\n, \n\r, and isolated \r to \n, to simplify the logic.

    Java allows you to write \uABCD where ABCD are hex digits as a
    replacement for any part of your source text, including comments, javadoc,
    quotes, and actual language structures. For example you
    can start a comment with \* and end it with \u002a\ since unicode code
    point 42 is an asterisk. This makes our job harder. The first thing is to 
    take care of this with preprocessing. We'll only deal with true ASCII (code
    points < 128) since all meaningful Java language characters lie in this
    range, and since dealing with higher ones is a pain in PHP.
    
    """
    
    def preprocess(rawtext):        
        # not backslash, then 2k+1 backslashes, u's, 00, two hex digits
        # nb: r"..." is a raw string to reduce backslash duplication
        tmp = re.sub(
            r"(?<!\\)((\\\\)*)\\u+00([0-7][0-9A-Fa-f])",
            # on the next line mo is a match object #
            lambda mo: mo.group(1) + chr(int(mo.group(3), 16)),
            rawtext)

        # normalize newlines. note 0x2028, 2029, 0085 are not valid in Java
        tmp = re.sub("\n\r|\r\n|\r", "\n", tmp)
        return tmp

    def report_error(description):
        nonlocal errmsg
        if errmsg=="":
            errmsg = "Error at line {}, column {}:\n{}".format(
                line, column, description)

    def tabify(seq):
        result = []
        line = []
        for item in seq:
            if isinstance(item, str):
                if item=='\n':
                    pass # we assume an integer just appeared
                else:
                    if len(line)==0 and item in whitespace: # kill leading spaces
                        pass
                    else:
                        line.append(item)
            else:
                if len(line)>0: # suppress blank lines
                    result.extend([" "*tabwidth*item, ''.join(line), '\n'])
                line = []
        return ''.join(result)
            

    ### here are the variables that are semantically constant ###
    # states (single, multi-line comment; single, double quote)
    java, scomment, mcomment, squote, dquote = [object() for i in range(5)]

    whitespace = {' ', '\t', '\f', '\n'}
    open_parens = {'{', '(', '['}
    close_parens = {'}', ')', ']'}
    match = {'{':'}', '}':'{', '(':')', ')':'(', '[':']', ']':'['}
    paren_name = {'{':'brace', '[':'bracket', '(':'parenthesis'}
    for p in open_parens: paren_name[match[p]] = paren_name[p]

    ### here are the variables that are not semantically constant ###
    semicolons = 0
    errmsg = ""
    # next two are sequences of characters, digrams, and integers before
    # each EOL/EOF indicating indentation amount of the previous line
    text_nocomments = [] # this is used to tabify and examine endings
    text_wcomments = []  # this is used to tabify
    position = 0
    state = java
    nesting_stack = []
    line = 0
    column = 0
    # line_indent is a running minimum of len(nesting_stack) on the current line
    line_indent = 0

    text = preprocess(rawtext)
    
    ### begin the parsing loop
    while position < len(text):
        # gobbledegook to define old.state, old.position
        old = type('', (), {'position': position, 'state': state})

        ch = text[position]
        is_newline = (ch == "\n") # \r was removed in preprocessing
        nextch = "NA" if (position+1 == len(text)) else text[position+1]
        digram = ch + nextch      
        position += 1      

        if state == java:
            # begin case-checking
            if ch in open_parens:
                nesting_stack.append(ch)
            elif ch in close_parens: 
                if len(nesting_stack) == 0: 
                    report_error(
                        "Found a closing '{}' not matching any earlier '{}'.".
                        format(ch, match[ch]))
                elif nesting_stack[-1] != match[ch]:
                    report_error(
                        "Found a closing '{}' where a '{}' was expected.".
                        format(ch, match[nesting_stack[-1]]))
                else:
                    nesting_stack.pop()
            elif ch == '"':
                state = dquote
            elif ch == "'":
                state = squote
            elif digram == '//':
                state = scomment
                position += 1
            elif digram == '/*':
                state = mcomment
                mcomment_start_line = line
                position += 1
            elif ch == ';':
                semicolons += 1
        # end of checking from 'java' state
        elif state == dquote:
            if is_newline:
                report_error('String delimeter (") followed by end of line.')
            elif digram in {r"\\", r'\"'}:
                position += 1
            elif ch == '"':
                state = java
        elif state == squote:
            if is_newline:
                report_error(
                    "Character delimeter (') followed by end of line.")
            elif digram in {r"\\", r"\'"}:
                position += 1
            elif ch == "'":
                state = java
        elif state == scomment:
            if is_newline:
                state = java
                text_nocomments.append(line_indent)
                text_nocomments.append('\n')
        elif state == mcomment:
            if digram == "*/":
                state = java
                position += 1
                if mcomment_start_line == line: # one-line /*comment*/
                    text_nocomments.append(' ')
                else:
                    text_nocomments.append(line_indent)
                    text_nocomments.append('\n')

      
        # continue parsing the next iteration!
        if is_newline:
            text_nocomments.append(line_indent)
            text_wcomments.append(line_indent)
            line += 1
            column = 0
            line_indent = len(nesting_stack)
        else:
            column += position - old.position
            line_indent = min(line_indent, len(nesting_stack))

        consumed = text[old.position:position]
        if len({state, old.state}.intersection({scomment, mcomment}))==0:
            text_nocomments.append(consumed)
        text_wcomments.append(consumed)

    # parsing loop is done
    if state == squote:
        report_error("Character delimeter (') followed by end of input.")
    elif state == dquote:
        report_error("String delimeter (\") followed by end of input.")
    elif state == mcomment:
        report_error("Comment delimeter (/*) followed by end of input.")
    elif len(nesting_stack) > 0:
        report_error("Unmatched '{}'. Expected '{}' at end.".format(
            nesting_stack[-1], match[nesting_stack[-1]]))

    text_nocomments.append(line_indent)
    text_wcomments.append(line_indent)

    result = {}
    valid = errmsg == ""

    last_significant_char = None
    for item in reversed(text_nocomments):
        if item in whitespace: continue
        last_significant_char = item
        break

    result["valid"] = valid
    result["ends_with_scomment"] = valid and state == scomment
    result["text"] = text
    result["errmsg"] = errmsg
    result["text_nocomments"] = ''.join(filter(lambda x: isinstance(x, str),
                                               text_nocomments))
    result["oneline"] = "\n" not in text and semicolons == 0
    result["oneline_with_semicolon"] = ("\n" not in text and semicolons == 1
                                        and last_significant_char == ';')
    result["empty"] = last_significant_char == None
    result["terminated_badly"] = last_significant_char not in {";", "}", None}
    result["tabified_nocomments"] = tabify(text_nocomments)
    result["tabified_wcomments"] = tabify(text_wcomments)    
    
    return result

def run_tests():
    tests = [
        ("\\u004eow testing. Gives 5 backslashes: \\\\\\u005c\\\\." +
         " Will not convert: \\\\u0066, \\u0088. New\\uu000aline, " +
         "line\\uuu000dfeed. Ta d\u0061\u0021"),
        "a single line",
        "a single line with newline at end\n",
        "a single line with cr at end\r",
        "a single line with tab at end\t",
        "a single line with semicolon at end;",
        "a single line with semicolon and tab at end;\t",
        "a single line with semicolon and newline at end;\n",
        "two semicolons;;",
        "quoted semicolon \";\"",
        "single-quoted semicolon ';'",
        "commented semicolon /*;*/",
        "inline-commented semicolon //;",
        "semicolon followed by comments; /* blah; */ // ",
        "semicolon followed by quotes; 'yeah'",
        "good braces {}{}{{{}}}",
        "wrong kind \u000a of braces {]",
        "wrong kind of braces {(})",
        "angle brackets arent checked --- since they are operators <>",
        "too many {{{{s",
        "balanced but unordered }{",
        "too many }}}}s",
        ("/* multi-line comment \u000a ends" +
         " here \\u002a/ while (stuff) {do things;}"),
        "/* this // is \n a valid comment \"'*/",
        "a very short comment; /**/",
        "a very short comment /\\u002a\\u002a/",
        "a quote \"containing \n a newline\"",
        "a quote '\n' with a newline",
        "a quote \"\\\\\" with 2 bses",
        "a quote \"\\\\\\\" with 3 bses",
        "unmatched \"!",
        "unmatched '!",
        "empty quotes '' \"\" ... the next test is an empty string",
        "",
        "3 windows newlines\r\n\r\n\r\n",
        "carriage\u000dreturn",
        "here/*space*/inserted",
        "here/*newline\n*/inserted",
        "here//newline\ninserted"]

    r = []
    for test in tests:
        r.append("\n\n")
        result = java_parse(test)
        r.append("<br/>Test<pre>"+test+"</pre> yields flags ")
        for k, v in result.items():
            if v is True:
                r.append("["+k+"] ")

        if result["text"] == test:
            r.append("<br/>")
        else:
            r.append("and returns changed text:<pre>"+result["text"]+"</pre>")

        if not result["valid"]:
            r.append("and error message:<br/>"+result["errmsg"]+"<br/>")

        if result["text_nocomments"] != result["text"]:
            r.append("Stripped text: <pre>"+result["text_nocomments"]+"</pre><br/>")

    return ''.join(r)

def run_tabify_tests():
    r = []
    tests = ["forloop {\n ifstatement { \n body1; \nbody2;\n}\n}",
             "forloop \n{\n ifstatement  \n{\n body1; \nbody2;\n}\n}",
             "if () {\n stuff \n } else { \n stuff \n}",
             "if () \n{\n stuff \n }\nelse\n{\n stuff\n }",
             "int[][] x = new int[][]{\n{1, 2},\n,\n{1, 2,\n3\n}\n}",
             "((\nshould not indent two levels\n))"
             ]
    for test in tests:
        r.append("\n\n<br>")
        result = java_parse(test)
        r.append("<br/>Test<pre>"+test+"</pre>")
        r.append("<br/>Tabified:<pre>"+result["tabified_wcomments"]+"</pre>")
        if result["tabified_wcomments"] != result["tabified_nocomments"]:
            r.append("<br/>Tabified, no comments:<pre>"+result["tabified_nocomments"]+"</pre>")
    return ''.join(r)
