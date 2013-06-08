"""Tests for pyJazz."""

import collections
import jazz
import unittest

Mock = collections.namedtuple('Mock', ['call_count', 'assert_any_call'])


class SuiteRunnerTest(unittest.TestCase):

  def setUp(self):
    reload(jazz)
    jazz.VERBOSITY = 0

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
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToBeOneMoreThan(e))


class ExpectationTest(unittest.TestCase):

  def test_extra_args(self):

    def BeXMoreThan(a, e, x):
      return e + x == a
    jazz.add_matcher(BeXMoreThan)
    a = 5
    e = 3
    x = 5 - 3

    jazz.expect(a).toBeXMoreThan(e, x)
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToBeXMoreThan(e, x))

  def test_expectation_pep8(self):
    jazz.expect(True).toBeTruthy()
    jazz.expect(True).to_be_truthy()
    self.assertRaises(
      AssertionError, lambda: jazz.expect(True).notToBeTruthy())
    self.assertRaises(
      AssertionError, lambda: jazz.expect(True).not_to_be_truthy())

  def test_expectation_be(self):
    a = {}
    e = a

    jazz.expect(a).toBe(e)
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToBe(e))

  def test_expectation_be_close_to(self):
    import math
    a = math.pi
    e = 3.1415

    jazz.expect(a).toBeCloseTo(e)
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToBeCloseTo(e))
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).toBeCloseTo(e, 8))

  def test_expectation_be_falsy(self):
    a = []

    jazz.expect(a).toBeFalsy()
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToBeFalsy())

  def test_expectation_be_greater_than(self):
    a = 3
    e = 2

    jazz.expect(a).toBeGreaterThan(e)
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToBeGreaterThan(e))

  def test_expectation_be_instance_of(self):
    a = 3
    e = int

    jazz.expect(a).toBeInstanceOf(e)
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToBeInstanceOf(e))

  def test_expectation_be_less_than(self):
    a = 2
    e = 3

    jazz.expect(a).toBeLessThan(e)
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToBeLessThan(e))

  def test_expectation_be_none(self):
    a = None

    jazz.expect(a).toBeNone()
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToBeNone())

  def test_expectation_be_truthy(self):
    a = 'truthy string is truthy'

    jazz.expect(a).toBeTruthy()
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToBeTruthy())

  def test_expectation_contain(self):
    a = ['key']
    e = 'key'

    jazz.expect(a).toContain(e)
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToContain(e))

  def test_expectation_equal(self):
    a = 4
    e = 4

    jazz.expect(a).toEqual(e)
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToEqual(e))

  def test_expectation_match(self):
    a = 'some string here matches'
    e = r'.*matches'

    jazz.expect(a).toMatch(e)
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToMatch(e))

  def test_expectation_raise(self):

    def a(): raise ValueError()
    e = ValueError

    jazz.expect(a).toRaise(e)
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToRaise(e))

    def a(): raise
    jazz.expect(a).toRaise()
    self.assertRaises(
      AssertionError, lambda: jazz.expect(a).notToRaise())

  def test_expectation_been_called(self):
    mock = Mock(0, None)
    jazz.expect(mock).notToHaveBeenCalled()
    mock = Mock(7, None)
    jazz.expect(mock).toHaveBeenCalled()

  def test_expectation_been_called_with(self):
    mock = Mock(None, lambda foo, bar: 42)
    jazz.expect(mock).toHaveBeenCalledWith(123, bar=45)


if __name__ == '__main__':
  unittest.main()

