"""Tests for pyJazz."""

import cStringIO
import jazz
import mock
import sys
import unittest

def the_spanish_inquisition():
  """Because one should always expect it."""
  return 42


class SuiteRunnerTest(unittest.TestCase):

  def setUp(self):
    reload(jazz)
    self.stdout_bak = sys.stdout
    sys.stdout = cStringIO.StringIO()
    jazz.VERBOSITY = 9

  def tearDown(self):
    sys.stdout = self.stdout_bak

  @property
  def output(self):
    return sys.stdout.getvalue()

  def test_unasserted_expectations_are_bad(self):

    class TheTestClass(jazz.Describe):

      def it_should_hate_this(self):
        jazz.expect(the_spanish_inquisition())

    self.assertRaisesRegexp(SystemExit, '1', jazz.run)
    out = self.output
    self.assertIn('The Test Class should hate this.', out)
    self.assertIn('UnassertedExpectation(', out)


  def test_xcluded_tests_do_not_run(self):
    it_ran = []

    class TheTestClass(jazz.Describe):

      def it_should_run_this(self):
        it_ran.append(1)

      def xit_should_not_run_this(self):
        it_ran.append(2)

    jazz.run()
    self.assertEqual([1], it_ran)

  def test_solo_tests_only_run(self):
    it_ran = []

    class TheTestClass(jazz.Describe):

      def iit_should_run_this(self):
        it_ran.append(1)

      def it_should_not_run_this(self):
        it_ran.append(2)

    jazz.run()
    self.assertEqual([1], it_ran)

  def test_nested_suites_run(self):
    it_ran = []

    class TheTestClass(jazz.Describe):

      class SubTestClass(jazz.Describe):

        def it_should_run_this(self):
          it_ran.append(2)

      def it_should_run_this(self):
        it_ran.append(1)

    jazz.run()
    self.assertEqual([1, 2], it_ran)

  def test_nested_suites_with_same_name(self):
    it_ran = []

    class TheTestClass(jazz.Describe):

      class TheTestClass(jazz.Describe):

        def it_should_run_this_too(self):
          it_ran.append(2)

      def it_should_run_this(self):
        it_ran.append(1)

    
    jazz.run()
    out = self.output
    self.assertIn('The Test Class should run this.', out)
    self.assertIn('The Test Class > The Test Class should run this too.', out)
    self.assertListEqual([1, 2], it_ran)

  def test_nested_suite_in_x_does_not_run(self):
    it_ran = []

    class ExcludedTest(jazz.xDescribe):

      class NestedNormalTest(jazz.Describe):

        def it_should_not_run_this(self):
          it_ran.append(2)

      class NestedSoloTest(jazz.DDescribe):

        def it_should_run_this(self):
          it_ran.append(3)

      def it_should_not_run_this(self):
        it_ran.append(1)

    jazz.run()
    self.assertEqual([3], it_ran)

  def test_before_eaches_run(self):
    it_ran = []

    class TheTestClass(jazz.Describe):

      def before_each(self):
        it_ran.append(1)

      class SubTestClass(jazz.Describe):

        def before_each(self):
          it_ran.append(2)

        def it_one(self): pass

        def it_two(self): pass

      def it_one(self): pass

      def it_two(self): pass

    jazz.run()
    expected = [1, 1, 1, 2, 1, 2]
    self.assertEqual(expected, it_ran)

  def test_after_eaches_run(self):
    it_ran = []

    class TheTestClass(jazz.Describe):

      def after_each(self):
        it_ran.append(1)

      class SubTestClass(jazz.Describe):

        def after_each(self):
          it_ran.append(2)

        def it_one(self): pass

        def it_two(self): pass

      def it_one(self): pass

      def it_two(self): pass

    jazz.run()
    expected = [1, 1, 1, 2, 1, 2]
    self.assertEqual(expected, it_ran)


class CustomMatchersTest(unittest.TestCase):

  def setUp(self):
    reload(jazz)

  def test_add_matcher(self):

    def BeFoo(a): return True

    def be_bar(a): return True

    jazz.add_matcher(BeFoo)
    jazz.add_matcher(be_bar)

    jazz.expect(jazz).toBeFoo()
    jazz.expect(jazz).toBeBar()

  def test_add_matchers(self):

    def BeFoo(a): return True

    def be_bar(a): return True

    matchers = {'be baz': lambda x: True}

    jazz.add_matchers(matchers)
    jazz.add_matchers([BeFoo, be_bar])

    jazz.expect(jazz).toBeFoo()
    jazz.expect(jazz).toBeBar()
    jazz.expect(jazz).toBeBaz()

  def test_custom_matcher(self):

    def BeOneMoreThan(a, e):
      return e + 1 == a
    jazz.add_matcher(BeOneMoreThan)
    a = 4
    e = 3

    jazz.expect(a).toBeOneMoreThan(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToBeOneMoreThan(e)


class SpyTest(unittest.TestCase):

  def test_spy_records(self):
    spy = jazz.create_spy('foo')
    spy(123)
    jazz.expect(spy).to_have_been_called_with(123)

  def test_spy_has_no_attributes(self):
    spy = jazz.create_spy('foo')
    with self.assertRaises(AttributeError):
      spy.foo()

  def test_spy_cannot_be_chained(self):
    spy = jazz.create_spy('foo')
    with self.assertRaises(AttributeError):
      spy().foo()

  def test_spy_obj_records(self):
    spy = jazz.create_spy_obj('foo', ['baz', 'cat'])
    spy.baz(456)
    jazz.expect(spy.baz).to_have_been_called_with(456)

  def test_spy_obj_methods_are_restricted(self):
    spy = jazz.create_spy_obj('foo', ['baz'])
    with self.assertRaises(AttributeError):
      spy.bar()

  def test_spy_obj_methods_cannot_be_chained(self):
    spy = jazz.create_spy_obj('foo', ['baz'])
    with self.assertRaises(AttributeError):
      spy.baz().bar()


class ExpectationTest(unittest.TestCase):

  def test_stringification(self):
    string = str(jazz.expect(the_spanish_inquisition()))

    self.assertIn('expect(42)', string)
    self.assertRegexpMatches(string, r'jazz_test.py:\d+')
    self.assertIn(
        'test_stringification:string = ' +
        'str(jazz.expect(the_spanish_inquisition()))', string)

  def test_matchers_can_be_chained(self):
    (jazz.expect(3)
      .toBe(3)
      .notToBeLessThan(3)
      .andNotToBeGreaterThan(3)
      .toBe(3)
      .andNotToBe(4)
      .notToBe(2)
      .andNotToBe(5))

  def test_extra_args(self):

    def BeXMoreThan(a, e, x):
      return e + x == a
    jazz.add_matcher(BeXMoreThan)
    a = 5
    e = 3
    x = 5 - 3

    jazz.expect(a).toBeXMoreThan(e, x)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToBeXMoreThan(e, x)

  def test_expectation_pep8(self):
    jazz.expect(True).toBeTruthy()
    jazz.expect(True).to_be_truthy()
    with self.assertRaises(AssertionError):
      jazz.expect(True).notToBeTruthy()
    with self.assertRaises(AssertionError):
      jazz.expect(True).not_to_be_truthy()

  def test_expectation_be(self):
    a = {}
    e = a

    jazz.expect(a).toBe(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToBe(e)

  def test_expectation_be_close_to(self):
    import math
    a = math.pi
    e = 3.1415

    jazz.expect(a).toBeCloseTo(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToBeCloseTo(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).toBeCloseTo(e, 8)

  def test_expectation_be_falsy(self):
    a = []

    jazz.expect(a).toBeFalsy()
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToBeFalsy()

  def test_expectation_be_greater_than(self):
    a = 3
    e = 2

    jazz.expect(a).toBeGreaterThan(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToBeGreaterThan(e)

  def test_expectation_be_instance_of(self):
    a = 3
    e = int

    jazz.expect(a).toBeInstanceOf(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToBeInstanceOf(e)

  def test_expectation_be_less_than(self):
    a = 2
    e = 3

    jazz.expect(a).toBeLessThan(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToBeLessThan(e)

  def test_expectation_be_none(self):
    a = None

    jazz.expect(a).toBeNone()
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToBeNone()

  def test_expectation_be_truthy(self):
    a = 'truthy string is truthy'

    jazz.expect(a).toBeTruthy()
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToBeTruthy()

  def test_expectation_contain(self):
    a = ['key']
    e = 'key'

    jazz.expect(a).toContain(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToContain(e)

  def test_expectation_equal(self):
    a = 4
    e = 4

    jazz.expect(a).toEqual(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToEqual(e)

  def test_expectation_match(self):
    a = 'some string here matches'
    e = r'.*matches'

    jazz.expect(a).toMatch(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToMatch(e)

  def test_expectation_raise(self):

    def a(): raise ValueError()
    e = ValueError

    jazz.expect(a).toRaise(e)
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToRaise(e)

    def a(): raise
    jazz.expect(a).toRaise()
    with self.assertRaises(AssertionError):
      jazz.expect(a).notToRaise()

  def test_expectation_been_called(self):
    m = mock.Mock()
    jazz.expect(m).notToHaveBeenCalled()
    m()
    jazz.expect(m).toHaveBeenCalled()

  def test_expectation_been_called_with(self):
    m = mock.Mock()
    m(123, bar=45)
    jazz.expect(m).toHaveBeenCalledWith(123, bar=45)

  def test_expectation_have_length(self):
    jazz.expect([1]).toHaveLength(1)
    with self.assertRaises(AssertionError):
      jazz.expect([1, 2]).toHaveLength(3)


if __name__ == '__main__':
  unittest.main()

