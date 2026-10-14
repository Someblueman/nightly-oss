"""Independent checker initially defined before reading candidate source/tests.

Oracle: Python's documented format-string grammar permits every source character
except ']' inside an item index. Only omitted positional argument names should
be supplied; all other source text must survive unchanged.
Run inside the trusted night.py helper, using python -c; never on the host.
"""
from itertools import product
import json


def cases():
    keys = ['{', '}', '{}', '{{', '}}', '{{}}', '{!r:}', '[', '[{', '{[',
            'a.b', 'a!r', 'a:3', ' ', '\t', 'é', '😀', '0{1}']
    keys += [''.join(chars) for size in range(1, 4)
             for chars in product('{}[!:a', repeat=size)]
    for key in dict.fromkeys(keys):
        lookup = '[' + key + ']'
        obj = {key: 'é'}
        for conv in ('', '!s', '!r', '!a'):
            for spec in ('', ':>12'):
                yield ('{' + lookup + conv + spec + '} {}',
                       '{0' + lookup + conv + spec + '} {1}',
                       (obj, 'tail'), {})
                yield ('{named' + lookup + conv + spec + '} {}',
                       '{named' + lookup + conv + spec + '} {0}',
                       ('tail',), {'named': obj})
                yield ('{0' + lookup + conv + spec + '} {1}',
                       '{0' + lookup + conv + spec + '} {1}',
                       (obj, 'tail'), {})
        yield ('{' + lookup + ':>{}} {}',
               '{0' + lookup + ':>{1}} {2}', (obj, 8, 'tail'), {})
        yield ('{named' + lookup + ':>{}} {}',
               '{named' + lookup + ':>{0}} {1}', (8, 'tail'), {'named': obj})
        yield ('{' + lookup + '[x{}]!r} {}',
               '{0' + lookup + '[x{}]!r} {1}', ({key: {'x{}': 'é'}}, 'tail'), {})
        yield ('{:>{' + lookup + '}} {}',
               '{0:>{1' + lookup + '}} {2}', ('é', {key: 8}, 'tail'), {})
        yield ('{:>{width' + lookup + '}} {}',
               '{0:>{width' + lookup + '}} {1}', ('é', 'tail'), {'width': {key: 8}})
        for literal in ('[', ']', '[]', '[[', '{{', '}}', '{{[]}}', '[{{}}]'):
            yield (literal + '{' + lookup + '} {}' + literal,
                   literal + '{0' + lookup + '} {1}' + literal,
                   (obj, 'tail'), {})
    for text, expected, args in [
        ('{} {}', '{0} {1}', ('a', 'b')),
        ('{:>{}} {}', '{0:>{1}} {2}', ('a', 5, 'b')),
        ('{:[>8} {}', '{0:[>8} {1}', ('a', 'b')),
        ('{:]>8} {}', '{0:]>8} {1}', ('a', 'b')),
        ('{{{}}}', '{{{0}}}', ('a',)),
        ('{{}} {} {{}} {}', '{{}} {0} {{}} {1}', ('a', 'b')),
        ('{[0]} {[12]}', '{0[0]} {1[12]}', ({0: 'a'}, {12: 'b'})),
        ('{.real} {}', '{0.real} {1}', (1 + 2j, 'b')),
        ('{[{}].real} {}', '{0[{}].real} {1}', ({'{}': 1 + 2j}, 'b')),
        ('{.real:>{}} {}', '{0.real:>{1}} {2}', (1 + 2j, 8, 'b')),
    ]:
        yield text, expected, args, {}


def check(infer, label, tokenize=None):
    total = invalid = 0
    failures = []
    for text, expected, args, kwargs in cases():
        try:
            original = text.format(*args, **kwargs)
        except (ValueError, KeyError, IndexError):
            invalid += 1
            continue
        total += 1
        try:
            actual = infer(text)
            if actual != expected:
                raise AssertionError('rewrite: ' + repr(actual) + ' != ' + repr(expected))
            if actual.format(*args, **kwargs) != original:
                raise AssertionError('format result changed')
            if tokenize is not None:
                # The public parser gives authoritative top-level field names.
                from string import Formatter
                names = [field for _, field, _, _ in Formatter().parse(expected)
                         if field is not None]
                actual_names = [part.fname for part in tokenize(text)
                                if not isinstance(part, str)]
                if actual_names != names:
                    raise AssertionError('field names: ' + repr(actual_names) + ' != ' + repr(names))
        except Exception as exc:
            failures.append({'input': text, 'expected': expected,
                             'error': type(exc).__name__ + ': ' + str(exc)})
    print(json.dumps({'label': label, 'valid_cases': total,
                      'invalid_builtin_cases': invalid,
                      'failure_count': len(failures),
                      'first_failures': failures[:12]}, ensure_ascii=True))
    return total, failures
