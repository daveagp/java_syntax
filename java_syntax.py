#!/usr/bin/python3
import re

"""
TODO for indentations:
1: handle inline-if/while/do loops correctly
2: prevent multiple indents on a single line
3: look for implied line continuations
4: switch

1:
- e.g. if()\nFOO; should indent FOO;
- this can occur after if(...), else, while(...), do
- likely implementation: put items on stack, delete all topmost
  inline blocks when a ; or } is processed
- make sure if()\nif()\nelse is indented logically!
  such an else should only close the latest if()
- if()\s*[not {] denotes the start of an inline-if, but the indent
  should be counted as starting right after the parenthesis
2:
- e.g. {{\nFOO should indent FOO by only one level
- similar with for() for() {\n...
3:
- maybe ; and } and , are the non-continuing characters?
4:
- inside of switch(){...} is indented by 2,
  but lines starting with 'symbol:' get indented only by 1.

test cases for 1+2: 'for()for()\n{\nFOO' should give
for()for()
{
   FOO
while 'x = {{foo,\nbar},\nbaz};' should give
x = {{foo,
   bar},
   baz};
"""

def record(**dict):
    """ e.g. foo = record(bar='baz', jim=5) creates an object foo
    such that foo.bar == 'baz', foo.jim == 5 """
    return type('', (), dict)

# parser states
java, scomment, mcomment, squote, dquote = [
    record(name = n) for n in [
    "JAVA", "SINGLE-LINE COMMENT", "MULTI-LINE COMMENT",
    "SINGLE-QUOTED LITERAL", "DOUBLE-QUOTED LITERAL"]]

def is_comment(state): return state in {scomment, mcomment}

whitespace = {' ', '\t', '\f', '\n'}
open_parens = {'{', '(', '['}
close_parens = {'}', ')', ']'}
match = {'{':'}', '}':'{', '(':')', ')':'(', '[':']', ']':'['}
paren_name = {'{':'brace', '[':'bracket', '(':'parenthesis'}
for p in open_parens: paren_name[match[p]] = paren_name[p]

default_tab_width = 4
    
def java_parse(rawtext):
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

    def tabify_output_list(keep_comments, tab_width):
        result = []
        line = []
        for item in output_list:
            if item.type=='text':
                if item.chars=='\n':
                    pass  # handled by 'indent'
                          # although it may add '\n' to very end
                elif not keep_comments and item.is_comment:
                    pass
                elif len(line)==0 and item.chars in whitespace: 
                    pass  # kill leading spaces
                else:
                    line.append(item.chars)
            elif item.type=='indent':
                # suppress blank lines if comments are off
                if keep_comments or len(line) > 0:
                    result.append(" " * tab_width * item.indent)
                    result.extend(line)
                    result.append('\n')
                    line = []
            else: assert False, "unknown type "+str(item.type)+"in tabify"
        return ''.join(result)

    def get_text(keep_comments = True, tabify = False, tab_width = default_tab_width):
        if tabify:
            return tabify_output_list(keep_comments = keep_comments,
                                      tab_width = tab_width)
        else:
            if keep_comments:
                return text
            else:
                return ''.join(i.chars for i in output_list
                               if i.type=='text' and not i.is_whitespace)

    def register_newline():
        nonlocal output_list
        output_list.append(record(type = 'indent', indent = line_indent))

    ### here are the variables that are not semantically constant ###
    semicolons = 0
    errmsg = ""
    output_list = []   # list of characters and metadata used for output
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
        # define old.state, old.position
        old = record(position = position, state = state)

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
        elif state == mcomment:
            if digram == "*/":
                state = java
                position += 1
                if mcomment_start_line == line: 
                    # fake whitespace! not pretty, but practical.
                    # this is to avoid tokens/* */collapsing.
                    # who really uses a one-line/* */anyway?
                    output_list.append(record(type = 'text',
                                              chars = ' ',
                                              is_comment = False))

      
        # continue parsing the next iteration!
        if is_newline:
            register_newline()
            line += 1
            column = 0
            line_indent = len(nesting_stack)
        else:
            column += position - old.position
            line_indent = min(line_indent, len(nesting_stack))

        output_list.append(record(
            type = 'text',
            chars = text[old.position:position],
            is_comment = ((is_comment(state) or is_comment(old.state))
                          and not (state == java and old.state == scomment))
            ))
        
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

    register_newline()

    result = {}
    valid = errmsg == ""

    last_significant_char = None
    for item in reversed(output_list):
        if item.type != 'text': continue
        if item.chars in whitespace: continue
        if item.is_comment: continue
        last_significant_char = item.chars[-1:]
        break

    return record(
        errmsg = errmsg,
        valid = valid,
        ends_with_scomment = valid and state == scomment,
        oneline = "\n" not in text and semicolons == 0,
        oneline_with_semicolon = ("\n" not in text and semicolons == 1
                                  and last_significant_char == ';'),
        empty = last_significant_char == None,
        terminated_badly = last_significant_char not in {";", "}", None},
        get_text = get_text,
        semicolons = semicolons
    )

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
        "here//newline\ninserted",
        "foo",
        "foo;\nbar;",
        "foo;\nbar//;",
]

    r = []
    for test in tests:
        r.append("\n\n")
        result = java_parse(test)
        r.append("<br/>Test<pre>"+test+"</pre> yields flags ")
        for k, v in result.__dict__.items():
            if v is True:
                r.append("["+k+"] ")

        gt = result.get_text
        if gt() == test:
            r.append("<br/>")
        else:
            r.append("and returns changed text:<pre>"+gt()+"</pre>")

        if not result.valid:
            r.append("and error message:<br/>"+result.errmsg+"<br/>")

        if gt(keep_comments = True) != gt():
            r.append("Stripped text: <pre>" + gt(keep_comments = True) + "</pre><br/>")

    return ''.join(r)

def run_tabify_tests():
    r = []
    tests = ["forloop {\n ifstatement { \n body1; \nbody2;\n}\n}",
             "forloop \n{\n ifstatement  \n{\n body1; \nbody2;\n}\n}",
             "if () {\n stuff \n } else { \n stuff \n}",
             "if () \n{\n stuff \n }\nelse\n{\n stuff\n }",
             "int[][] x = new int[][]{\n{1, 2},\n,\n{1, 2,\n3\n}\n}",
             "((\nshould not indent two levels\n))",
             ("for (){ // some comment blah \n // comment \n stuff /* multi\n"+
              "line*/ \n} // endish") 
             ]

    for test in tests:
        
        result = java_parse(test)
        with_comments = result.get_text(tabify = True, keep_comments = True)
        no_comments = result.get_text(tabify = True, keep_comments = False)

        r.append("\n\n<br>")
        r.append("<br/>Test<pre>"+test+"</pre>")
        r.append("<br/>Tabified:<pre>" + with_comments + "</pre>")
        if with_comments != no_comments:
            r.append("<br/>Tabified, no comments:<pre>" + no_comments + "</pre>")

    return ''.join(r)
