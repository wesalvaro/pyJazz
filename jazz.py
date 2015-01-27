"""pyJazz: A Python interpretation of the Jasmine testing framework."""

import optparse
import collections
import itertools
import mock
import re
import sys
import time
import traceback
import types
from os import path


def _ParseOptions():
  parser = optparse.OptionParser()
  parser.add_option('-r', '--runs', help='Repeat the tests RUNS times.',
                    type='int', default=1, dest='runs')
  parser.add_option('-v', '--verbosity', help='Set the verbosity level.',
                    default=3, dest='verbosity')
  parser.add_option('-q', '--quiet', help='No output. Return value only.',
                    action='store_const', const=0, dest='verbosity')
  parser.add_option('--noisy', help='As much output as possible.',
                    action='store_const', const=9, dest='verbosity')
  parser.add_option('--hide-stack', help='Hide stack traces.',
                    action='store_false', dest='show_stack', default=True)
  parser.add_option('--full-paths', help='Show full stack trace file paths.',
                    action='store_false', dest='show_basename', default=True)
  options, _ = parser.parse_args()
  return options

OPTIONS = _ParseOptions()

OUTPUT_BASENAME_ONLY = OPTIONS.show_basename
OUTPUT_STACKTRACE = OPTIONS.show_stack
VERBOSITY = OPTIONS.verbosity
RUNS = OPTIONS.runs

_SUITES = []
_SOLO_MODE = False
_DECORATOR_MODE = False


def run():
  """Invokes the Jazz Suite Runner.

  This runs your tests.
  """
  suite_runner = _SuiteRunner(_SUITES)
  total_failures = 0
  total_spec_count = 0
  total_elapsed = 0
  runs_failing = 0
  for _ in xrange(RUNS):
    failures, spec_count, elapsed = suite_runner.run()
    runs_failing += 1 if failures else 0
    total_failures += failures
    total_spec_count += spec_count
    total_elapsed += elapsed
  if RUNS > 1:
    if runs_failing:
      print '==== %d/%d RUNS FAILED ==== %d/%d total test failures.' % (
          runs_failing, RUNS, total_failures, total_spec_count)
    else:
      print '==== ALL %d RUNS PASSED ==== %s tests passed in %.3fs' % (
          RUNS, total_spec_count, total_elapsed)
    
  if total_failures:
    sys.exit(total_failures)


def _enable_solo_mode():
  """Enables solo mode for the suite runner."""
  global _SOLO_MODE
  _SOLO_MODE = True


def _enable_decorator_mode():
  """Enables the decorator mode flag to warn about mixing."""
  global _DECORATOR_MODE
  _DECORATOR_MODE = True


def _check_decorator_mode():
  if _DECORATOR_MODE:
    print 'Warning: Mixing @it spec decorator with `it_` spec function naming.'


class _DescribeMeta(type):
  """The metaclass for a suite.

  This looks at the class attributes and picks out specs,
  setup+teardown functions, and sub-suites. It then adds the suite to the
  global list of suites.
  """

  def __new__(mcs, name, bases, attrs):
    """Creates and sets up a new Jazz suite."""
    specs = []
    suites = []
    for attr_name, attr_val in attrs.iteritems():
      if attr_name.startswith('it'):
        _check_decorator_mode()
        attr_val.solo = False
        specs.append(attr_val)
      elif attr_name.startswith('iit'):
        _check_decorator_mode()
        attr_val.solo = True
        _enable_solo_mode()
        specs.append(attr_val)
      elif hasattr(attr_val, 'spec'):
        specs.append(attr_val)
      elif hasattr(attr_val, 'suite'):
        suites.append(attr_val)
        attr_val.top = False
    attrs.update({'suites': suites, 'specs': specs})
    suite = super(_DescribeMeta, mcs).__new__(mcs, name, bases, attrs)
    if suite.__module__.rpartition('.')[2] != 'jazz':
      _SUITES.append(suite)
      if suite.solo:
        _enable_solo_mode()
    return suite

class Describe(object):
  """The base class for a regular Jazz suite."""
  __metaclass__ = _DescribeMeta
  top = True
  suite = True
  solo = False
  excluded = False

class DDescribe(Describe):
  """The base class for a solo Jazz suite.

  Solo suites will run all of their internal specs, but specs outside of solo
  suites will not be run.
  """
  solo = True
dDescribe = DDescribe

class XDescribe(Describe):
  """The base class for an excluded Jazz suite.

  An excluded Jazz suite will not have its specs run unless they are marked as
  solo specs.
  """
  excluded = True
xDescribe = XDescribe


def it(fn):
  """A decorator for creating a regular Jazz spec.

  Args:
    fn: A function to setup as a spec.
  """
  fn.spec = True
  fn.solo = False
  _enable_decorator_mode()
  return fn

def iit(fn):
  """A decorator for creating a solo Jazz spec.

  Solo specs will always be run, however specs outside of a solo spec will not.

  Args:
    fn: A function to setup as a solo spec.
  """
  fn.spec = True
  fn.solo = True
  _enable_solo_mode()
  _enable_decorator_mode()
  return fn

def xit(fn):
  """A decorator for creating an excluded Jazz spec.

  Excluded specs will not run.

  Args:
    fn: A function to setup as an excluded spec.
  """
  _enable_decorator_mode()
  return fn

def add_matchers(matchers):
  """Adds one or more matchers to the global set of matchers.

  Unlike Jasmine, matchers in Jazz need only be added once per test binary.
  TODO(wesalvaro): This may be revised in the future.

  Args:
    matchers: One of (list of functions, function, or dict of functions).
      If a function or a list of functions, the function names will be used as
      the matcher names. If a dict of functions, the keys will be used as the
      names for the respective values function matchers.
  """
  if isinstance(matchers, list):
    for matcher in matchers:
      if not callable(matcher):
        raise ValueError('Argument was not callable.')
      name = _get_matcher_name(matcher.__name__).lstrip('to ')
      _MATCHERS[name] = matcher
  elif isinstance(matchers, dict):
    _MATCHERS.update(matchers)
  elif callable(matchers):
    add_matchers([matchers])
  else:
    raise ValueError('Argument was was not a list, dict, or callable.')
addMatcher = addMatchers = add_matcher = add_matchers


def expect(actual):
  """Creates an expectation object for testing an actual value.

  Args:
    actual: The actual value to test against an expected value with a matcher.
  Returns:
    An expectation object. Its methods are matchers to check the value.
  """
  return _Expectation(actual)


def __callable(*args, **kwargs): pass


def create_spy(name):
  return mock.Mock(spec=__callable, name=name)


def create_spy_obj(name, methods):
  t = collections.namedtuple(name, methods)
  s = t(*(__callable,) * len(methods))
  return mock.Mock(spec=s, name=name)


def _raise(actual, expected=Exception):
  """Helps test a function raising an exception.

  Args:
    actual: Callable that is suspected to raise.
    expected: Exception type that is suspect.
  Returns:
    True if the expected exception was raised; False otherwise.
  """
  try:
    actual()
  except Exception as e:
    return isinstance(e, expected)
  else:
    return False


def _have_been_called_with(actual, *args, **kwargs):
  try:
    actual.assert_any_call(*args, **kwargs)
  except AssertionError:
    return False
  return True


_MATCHERS = {
  'be': lambda a, e:
    a is e,
  'be close to': lambda a, e, p=2:
    abs(e - a) < (pow(10, -p) / 2),
  'be falsy': lambda a:
    not a,
  'be greater than': lambda a, e:
    a > e,
  'be instance of': isinstance,
  'be less than': lambda a, e:
    a < e,
  'be none': lambda a:
    a is None,
  'be truthy': lambda a:
    a,
  'equal': lambda a, e:
    a == e,
  'match': lambda a, e:
    re.match(e, a),
  # Callable
  'raise': _raise,
  # Mock
  'have been called with': _have_been_called_with,
  'have been called': lambda a:
    a.call_count > 0,
  # Iterables
  'contain': lambda a, e:
    e in a,
  'have length': lambda a, e:
    len(list(a)) == e,
}


def _convert_name(name):
  """Creates a pretty name for suites and specs."""
  name = name.replace('_', ' ')
  name = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
  name = re.sub('([a-z0-9])([A-Z])', r'\1 \2', name)
  return name.lstrip('it ').lstrip('iit ').strip()


def _get_name(value):
  """Takes some value and tries to get a pretty name for it.

  Example:
    The module object for jazz.py should output 'jazz'.

  Args:
    value: Any value or type.
  Returns:
    A string. The string should be a pretty name for the value.
  """
  if callable(value) or isinstance(value, types.ModuleType):
    name = getattr(value, '__name__', None)
    name = name or getattr(value, '__class__', name)
    name = getattr(name, '__name__', name)
  else:
    name = str(value)
  return name


def _get_matcher_name(name):
  """Converts a function name to a string key for a matcher."""
  return re.sub(r'([A-Z])', r' \1', name).lower().replace('_', ' ').strip()


class _Expectation(object):
  """The expectation object for an actual value."""
  MATCHER_PATTERN = re.compile(r'^(not)?_?(t|T)o_?(\w+)$')

  def __init__(self, actual):
    """Stores the actual value for multiple assertions."""
    self.actual = actual

  def __getattr__(self, key):
    """Gets a matcher by its name by parsing the attribute requested.

    Example:
      expect(foo).notToBeGreaterThan would yield a callable that is posed to
      check the negative match of matchers['be greater than'] against foo.

    Args:
      key: The matcher setup requested.
    Returns:
      A function, the matcher setup for assertion.
    """
    match = re.match(self.MATCHER_PATTERN, key)
    if not match:
      raise AttributeError('Bad Matcher pattern')
    negate, _, matcher_name = match.groups()
    matcher_name = _get_matcher_name(matcher_name)
    matcher = _MATCHERS.get(matcher_name)
    if not matcher:
      raise NotImplementedError(
          'No matcher found by the name "%s".' % matcher_name)

    def attr(*args, **kwargs):
      """Sets up the matcher to be asserted with a requested matcher.

      Args:
        *args: Any arguments to the matcher.
        **kwargs: Any keyword arguments to the matcher.
      """
      result = matcher(self.actual, *args, **kwargs)
      expected = args[0] if args else None
      names = (_get_name(self.actual), matcher_name, _get_name(expected))
      if negate:
        msg = 'Expected %s not to %s %s.' % names
        assert not result, msg
      else:
        msg = 'Expected %s to %s %s.' % names
        assert result, msg
    return attr


class _Cause(object):
  """Records the cause of an exception, if currently under inspection."""
  TEST_FILE = __name__ + '.py'

  def __init__(self):
    """Grabs the exception and filtered traceback if available."""
    self.exc_type, self.exc_val, trace = sys.exc_info()
    sys.exc_clear()
    if trace:
      self.error = True
      extracted_tb = traceback.extract_tb(trace)

      self.trace = itertools.ifilterfalse(
          lambda x: x[0].endswith(self.TEST_FILE), extracted_tb)
    else:
      self.error = False
      self.trace = None

  def __str__(self):
    """Nicely outputs the cause for humans."""
    if not self.trace:
      return ''
    result = '\n     %s(%s)' % (self.exc_type.__name__, self.exc_val)
    if OUTPUT_STACKTRACE:
      for frame in self.trace:
        frame = list(frame)
        if OUTPUT_BASENAME_ONLY:
          frame[0] = path.basename(frame[0])
        result += '\n  %s:%d in %s\n    %s' % tuple(frame)
    return result


class _Result(object):
  """The result of a spec."""

  def __init__(self, suite, spec, parents=None):
    """Saves the execution state for printing."""
    self.suite, self.spec, self.parents = suite, spec, parents
    self.cause = _Cause()

  def __str__(self):
    """Nicely outputs the result for humans."""
    if self.parents:
      parents = '%s > ' % ' > '.join(
          map(_convert_name, map(lambda x: x.__name__, self.parents)))
    else:
      parents = ''
    status = '!!' if self.cause.error else 'OK'
    return '[%s] %s%s %s.%s' % (
        status, parents, _convert_name(self.suite.__name__),
        _convert_name(self.spec.__name__).lower(), self.cause)


class _SuiteRunner(object):
  """Runs a set of Jazz suites."""

  def __init__(self, suites):
    """Sets up the runner.

    Args:
      suites: A list of suites to run.
    """
    self.suites = suites

  def _run_one(self, suite, parents=None, excluded=False,
               before_each=None, after_each=None, solo=False):
    """Runs a single suite.

    This suite may be a nested suite.
    This method is recursive for nested suites.

    Args:
      suite: The suite to run.
      parents: A genealogy list of encapsulating suites.
      before_each: A list of setup functions to run.
      after_each: A list of tear down functions to run.
      solo: True if this suite is part of a solo suite.
    """
    before_each = before_each or []
    after_each = after_each or []
    parents = parents or []
    test = suite()
    if hasattr(test, 'before_each'):
      before_each.append(test.before_each)
    if hasattr(test, 'after_each'):
      after_each.append(test.after_each)

    solo = solo or suite.solo
    excluded = (excluded or suite.excluded) and not solo
    for spec in test.specs:
      if excluded:
        continue
      if _SOLO_MODE and not (solo or spec.solo):
        continue
      map(lambda x: x(), before_each)
      try:
        spec(test)
      except Exception:
        self.failures += 1
      self.spec_count += 1
      map(lambda x: x(), after_each)
      result = _Result(suite, spec, parents=parents)
      if result.cause.error or VERBOSITY > 2:
        print result
      elif VERBOSITY > 1:
        print '.',

    parents.append(suite)
    for sub_suite in test.suites:
      self._run_one(sub_suite, parents=parents, before_each=before_each,
                   after_each=after_each, solo=solo, excluded=excluded)
    if hasattr(test, 'before_each'):
      before_each.pop()
    if hasattr(test, 'after_each'):
      after_each.pop()
    parents.pop()

  def run(self):
    """Runs and times the suites, printing the results."""
    self.failures = 0
    self.spec_count = 0
    self.results = []
    start = time.time()
    sys.exc_clear()
    map(self._run_one, itertools.ifilter(lambda x: x.top, self.suites))
    elapsed = time.time() - start
    if self.failures:
      print '==== FAILED ==== %d/%d tests failed.' % (
          self.failures, self.spec_count)
    elif VERBOSITY > 0:
      print '==== PASSED ==== %s tests passed in %.3fs' % (
          self.spec_count, elapsed)
    return self.failures, self.spec_count, elapsed
