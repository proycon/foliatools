
def makencname(s):
    s = s.replace(" ","_")
    s = s.replace(":","_")
    if s and not s[0].isalpha() and s[0] != '_':
        s = "_" + s
    return s

def set_metadata(doc, **kwargs):
    for key, value in kwargs.items():
        doc.metadata[key] = value

