#!/usr/bin/python3
def java_parse(rawtext):
    """
    Procedure to check whether a snippet of Java 7 text represents
    a single line, a properly nested {} block structure, or none of the above.
     
    A single line is defined as having no \r\n; outside of comments/quotes.
    This is not the absolute best definition as you could write something like
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
        import re
        
        # not backslash, then 2k+1 backslashes, u's, 00, two hex digits
        # nb: r"..." is a raw string to reduce backslash duplication
        tmp = re.sub(
            r"(?<!\\)((\\\\)*)\\u+00([0-7][[0-9A-Fa-f]])",
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
            
    ### here are the variables that are semantically constant ###
    # states (single, multi-line comment; single, double quote)
    java, scomment, mcomment, squote, dquote = [object() for i in range(5)]

    open_parens = {'{', '(', '['}
    close_parens = {'}', ')', ']'}
    match = {'{':'}', '}':'{', '(':')', ')':'(', '[':']', ']':'['}
    paren_name = {'{':'brace', '[':'bracket', '(':'parenthesis'}
    for p in open_parens: paren_name[match[p]] = paren_name[p]

    ### here are the variables that are not semantically constant ###
    oneline = True
    oneline_with_semicolon = False
    last_significant_char = None
    errmsg = ""
    text_nocomments = []
    next = 0
    state = java
    parens = []
    oldstate = -1
    line = 0
    column = 0

    text = preprocess(rawtext)
    
    ### begin the parsing loop
    while next < len(text):
        oldnext = next
        ch = text[next]
        is_newline = (ch == "\n") # \r was removed in preprocessing
        nextch = "NA" if (next+1 == len(text)) else text[next+1]
        digram = ch + nextch
      
        #/* //for debugging
        #//if ($oldstate != $state && $oldstate != -1) 
        #echo "[$next $digram $oneline ".$state_name[$state]."]"
        #// */

        oldstate = state
        next += 1      

        if state == java:
            is_inline_whitespace = ch in {"\t", "\f", " "}
            if not (is_newline or is_inline_whitespace
                    or digram in {"//", "/*"}):
                last_significant_char = ch

            oneline_with_semicolon &= (is_inline_whitespace
                                       or digram in {"//", "/*"})

            # begin case-checking
            if (is_newline or ch == ";") and oneline:
                oneline = False
                if ch == ';':
                    oneline_with_semicolon = True                
            elif ch in open_parens:
                parens.append(ch)
            elif ch in close_parens: 
                if len(parens) == 0: 
                    report_error(
                        "Found a closing '{}' not matching any earlier '{}'.".
                        format(ch, match[ch]))
                elif parens[-1] != match[ch]:
                    report_error(
                        "Found a closing '{}' where a '{}' was expected.".
                        format(ch, match[parens[-1]]))
                else:
                    parens.pop()
            elif ch == '"':
                state = dquote
            elif ch == "'":
                state = squote
            elif digram == '//':
                state = scomment
                next += 1
            elif digram == '/*':
                state = mcomment
                next += 1
        # end of checking from 'java' state
        elif state == dquote:
            if is_newline:
                report_error('String delimeter (") followed by end of line.')
            elif digram in {r"\\", r'\"'}:
                next += 1
            elif ch == '"':
                state = java
        elif state == squote:
            if is_newline:
                report_error(
                    "Character delimeter (') followed by end of line.")
            elif digram in {r"\\", r"\'"}:
                next += 1
            elif ch == "'":
                state = java
        elif state == scomment:
            if is_newline:
                state = java
                text_nocomments.append(ch)
        elif state == mcomment:
            if digram == "*/":
                state = java
                next += 1
                text_nocomments.append(' ')
      
        # continue parsing the next iteration!
        if len({state, oldstate}.intersection({scomment, mcomment}))==0:
            text_nocomments.append(text[oldnext:next])
            
        if is_newline:
            line += 1
            column = 0
        else:
            column += next - oldnext
    
    # parsing loop is done
    if state == squote:
        report_error("Character delimeter (') followed by end of input.")
    elif state == dquote:
        report_error("String delimeter (\") followed by end of input.")
    elif state == mcomment:
        report_error("Comment delimeter (/*) followed by end of input.")
    elif len(parens) > 0:
        report_error("Unmatched '{}': '{}' expected at end.".format(
            parens[-1], match[parens[-1]]))

    result = {}
    valid = errmsg == ""

    result["valid"] = valid
    result["ends_with_scomment"] = valid and state == scomment
    result["text"] = text
    result["errmsg"] = errmsg
    result["text_nocomments"] = ''.join(text_nocomments)
    result["online"] = oneline
    result["empty"] = last_significant_char == None
    result["terminated_badly"] = last_significant_char not in {"", "}", None}

    return result

def run_tests():
    tests = [
        ("\\u004eow testing. Gives 5 backslashes: \\\\\\u005c\\\\." +
         " Won't convert: \\\\u0066, \\u0088. New\\uu000aline, " +
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
        "wrong kind of braces {]",
        "wrong kind of braces {(})",
        "angle brackets aren't checked --- since they are operators <>",
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
        "carriage\u000dreturn"]

    r = []
    for test in tests:
        r.append("\n\n")
        result = java_parse(test);
        r.append("<br/>Test<br/>"+test+"<br/> yields flags ")
        for k, v in result.items():
            if v is True:
                r.append("["+k+"] ")

        if result["text"] == test:
            r.append("<br/>")
        else:
            r.append("and returns changed text:<br/>"+result["text"]+"<br/>")

        if not result["valid"]:
            r.append("and error message:<br/>"+result["errmsg"]+"<br/>")

        if result["text_nocomments"] != result["text"]:
            r.append("Stripped text: "+result["text_nocomments"]+"<br/>")
    return ''.join(r)

