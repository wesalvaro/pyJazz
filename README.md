# pyJazz

pyJazz is a Python port of the amazing JavaScript testing framework [Jasmine](https://jasmine.github.io/).

```py
from jazz import *

class MyArithmetic(Describe):
  def it_should_add_2_and_2(self):
    expect(2 + 2).toEqual(4)
```

[![Build Status](https://travis-ci.org/wesalvaro/pyJazz.png?branch=master)](https://travis-ci.org/wesalvaro/pyJazz)

## Usage

Usage should be identical to Jasmine, but in Python. If it doesn't, it should. =D Everything from multiple `before|afterEach`, nested `Describe`s, `XDescribe` and `DDescribe`, `xit` and `iit`, to the matchers.

Test suites are collected in the module and executed when `run()` is called.
Matchers are stored in the module and can be used separately from the test runner.
Spec and matcher naming is fairly flexible, allowing for both camelCase and pep_8 syntax (e.g. `toEqual`, `to_equal`, `it_should_work`, `itShouldWork`).
The test methods may be named with an `it` prefix or wrapped with the `@it` function decorator.
However, these two methods should not be mixed (consistency!).

## Matchers

To use a matcher, create an expectation `expect(actual)` and then call one of the installed matchers with a `to` or `notTo` prefix. Matchers can also be called with camel case or pep8 `_` style (e.g. `toBeLessThan` or `not_to_be_none`).

### Built-in

#### Anything
 - be
 - be close to
 - be falsy
 - be greater than
 - be instance of
 - be less than
 - be none
 - be truthy
 - equal
 - match

#### Callables
 - raise

#### Mocks
 - have been called with
 - have been called

#### Iterables
 - contain
 - have length

### Custom Matchers

You can add your own matchers in a couple different ways.

```py
def BeFoo(a): return True
def be_bar(a): return True

# Add functions one at a time (name is inferred from function):
jazz.add_matcher(BeFoo)
jazz.add_matcher(be_bar)

# You can also add multiple matchers via a dict or list:
matchers = {
  'be a cat': lambda x: instanceof(x, Cat),
  'duck': lambda x: x.quack(),
}

jazz.add_matchers(matchers)
jazz.add_matchers([BeFoo, be_bar])

# Matcher names are normalized:
expect(goose).notToDuck()
expect(calico).toBeACat()
expect(baz).notToBeBar()
expect(foo).to_be_foo()
```
