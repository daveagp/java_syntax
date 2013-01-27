<?php

require "java.php";

if (function_exists('add_shortcode'))
  add_shortcode('javaTest', 'test_java_syntax');
else
  echo test_java_syntax(null, null) . "\n";

function test_java_syntax($options, $content) {
   $r = "";
   foreach (array(
		  "\\u004eow testing. Gives 5 backslashes: \\\\\\u005c\\\\." .
		  " Won't convert: \\\\u0066, \\u0088. New\\uu000aline, " . 
		  "line\\uuu000dfeed. Ta d\u0061\u0021",
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
		  "too many {{{{s",
		  "balanced but unordered }{",
		  "too many }}}}s",
		  "/* multi-line comment \u000a ends ".
		  "here \\u002a/ while (stuff) {do things;}",
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
		  "carriage\rreturn"
		  ) 
	    as $test) {
     $r .= "\n\n";
     $result = java_parse($test);
     $r .= "<br/>Test<br/>$test<br/> yields flags ";
     foreach ($result as $key => $value) {
       if ($value === True) 
	 $r .= "[$key] ";
     }
     if ($result["text"] == $test) $r .= "<br/>";
     else $r .= "and returns changed text:<br/>".$result["text"]."<br/>";
     if ($result["errmsg"] != "")
       $r .= "and error message:<br/>".$result["errmsg"]."<br/>";
     //break; // for debugging
     if ($result["text_nocomments"] != $result["text"])
       $r .= "Stripped text: " . $result["text_nocomments"]."<br/>";
   }
   return $r;
 };



