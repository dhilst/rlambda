from copy import copy
import re
import sys
from typing import *
from collections import namedtuple as t  # type: ignore

var = t("var", "name")
lamb = t("lamb", "var body")
rappl = t("rappl", "l r")


class ParseError(Exception):
    pass


class EndOfInput(ParseError):
    pass


def pregex(word):
    def _pregex(inp):
        if not inp:
            raise EndOfInput
        match = re.match(rf"\s*({word})", inp)
        if match is not None:
            return match.group(1), inp[match.end(1) :]
        raise ParseError(f"Epxect {word} found {inp}")

    return _pregex


def pand(*parsers):
    def _pall(inp):
        results = []
        for p in parsers:
            res, inp = p(inp)
            results.append(res)
        return results, inp

    return _pall


def por(*parsers):
    def _por(inp):
        for p in parsers:
            try:
                return p(inp)
            except ParseError:
                continue
        raise ParseError(f"Expect any of {parsers}, but no match")

    return _por


def test_parser():
    foo = pregex("foo")
    bar = pregex("bar")
    pand(foo, foo, foo)("foo foo foo")[0] == "foo foo foo".split()
    por(foo, bar)("foo")[0][0] == "foo"
    por(foo, bar)("bar")[0][0] == "bar"

    try:
        foo("")
    except EndOfInput:
        pass
    else:
        assert false, "Expected EndOfInput error"


LPAR = pregex(r"\(")
RPAR = pregex(r"\)")
ARROW = pregex(r"=>")
VAR = pregex(r"\w+")


def pexpr(inp):
    return pexpr_1(inp)


def pexpr_1(inp):
    return por(plamb, pexpr_2)(inp)


def pexpr_2(inp):
    return por(prappl, pexpr_3)(inp)


def pexpr_3(inp):
    return por(pvar, pparen)(inp)


def plamb(inp):
    (v, _, body), inp = pand(VAR, ARROW, pexpr)(inp)
    return lamb(v, body), inp


def pvar(inp):
    v, inp = VAR(inp)
    return var(v), inp


def prappl(inp):
    e1, inp = pexpr_3(inp)
    e2, inp = pexpr(inp)
    return rappl(e1, e2), inp


def pparen(inp):
    (_, e, _), inp = pand(LPAR, pexpr, RPAR)(inp)
    return e, inp


def test_lparser():
    assert pexpr("a") == (var("a"), "")
    assert pexpr("(a)") == (var("a"), "")

    assert pexpr("a b")[0] == rappl(var("a"), var("b"))
    assert pexpr("(a b)")[0] == rappl(var("a"), var("b"))

    assert pexpr("a => b")[0] == lamb("a", var("b"))
    assert pexpr("(a => b)")[0] == lamb("a", var("b"))
    assert pexpr("a => b => c")[0] == lamb("a", lamb("b", var("c")))

    assert pexpr("x (a => b)")[0] == rappl(var("x"), lamb("a", var("b")))
    assert pexpr("x (a => b)")[0] == rappl(var("x"), lamb("a", var("b")))

    assert pexpr("a => a b") == (
        lamb(var="a", body=rappl(l=var(name="a"), r=var(name="b"))),
        "",
    )

    assert pexpr("x a => b => c")[0] == rappl(
        l=var(name="x"), r=lamb(var="a", body=lamb(var="b", body=var(name="c")))
    )
    assert pexpr("x (a => b => c)")[0] == rappl(
        l=var(name="x"), r=lamb(var="a", body=lamb(var="b", body=var(name="c")))
    )

    assert pexpr("x (a => b => c)")[0] == rappl(
        l=var(name="x"), r=lamb(var="a", body=lamb(var="b", body=var(name="c")))
    )

    def _fails(f):
        try:
            r = f()
        except ParseError:
            pass
        else:
            assert False, f"Expected ParseError found {r}"

    # precedence tests
    assert pexpr("a => b => c") == pexpr("a => (b => c)")
    assert pexpr("a => b c") == pexpr("a => (b c)")
    # application is inverted
    assert pexpr("a b => c") == pexpr("a (b => c)")

    assert pexpr("(x => x) (id => 1 id)")[0] == rappl(
        l=lamb(var="x", body=var(name="x")),
        r=lamb(var="id", body=rappl(l=var(name="1"), r=var(name="id"))),
    )

    assert pexpr("1 2 (a => b => a)")[0] == rappl(
        l=var(name="1"),
        r=rappl(
            l=var(name="2"), r=lamb(var="a", body=lamb(var="b", body=var(name="a")))
        ),
    )

    assert pexpr("1 2 (a => b => a)")[0] == pexpr("1 (2 (a => b => a))")[0]


def eval_(term, env={}):
    if type(term) is var:
        try:
            return eval_(env[term.name], env)
        except KeyError:
            return term.name
    elif type(term) is rappl:
        l = eval_(term.l, env)
        r = eval_(term.r, env)
        if type(r) is lamb:
            env[r.var] = l
            res = eval_(r.body, env)
            return eval_(res, env)
    return term


def test_eval():
    assert eval_(pexpr("1 (x => x)")[0]) == "1"
    assert eval_(pexpr("1 2 (a => b => a)")[0]) == "2"
