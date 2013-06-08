"""A hacky demo of how you can use pyJazz."""


class Subject:

  def add(self, x, y):
    return x + y

  def just_run(self):
    raise Exception()

  def callback(self, fn):
    fn(42, foo='bar')
