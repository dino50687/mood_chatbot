import sys
import io
import tokenize


def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
    changed = False
    new_tokens = []
    for toknum, tokval, start, end, line in tokens:
        if toknum == tokenize.STRING:
            s = tokval
            # find first quote char position
            quote_idx = None
            for i, ch in enumerate(s):
                if ch in ("'", '"'):
                    quote_idx = i
                    break
            if quote_idx is None:
                new_tokens.append((toknum, tokval))
                continue
            prefixes = s[:quote_idx]
            if ("f" in prefixes.lower()) and ("{" not in s) and ("}" not in s):
                # remove 'f' or 'F' from prefixes
                new_prefix = "".join(ch for ch in prefixes if ch.lower() != "f")
                new_tokval = new_prefix + s[quote_idx:]
                tokval = new_tokval
                changed = True
        new_tokens.append((toknum, tokval))
    new_src = tokenize.untokenize(new_tokens)
    # Remove unused imports from app.py
    if path.endswith("app.py"):
        new_src = new_src.replace("import re\n", "", 1)
        new_src = new_src.replace("import json\n", "", 1)
    if changed or new_src != src:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_src)
        print("Fixed", path)
    else:
        print("No changes for", path)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        fix_file(p)
