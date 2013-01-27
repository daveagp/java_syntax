#!/usr/bin/python3
def java_parse(text):
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
    is ; or }. Otherwise it returns a "terminated badly" flag. This is
    mostly to avoid students doing sneaky things where we ask them to
    fill in a spot and then they get it to interact with surrounding fixed
    text. E.g., "x =" on one line followed by our "y = input()" on the next.
    
    Reference:
    http://docs.oracle.com/javase/specs/jls/se7/html/index.html
    
    About preprocessing:
    
    Java allows you to write \uABCD where ABCD are hex digits as a
    replacement for any part of your source text, including comments, javadoc,
    quotes, and actual language structures. For example you
    can start a comment with \* and end it with \u002a\ since unicode code
    point 42 is an asterisk. This makes our job harder. The first thing is to 
    take care of this with preprocessing. We'll only deal with true ASCII (code
    points < 128) since all meaningful Java language characters lie in this
    range, and since dealing with higher ones is a pain in PHP.
    
    We convert all \r\n, \n\r, and isolated \r to \n, to simplify the logic.
    """
    
    def preprocess(rawtext):
        $regex = "(?<!\\\\)((\\\\\\\\)*)\\\\u+00([0-7][[:xdigit:]])";
    // not a backslash, followed by 2k+1 backslashes, u's, 00, two hex digits
    // nb: backslash duplication both for PHP escaping and regex escaping
    
    $tmp = preg_replace_callback("/$regex/", 
				 function($match) {
				   return $match[1] . chr(hexdec($match[3]));
				 },
				 $rawtext);
    
    // normalize carriage returns and newlines. note that other weird unicode
    // newlines (0x2028, 0x2029, 0x0085) are not valid in java source code
    // except in quotes and comments, where they are valid
    $tmp = preg_replace("/\n\r|\r\n|\r/", "\n", $tmp);
    return $tmp;
  }

  var $rawtext, $text;

  function __construct($rawtext) {
    $this->$rawtext = $rawtext;
    $text = $this->preprocess($rawtext);
    $this->parse_loop();
  }

  function report_error($description) {
    if ($errmsg == "") {
      $errmsg = "Error at line $line, column $column:\n" . $description;
    }
  }

  var  // here are the variables that are semantically constant 
    // states (single, multi-line comment; single, double quote)
    $java = 0, $scomment = 1, $mcomment = 2, $squote = 3, $dquote = 4,
    $state_name = array("java", "scomment", "mcomment", "squote", "dquote"),
    // characters
    $bs = "\\", $sq = "'", $dq = "\"",
    $paren_match = array("{" => "}", "}" => "{", "[" => "]", "]" => "[", "(" => ")", ")", "("),
    $paren_name = array("{" => "brace", "}" => "brace", "[" => "bracket", "]" => "bracket",
			"(" => "parenthesis", ")" => "parenthesis");

  var // here are the variables that are not semantically constant
    $oneline = True, $oneline_with_semicolon = False,
    $lastchar = NULL,
    $errmsg = "",
    $text_nocomments = "",
    $next = 0,
    $state = 0, // $java
    $depth = 0,
    $parens = array(),
    $oldstate = -1,
    $line = 0,
    $column = 0;

  public // the output ends up here
    $results;

  function parse_loop() {
    while ($this->$next < strlen($this->$text)) {
      $this->$oldnext = $this->$next;
      $ch = $text[$next];
      $is_newline = $ch == "\n"; // "\r" was removed in preprocessing
      $nextch = ($next+1 == strlen($text)) ? "NA" : $text[$next+1];
      $digram = $ch . $nextch;
      
      /* //for debugging
      //if ($oldstate != $state && $oldstate != -1) 
      echo "[$next $digram $oneline ".$state_name[$state]."]";
      // */
      $oldstate = $state;
      $next++;
      
      if ($is_newline) {
	$line++;
	$column = 0;
      }
      
      if ($state === $java) {
	$is_inline_whitespace = ($ch == "\t") || ($ch == "\f") || ($ch == " ");
	if (!($is_newline || $is_inline_whitespace || $digram == "//"
	      || $digram == "/*"))
	  $lastchar = $ch;
	$oneline_with_semicolon = $oneline_with_semicolon &&
	  ($is_inline_whitespace || ($digram == "//") || ($digram == "/*"));
	if (($is_newline || $ch == ";") && $oneline) {
	  $oneline = False;
	  if ($ch == ";")
	    $oneline_with_semicolon = True;
	}
	if ($ch == '{' or $ch == '(' or $ch == '[' ) {
	  $parens[$depth] = $ch;
	  $depth++;
	}
	if ($ch == '}' or $ch == ')' or $ch == ']' ) {
	  $depth--;
	  if ($depth < 0) { 
	    report_error("Found a closing {$paren_title[$ch]} '$ch' " .
			 "not matching any earlier {$paren_match[$ch]}.");
	    $depth++; // nonsensical, but avoid crashing
	  }
	  else if ($parens[$depth] != $paren_match[$ch])
	    report_error("Found a closing {$paren_title[$ch]} '$ch' " .
			 "where a {$paren_title[$parens[$depth]]} " .
			 "'{$paren_match[$parens[$depth]]}' was expected.");
	}
	if ($ch == $dq) { 
	  $state = $dquote;
	}
	else if ($ch == $sq) {
	  $state = $squote;
	}
	else if ($digram == "//") {
	  $state = $scomment;
	  $next++;
	}
	else if ($digram == "/*") {
	  $state = $mcomment;
	  $next++;
	}
      }
      else if ($state === $dquote) {
	if ($is_newline)
	  report_error("String delimeter (\") followed by end of line.");
	if ($digram == $bs.$bs || $digram == $bs.$dq) {
	  $next++;
	}
	else if ($ch == $dq) {
	  $state = $java;
	}
      }
      else if ($state === $squote) {
	if ($is_newline)
	  report_error("Character delimeter (') followed by end of line.");
	if ($digram == $bs.$bs || $digram == $bs.$sq) {
	  $next++;
	}
	else if ($ch == $sq) {
	  $state = $java;
	}
      }
      else if ($state === $scomment) {
	if ($is_newline) {
	  $state = $java;
	  $text_nocomments .= $ch; // otherwise, would never get added
	}
      }
      else if ($state === $mcomment) {
	if ($digram == "*/") {
	  $state = $java;
	  $next++;
	  $text_nocomments .= ' '; // otherwise, can collapse a keyword and an identifier
	}
      }
      
      // continue parsing the next iteration!
      if (($state != $scomment) and ($state != $mcomment) and ($oldstate != $scomment) and ($oldstate != $mcomment)) {
	for ($i=$oldnext; $i<$next; $i++)
	  $text_nocomments .= $text[$i];
      }
      if (!$is_newline)
	$column += $next - $oldnext;
    }
    
    // parsing loop is done
    if ($state === $squote)
      report_error("Character delimeter (') followed by end of input.");
    else if ($state === $dquote)
      report_error("String delimeter (\") followed by end of input.");
    else if ($state === $mcomment)
      report_error("Comment delimeter (/*) followed by end of input.");
    else if ($depth > 0)
      report_error("Unmatched {$paren_title[$parens[$depth-1]]}: " .
		   "'{$paren_match[$parens[$depth-1]]}' expected at end.");
    
  
    $ends_with_scomment = (($errmsg == "") && ($state === $scomment));
    $valid = ($errmsg == "");
    $results = array("valid" => $valid, "text" => $text, "errmsg" => $errmsg, 
		     "text_nocomments" => $text_nocomments,
		     "oneline" => $oneline,
		     "oneline_with_semicolon" => $oneline_with_semicolon, 
		     "ends_with_scomment" => $ends_with_scomment,
		     "empty" => ($lastchar === NULL),
		     "terminated_badly" => !($lastchar == ";" || $lastchar == "}")); 
  }
}

