"""Tiny S-expression reader/writer for KiCad files."""
import re

_tok = re.compile(r'\s*(\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+)')


def parse(text):
    stack, cur = [], []
    for m in _tok.finditer(text):
        t = m.group(1)
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t)
    return cur[0] if len(cur) == 1 else cur


def dump(node, indent=0):
    if not isinstance(node, list):
        return node
    if all(not isinstance(x, list) for x in node):
        return "(" + " ".join(node) + ")"
    pad = "  " * (indent + 1)
    out = "("
    first = True
    for x in node:
        if isinstance(x, list):
            out += "\n" + pad + dump(x, indent + 1)
        else:
            out += ("" if first else " ") + x
        first = False
    return out + ")"


def find(node, head):
    return [x for x in node if isinstance(x, list) and x and x[0] == head]


def walk(node, head):
    if isinstance(node, list):
        if node and node[0] == head:
            yield node
        for x in node:
            yield from walk(x, head)


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def unq(s):
    return s[1:-1].replace('\\"', '"') if s.startswith('"') else s
