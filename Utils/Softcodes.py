import os


def replace_softcodes(text_bytes, text_softcodes, softcode_lookup):
   
    if text_softcodes is not None:
        all_replacements = []
        for match, offsets in text_softcodes.items():
            value = softcode_lookup[match]
            softcode_length = len(match) + 2 # For [ and ]
            for offset in offsets:
                all_replacements.append((offset, value, softcode_length))
        all_replacements = sorted(all_replacements, key=lambda x : x[0])
        
        offset_adjustment = 0
        for offset, value, softcode_length in all_replacements:
            text_a = text_bytes[:offset + offset_adjustment]
            text_b = text_bytes[offset + offset_adjustment + softcode_length:]
            str_value = str(value).encode('utf8')
            text_bytes = text_a + str_value + text_b
            offset_adjustment += len(str_value) - softcode_length
        
    return text_bytes