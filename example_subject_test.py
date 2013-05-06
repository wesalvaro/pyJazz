"""A hacky demo of how you can use pyJazz."""

from jazz import *
from example_subject import Subject


class Adder(Describe):

  def before_each(self):
    self.subject = Subject()

  @it
  def ShouldAddTwoNumbers(self):
    actual = self.subject.add(2, 3)
    expect(actual).toEqual(5)

  @it
  def ShouldAtLeastAddSomething(self):
    actual = self.subject.add(2, 3)
    expect(actual).toBeGreaterThan(2)

  class Sub(Describe):

    def before_each(self):
      self.subject = Subject()

    @it
    def ShouldBeASubTest(self):
      actual = self.subject.add(2, 3)
      expect(actual).toBeLessThan(6)

    class SubSub(Describe):
      def it_should_keep_nesting(self): pass

  @it
  def ShouldJustRun(self):
    expect(self.subject.just_run).toRaise()


class AdderPep8(Describe):

  def it_should_add_two_numbers(self):
    subject = Subject()
    expect(subject.add(2, 3)).toEqual(5)

  def it_should_at_least_add_something(self):
    subject = Subject()
    expect(subject.add(2, 3)).toBeGreaterThan(2)

  def it_should_just_run(self):
    subject = Subject()
    expect(subject.just_run).toRaise()


if __name__ == '__main__':
  run()

