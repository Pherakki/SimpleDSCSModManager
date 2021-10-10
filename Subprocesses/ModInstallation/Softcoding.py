import re

# Break the expression into pieces... (?<!\\)   \[   [^:\[\]]+  :  [^:\[\]]+   (?<!\\)  \]
# 1) (?<!\\)    Make sure the substring doesn't start with \
# 2) \[         Match [
# 3) [^:\[\]]+  Match at least one character that does not contain :, [, or ]
# 4) :          Match :
# 5) [^:\[\]]+  Match at least one character that does not contain :, [, or ]
# 6) (?<!\\)    Make sure the final character of 5) isn't \
# 7) \]         Match ]
# This expression will match expressions like [keychain:key]
# and ignore those with escape characters on the [ or ], e.g. \[keychain:key]
expr = re.compile(r"(?<!\\)\[[^:\[\]]+:[^:\[\]]+(?<!\\)\]")

def search_string_for_softcodes(input_string):
    return set(expr.findall(input_string))

def construct_softcode_links(codes):
    out = {}
    # Dummy code, needs to have a range for each code class and link to pre-set code classes 
    for i, code in enumerate(codes):
        code_class, key = code[1:-1].split(':')
        out[code] = str(i)
    return out