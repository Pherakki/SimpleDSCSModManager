import re

# This RegEx will match any of the following:
# [A::B]
# [A::B|C::D]
# [A::B|C::D::E()]
# [A::B|C::D|E::F]
# [A::B|C::D|E::F::G()]
# etc.
expr_text = b""
expr_text += rb"(?<=\[)"                              # Match [, do not include it in result
expr_text += rb"([a-zA-Z0-9\s]+::[a-zA-Z0-9\s]+\|)*"  # Repeatedly match pairs of alphanumeric 'words' separated by :: and ending with |
expr_text += rb"([a-zA-Z0-9\s]+::[a-zA-Z0-9\s]+)"     # Match a pair of alphanumeric 'words' separated by :: once
expr_text += rb"(::[a-zA-Z0-9\s]+\(\))?"              # Optionally match an alphanumeric word beginning with :: and ending with ()
expr_text += rb"(?=\])"                               # Match ], do not include it in result

expr =   re.compile(expr_text.decode('ascii'))
b_expr = re.compile(expr_text)
def search_string_for_softcodes(input_string):
    return expr.finditer(input_string)

def search_bytestring_for_softcodes(input_string):
    return b_expr.finditer(input_string)
