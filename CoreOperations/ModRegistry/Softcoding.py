import re

# Break the expression into pieces... (?<!\\\[)    (?<=\[)   ([^:\[\]]+)  :  ([^:\[\]]+)   (?<!\\)  (?=\])
# 1) (?<!\\\[)   Make sure the substring doesn't start with \[
# 2) (?<=\[)     Match [, do not include it in result
# 3) ([^:\[\]]+) Match at least one character that does not contain :, [, or ]; make it a group
# 4) :           Match :
# 5) ([^:\[\]]+) Match at least one character that does not contain :, [, or ]; make it a group
# 6) (?<!\\)     Make sure the final character of 5) isn't \
# 7) (?=\])     Match ], do not include it in result
# This expression will match expressions like [keychain:key]
# and ignore those with escape characters on the [ or ], e.g. \[keychain:key]
expr = re.compile(r"(?<!\\\[)(?<=\[)([^:\[\]]+):([^:\[\]]+)(?<!\\)(?=\])")
b_expr = re.compile(rb"(?<!\\\[)(?<=\[)([^:\[\]]+):([^:\[\]]+)(?<!\\)(?=\])")

def search_string_for_softcodes(input_string):
    return expr.finditer(input_string)

def search_bytestring_for_softcodes(input_string):
    return b_expr.finditer(input_string)
