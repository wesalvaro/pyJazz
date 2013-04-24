import inspect
import re
import types


def add_matchers(matchers):
  if isinstance(matchers, list):
    for matcher in matchers:
      if not callable(matcher):
        raise ValueError('Argument was not callable.')
      name = _get_matcher_name(matcher.__name__).lstrip('to ')
      _matchers[name] = matcher
  elif isinstance(matchers, dict):
    _matchers.update(matchers)
  elif callable(matchers):
    add_matchers([matchers])
  else:
    raise ValueError('Argument was was not a list, dict, or callable.')
addMatcher = addMatchers = add_matcher = add_matchers


def expect(actual):
  return _Expectation(actual)


def _raise(actual, expected=Exception):
  try:
    actual()
  except Exception as e:
    return isinstance(e, expected)
  else:
    return False


_matchers = {
  'be': lambda a, e:
    a is e,
  'be close to': lambda a, e, p=2:
    abs(e - a) < (pow(10, -p) / 2),
  'be falsy': lambda a:
    not a,
  'be greater than': lambda a, e:
    a > e,
  'be instance of': lambda a, e:
    isinstance(a, e),
  'be less than': lambda a, e:
    a < e,
  'be none': lambda a:
    a is None,
  'be truthy': lambda a:
    a,
  'contain': lambda a, e:
    e in a,
  'equal': lambda a, e:
    a == e,
  'match': lambda a, e:
    re.match(e, a),
  'raise': _raise,
}


def _get_name(value):
  if callable(value) or isinstance(value, types.ModuleType):
    name = getattr(value, '__name__', None)
    name = name or getattr(value, '__class__', name)
    name = getattr(name, '__name__', name)
  else:
    name = str(value)
  return name


def _get_matcher_name(name):
  return re.sub(r'([A-Z])', r' \1', name).lower().replace('_', ' ').strip()


class _Expectation(object):
  MATCHER_PATTERN = re.compile(r'^(not)?_?(t|T)o_?(\w+)$')

  def __init__(self, actual):
    self.actual = actual

  def __getattr__(self, key):
    match = re.match(self.MATCHER_PATTERN, key)
    if not match:
      raise AttributeError('Bad Matcher pattern')
    negate, _, matcher_name = match.groups()
    matcher_name = _get_matcher_name(matcher_name)
    matcher = _matchers.get(matcher_name)
    if not matcher:
      raise NotImplementedError(
          'No matcher found by the name "%s".' % matcher_name)

    def match(*args, **kwargs):
      result = matcher(self.actual, *args, **kwargs)
      expected = args[0] if args else None
      names = (_get_name(self.actual), matcher_name, _get_name(expected))
      if negate:
        msg = 'Expected %s not to %s %s.' % names
        assert not result, msg
      else:
        msg = 'Expected %s to %s %s.' % names
        assert result, msg
    return match
