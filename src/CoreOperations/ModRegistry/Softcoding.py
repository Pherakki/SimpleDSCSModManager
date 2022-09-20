import re

# This RegEx will match any of the following:
# [A::B]
# [A::B|C::D]
# [A::B|C::D::E()]
# [A::B|C::D|E::F]
# [A::B|C::D|E::F::G()]
# etc.
capture_block = r"[a-zA-Z0-9\s_]"
expr_text = ""
expr_text += r"(?<=\[)"                                             # Match [, do not include it in result
expr_text += r"({}+::{}+\|)*".format(capture_block, capture_block)  # Repeatedly match pairs of alphanumeric 'words' separated by :: and ending with |
expr_text += r"({}+::{}+)".format(capture_block, capture_block)     # Match a pair of alphanumeric 'words' separated by :: once
expr_text += r"(::{}+\(\))?".format(capture_block)                  # Optionally match an alphanumeric word beginning with :: and ending with ()
expr_text += r"(?=\])"                                              # Match ], do not include it in result

expr =   re.compile(expr_text)
b_expr = re.compile(expr_text.encode('ascii'))

def search_string_for_softcodes(input_string):
    return expr.finditer(input_string)

def search_bytestring_for_softcodes(input_string):
    return b_expr.finditer(input_string)
