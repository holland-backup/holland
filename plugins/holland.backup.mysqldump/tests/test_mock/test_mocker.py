import unittest
import tempfile
import inspect
import shutil
import sys
import os
import gc

from types import ModuleType

try:
    import coverage
except ImportError:
    coverage = None
else:
    # Start coverage check before importing from mocker, to get all of it.
    coverage.erase()
    coverage.start()

from holland.backup.mysqldump.mock.mocker import \
    MockerBase, Mocker, Mock, Event, Task, Action, Path, recorder, expect, \
    PathMatcher, path_matcher_recorder, RunCounter, ImplicitRunCounter, \
    run_counter_recorder, run_counter_removal_recorder, MockReturner, \
    mock_returner_recorder, FunctionRunner, Orderer, SpecChecker, \
    spec_checker_recorder, match_params, ANY, IS, CONTAINS, IN, MATCH, ARGS, \
    KWARGS, MatchError, PathExecuter, ProxyReplacer, Patcher, Undefined, \
    PatchedMethod, MockerTestCase, ReplayRestoreEvent, OnRestoreCaller


class TestCase(unittest.TestCase):
    """Python 2.3 lacked a couple of useful aliases."""
    
    assertTrue = unittest.TestCase.failUnless
    assertFalse = unittest.TestCase.failIf


class CleanMocker(MockerBase):
    """Just a better name for MockerBase in a testing context."""


class IntegrationTest(TestCase):

    def setUp(self):
        self.mocker = Mocker()

    def tearDown(self):
        self.mocker.restore()

    def test_count(self):
        obj = self.mocker.mock()
        obj.x
        self.mocker.count(2, 3)

        self.mocker.replay()
        obj.x
        self.assertRaises(AssertionError, self.mocker.verify)
        obj.x
        self.mocker.verify()
        obj.x
        self.mocker.verify()
        self.assertRaises(AssertionError, getattr, obj, "x")

    def test_order(self):
        obj = self.mocker.mock()

        with_manager = self.mocker.order()
        with_manager.__enter__()
        obj.x
        obj.y
        obj.z
        with_manager.__exit__(None, None, None)

        self.mocker.replay()
        self.assertRaises(AssertionError, getattr, obj, "y")
        self.assertRaises(AssertionError, getattr, obj, "z")

        self.mocker.replay()
        obj.x
        self.assertRaises(AssertionError, getattr, obj, "z")

        self.mocker.replay()
        obj.x
        obj.y
        obj.z

    def test_spec_and_type(self):
        class C(object):
            def m(self, a): pass
        
        obj = self.mocker.mock(C)

        obj.m(1)
        obj.m(a=1)
        obj.m(1, 2)
        obj.m(b=2)
        obj.x()
        obj.y()
        self.mocker.nospec()
        obj.z()

        self.mocker.replay()

        self.assertTrue(isinstance(obj, C))

        obj.m(1)
        obj.m(a=1)
        obj.y()
        self.assertRaises(AssertionError, obj.m, 1, 2)
        self.assertRaises(AssertionError, obj.m, b=2)
        self.assertRaises(AssertionError, obj.x)
        self.assertRaises(AssertionError, obj.z)

    def test_result(self):
        obj = self.mocker.mock()
        obj.x
        self.mocker.result(42)
        self.mocker.replay()
        self.assertEquals(obj.x, 42)

    def test_throw(self):
        obj = self.mocker.mock()
        obj.x()
        self.mocker.throw(ValueError)
        self.mocker.replay()
        self.assertRaises(ValueError, obj.x)

    def test_call(self):
        calls = []
        def func(arg):
            calls.append(arg)
            return 42
        obj = self.mocker.mock()
        obj.x(24)
        self.mocker.call(func)
        self.mocker.replay()
        self.assertEquals(obj.x(24), 42)
        self.assertEquals(calls, [24])

    def test_call_result(self):
        calls = []
        def func(arg):
            calls.append(arg)
            return arg
        obj = self.mocker.mock()
        obj.x(24)
        self.mocker.call(func)
        self.mocker.result(42)
        self.mocker.replay()
        self.assertEquals(obj.x(24), 42)
        self.assertEquals(calls, [24])

    def test_generate(self):
        obj = self.mocker.mock()
        obj.x(24)
        self.mocker.generate([1, 2, 3])
        self.mocker.replay()
        result = obj.x(24)
        def g(): yield None
        self.assertEquals(type(result), type(g()))
        self.assertEquals(list(result), [1, 2, 3])

    def test_proxy(self):
        class C(object):
            def sum(self, *args):
                return sum(args)
        
        obj = self.mocker.proxy(C())
        expect(obj.multiply(2, 3)).result(6).nospec()
        expect(obj.sum(0, 0)).result(1)
        expect(obj.sum(0, 0)).passthrough()

        self.mocker.replay()

        self.assertEquals(obj.multiply(2, 3), 6) # Mocked.
        self.assertRaises(AttributeError, obj.multiply) # Passed through.

        self.assertEquals(obj.sum(2, 3), 5) # Passed through.
        self.assertEquals(obj.sum(0, 0), 1) # Mocked.
        self.assertEquals(obj.sum(0, 0), 0) # Passed through explicitly.
        self.assertRaises(AssertionError, obj.sum, 0, 0) # Seen twice.

    def test_replace_install_and_restore(self):
        module = self.mocker.replace("calendar")
        import calendar
        self.assertTrue(calendar is not module)
        self.mocker.replay()
        import calendar
        self.assertTrue(calendar is module)
        self.mocker.restore()
        import calendar
        self.assertTrue(calendar is not module)

    def test_replace_os_path_join(self):
        path = self.mocker.replace("os.path")
        expect(path.join(ARGS)).call(lambda *args: "-".join(args))
        expect(path.join("e", ARGS)).passthrough()
        self.mocker.replay()
        import os
        self.assertEquals(os.path.join("a", "b", "c"), "a-b-c")
        self.assertNotEquals(os.path.join("e", "f", "g"), "e-f-g")

    def test_replace_os_path_isfile(self):
        path = self.mocker.replace("os.path")
        expect(path.isfile("unexistent")).result(True)
        expect(path.isfile(ANY)).passthrough().count(2)
        self.mocker.replay()
        import os
        self.assertFalse(os.path.isfile("another-unexistent"))
        self.assertTrue(os.path.isfile("unexistent"))
        self.assertFalse(os.path.isfile("unexistent"))

    def test_patch_with_spec(self):
        class C(object):
            def method(self, a, b):
                pass
        mock = self.mocker.patch(C)
        mock.method(1, 2)
        mock.method(1)
        self.mocker.replay()
        mock.method(1, 2)
        self.assertRaises(AssertionError, mock.method, 1)

    def test_patch_with_spec_and_unexistent(self):
        class C(object):
            pass
        mock = self.mocker.patch(C)
        mock.method(1, 2)
        self.mocker.count(0)
        self.mocker.replay()
        self.assertRaises(AssertionError, self.mocker.verify)

    def test_mock_iter(self):
        """
        list() uses len() as a hint. When we mock iter(), it shouldn't
        explode due to the lack of len().
        """
        mock = self.mocker.mock()
        iter(mock)
        self.mocker.result(iter([1, 2, 3]))
        self.mocker.replay()
        self.assertEquals(list(mock), [1, 2, 3])
        self.mocker.verify()

    def test_replace_builtin_function(self):
        """
        Inspection doesn't work on builtin functions, but proxying should
        work even then (without spec enforcement in these cases).
        """
        from zlib import adler32
        mock = self.mocker.proxy(adler32)
        mock()
        self.mocker.result(42)
        self.mocker.replay()
        self.assertEquals(mock(), 42)


class ExpectTest(TestCase):

    def setUp(self):
        self.mocker = CleanMocker()

    def test_calling_mocker(self):
        obj = self.mocker.mock()
        expect(obj.attr).result(123)
        self.mocker.replay()
        self.assertEquals(obj.attr, 123)

    def test_chaining(self):
        obj = self.mocker.mock()
        expect(obj.attr).result(123).result(42)
        self.mocker.replay()
        self.assertEquals(obj.attr, 42)


class MockerTestCaseTest(TestCase):

    def setUp(self):
        self.test = MockerTestCase("shortDescription")

    def tearDown(self):
        self.test.mocker.restore()
        # Run it so that any cleanups are performed.
        self.test.run()

    def test_has_mocker(self):
        self.assertEquals(type(self.test.mocker), Mocker)

    def test_has_expect(self):
        self.assertTrue(self.test.expect is expect)

    def test_attributes_are_the_same(self):
        class MyTest(MockerTestCase):
            def test_method(self):
                pass
            test_method.foo = "bar"
        test = MyTest("test_method")
        self.assertEquals(getattr(test.test_method, "im_class", None), MyTest)
        self.assertEquals(getattr(test.test_method, "foo", None), "bar")

    def test_constructor_is_the_same(self):
        self.assertEquals(inspect.getargspec(TestCase.__init__),
                          inspect.getargspec(MockerTestCase.__init__))

    def test_docstring_is_the_same(self):
        class MyTest(MockerTestCase):
            def test_method(self):
                """Hello there!"""
        self.assertEquals(MyTest("test_method").test_method.__doc__,
                          "Hello there!")

    def test_short_description_is_the_same(self):
        class MyTest(MockerTestCase):
            def test_method(self):
                """Hello there!"""
        class StandardTest(TestCase):
            def test_method(self):
                """Hello there!"""

        self.assertEquals(MyTest("test_method").shortDescription(),
                          StandardTest("test_method").shortDescription())

    def test_missing_method_raises_the_same_error(self):
        class MyTest(TestCase):
            pass

        try:
            MyTest("unexistent_method").run()
        except Exception, e:
            expected_error = e

        class MyTest(MockerTestCase):
            pass
        
        try:
            MyTest("unexistent_method").run()
        except Exception, e:
            self.assertEquals(str(e), str(expected_error))
            self.assertEquals(type(e), type(expected_error))

    def test_raises_runtime_error_if_not_in_replay_mode_with_events(self):
        class MyTest(MockerTestCase):
            def test_method(self):
                pass

        test = MyTest("test_method")

        # That's fine.
        test.test_method()

        test.mocker.add_event(Event())

        # That's not.
        self.assertRaises(RuntimeError, test.test_method)

        test.mocker.replay()

        # Fine again.
        test.test_method()

    def test_mocker_is_verified_and_restored_after_test_method_is_run(self):
        calls = []
        class MyEvent(Event):
            def verify(self):
                calls.append("verify")
            def restore(self):
                calls.append("restore")
        class MyTest(MockerTestCase):
            def test_method(self):
                self.mocker.add_event(MyEvent())
                self.mocker.replay()
            def test_method_raising(self):
                self.mocker.add_event(MyEvent())
                self.mocker.replay()
                raise AssertionError("BOOM!")

        result = unittest.TestResult()
        MyTest("test_method").run(result)

        self.assertEquals(calls, ["verify", "restore"])
        self.assertTrue(result.wasSuccessful())

        del calls[:]

        result = unittest.TestResult()
        MyTest("test_method_raising").run(result)

        self.assertEquals(calls, ["restore"])
        self.assertEquals(len(result.errors), 0)
        self.assertEquals(len(result.failures), 1)
        self.assertTrue("BOOM!" in result.failures[0][1])

    def test_expectation_failure_acts_appropriately(self):
        class MyTest(MockerTestCase):
            def test_method(self):
                mock = self.mocker.mock()
                mock.x
                self.mocker.replay()
        
        result = unittest.TestResult()
        MyTest("test_method").run(result)

        self.assertEquals(len(result.errors), 0)
        self.assertEquals(len(result.failures), 1)
        self.assertTrue("mock.x" in result.failures[0][1])

    def test_add_cleanup(self):
        stash = []
        def func(a, b):
            stash.append((a, b))

        class MyTest(MockerTestCase):
            def tearDown(self):
                self.addCleanup(func, 3, b=4)
            def test_method(self):
                self.addCleanup(func, 1, b=2)
                stash.append(stash[:])

        MyTest("test_method").run()

        self.assertEquals(stash, [[], (1, 2), (3, 4)])

    def test_twisted_trial_deferred_support(self):
        calls = []
        callbacks = []
        errbacks = []
        deferreds = []
        class Deferred(object):
            def addCallback(self, callback):
                callbacks.append(callback)
            def addErrback(self, errback):
                errbacks.append(errback)
        class MyEvent(Event):
            def verify(self):
                calls.append("verify")
            def restore(self):
                calls.append("restore")
        class MyTest(MockerTestCase):
            def test_method(self):
                self.mocker.add_event(MyEvent())
                self.mocker.replay()
                deferred = Deferred()
                deferreds.append(deferred)
                return deferred

        result = unittest.TestResult()
        test = MyTest("test_method")
        deferred = test.test_method()

        self.assertEquals(deferred, deferreds[-1])
        self.assertEquals(calls, [])
        self.assertEquals(len(callbacks), 1)
        self.assertEquals(callbacks[-1]("foo"), "foo")
        self.assertEquals(calls, ["verify"])


    def test_fail_unless_is_raises_on_mismatch(self):
        try:
            self.test.failUnlessIs([], [])
        except AssertionError, e:
            self.assertEquals(str(e), "[] is not []")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_is_uses_msg(self):
        try:
            self.test.failUnlessIs([], [], "oops!")
        except AssertionError, e:
            self.assertEquals(str(e), "oops!")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_is_succeeds(self):
        obj = []
        try:
            self.test.failUnlessIs(obj, obj)
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_if_is_raises_on_mismatch(self):
        obj = []
        try:
            self.test.failIfIs(obj, obj)
        except AssertionError, e:
            self.assertEquals(str(e), "[] is []")
        else:
            self.fail("AssertionError not raised")

    def test_fail_if_is_uses_msg(self):
        obj = []
        try:
            self.test.failIfIs(obj, obj, "oops!")
        except AssertionError, e:
            self.assertEquals(str(e), "oops!")
        else:
            self.fail("AssertionError not raised")

    def test_fail_if_is_succeeds(self):
        try:
            self.test.failIfIs([], [])
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_unless_in_raises_on_mismatch(self):
        try:
            self.test.failUnlessIn(1, [])
        except AssertionError, e:
            self.assertEquals(str(e), "1 not in []")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_in_uses_msg(self):
        try:
            self.test.failUnlessIn(1, [], "oops!")
        except AssertionError, e:
            self.assertEquals(str(e), "oops!")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_in_succeeds(self):
        try:
            self.test.failUnlessIn(1, [1])
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_if_in_raises_on_mismatch(self):
        try:
            self.test.failIfIn(1, [1])
        except AssertionError, e:
            self.assertEquals(str(e), "1 in [1]")
        else:
            self.fail("AssertionError not raised")

    def test_fail_if_in_uses_msg(self):
        try:
            self.test.failIfIn(1, [1], "oops!")
        except AssertionError, e:
            self.assertEquals(str(e), "oops!")
        else:
            self.fail("AssertionError not raised")

    def test_fail_if_in_succeeds(self):
        try:
            self.test.failIfIn(1, [])
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_unless_starts_with_raises_on_mismatch(self):
        try:
            self.test.failUnlessStartsWith("abc", "def")
        except AssertionError, e:
            self.assertEquals(str(e), "'abc' doesn't start with 'def'")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_starts_with_uses_msg(self):
        try:
            self.test.failUnlessStartsWith("abc", "def", "oops!")
        except AssertionError, e:
            self.assertEquals(str(e), "oops!")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_starts_with_succeeds(self):
        try:
            self.test.failUnlessStartsWith("abcdef", "abc")
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_unless_starts_with_works_with_non_strings(self):
        self.test.failUnlessStartsWith([1, 2, 3], [1, 2])
        self.assertRaises(AssertionError,
                          self.test.failUnlessStartsWith, [1, 2, 3], [4, 5, 6])

    def test_fail_if_starts_with_raises_on_mismatch(self):
        try:
            self.test.failIfStartsWith("abcdef", "abc")
        except AssertionError, e:
            self.assertEquals(str(e), "'abcdef' starts with 'abc'")
        else:
            self.fail("AssertionError not raised")

    def test_fail_if_starts_with_uses_msg(self):
        try:
            self.test.failIfStartsWith("abcdef", "abc", "oops!")
        except AssertionError, e:
            self.assertEquals(str(e), "oops!")
        else:
            self.fail("AssertionError not raised")

    def test_fail_if_starts_with_succeeds(self):
        try:
            self.test.failIfStartsWith("abc", "def")
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_if_starts_with_works_with_non_strings(self):
        self.test.failIfStartsWith([1, 2, 3], [4, 5, 6])
        self.assertRaises(AssertionError,
                          self.test.failIfStartsWith, [1, 2, 3], [1, 2])

    def test_fail_unless_ends_with_raises_on_mismatch(self):
        try:
            self.test.failUnlessEndsWith("abc", "def")
        except AssertionError, e:
            self.assertEquals(str(e), "'abc' doesn't end with 'def'")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_ends_with_uses_msg(self):
        try:
            self.test.failUnlessEndsWith("abc", "def", "oops!")
        except AssertionError, e:
            self.assertEquals(str(e), "oops!")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_ends_with_succeeds(self):
        try:
            self.test.failUnlessEndsWith("abcdef", "def")
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_unless_ends_with_works_with_non_strings(self):
        self.test.failUnlessEndsWith([1, 2, 3], [2, 3])
        self.assertRaises(AssertionError,
                          self.test.failUnlessEndsWith, [1, 2, 3], [4, 5, 6])

    def test_fail_if_ends_with_raises_on_mismatch(self):
        try:
            self.test.failIfEndsWith("abcdef", "def")
        except AssertionError, e:
            self.assertEquals(str(e), "'abcdef' ends with 'def'")
        else:
            self.fail("AssertionError not raised")

    def test_fail_if_ends_with_uses_msg(self):
        try:
            self.test.failIfEndsWith("abcdef", "def", "oops!")
        except AssertionError, e:
            self.assertEquals(str(e), "oops!")
        else:
            self.fail("AssertionError not raised")

    def test_fail_if_ends_with_succeeds(self):
        try:
            self.test.failIfEndsWith("abc", "def")
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_if_ends_with_works_with_non_strings(self):
        self.test.failIfEndsWith([1, 2, 3], [4, 5, 6])
        self.assertRaises(AssertionError,
                          self.test.failIfEndsWith, [1, 2, 3], [2, 3])

    def test_fail_unless_approximates_raises_on_mismatch(self):
        try:
            self.test.failUnlessApproximates(1, 2, 0.999)
        except AssertionError, e:
            self.assertEquals(str(e), "abs(1 - 2) > 0.999")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_approximates_uses_msg(self):
        try:
            self.test.failUnlessApproximates(1, 2, 0.999, "oops!")
        except AssertionError, e:
            self.assertEquals(str(e), "oops!")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_approximates_succeeds(self):
        try:
            self.test.failUnlessApproximates(1, 2, 1)
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_if_approximates_raises_on_mismatch(self):
        try:
            self.test.failIfApproximates(1, 2, 1)
        except AssertionError, e:
            self.assertEquals(str(e), "abs(1 - 2) <= 1")
        else:
            self.fail("AssertionError not raised")

    def test_fail_if_approximates_uses_msg(self):
        try:
            self.test.failIfApproximates(1, 2, 1, "oops!")
        except AssertionError, e:
            self.assertEquals(str(e), "oops!")
        else:
            self.fail("AssertionError not raised")

    def test_fail_if_approximates_succeeds(self):
        try:
            self.test.failIfApproximates(1, 2, 0.999)
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_unless_methods_match_raises_on_different_method(self):
        class Fake(object):
            def method(self, a): pass
        class Real(object):
            def method(self, b): pass
        try:
            self.test.failUnlessMethodsMatch(Fake, Real)
        except AssertionError, e:
            self.assertEquals(str(e), "Fake.method(self, a) != "
                                      "Real.method(self, b)")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_methods_match_raises_on_missing_method(self):
        class Fake(object):
            def method(self, a): pass
        class Real(object):
            pass
        try:
            self.test.failUnlessMethodsMatch(Fake, Real)
        except AssertionError, e:
            self.assertEquals(str(e), "Fake.method(self, a) not present "
                                      "in Real")
        else: self.fail("AssertionError not raised")

    def test_fail_unless_methods_match_succeeds_on_missing_priv_method(self):
        class Fake(object):
            def _method(self, a): pass
        class Real(object):
            pass
        try:
            self.test.failUnlessMethodsMatch(Fake, Real)
        except AssertionError, e:
            self.fail("AssertionError shouldn't be raised")

    def test_fail_unless_methods_match_raises_on_different_priv_method(self):
        class Fake(object):
            def _method(self, a): pass
        class Real(object):
            def _method(self, b): pass
        try:
            self.test.failUnlessMethodsMatch(Fake, Real)
        except AssertionError, e:
            self.assertEquals(str(e), "Fake._method(self, a) != "
                                      "Real._method(self, b)")
        else:
            self.fail("AssertionError not raised")

    def test_fail_unless_methods_match_succeeds(self):
        class Fake(object):
            def method(self, a): pass
        class Real(object):
            def method(self, a): pass
        obj = []
        try:
            self.test.failUnlessMethodsMatch(Fake, Real)
        except AssertionError:
            self.fail("AssertionError shouldn't be raised")

    def test_aliases(self):
        get_method = MockerTestCase.__dict__.get

        self.assertEquals(get_method("assertIs"),
                          get_method("failUnlessIs"))

        self.assertEquals(get_method("assertIsNot"),
                          get_method("failIfIs"))

        self.assertEquals(get_method("assertIn"),
                          get_method("failUnlessIn"))

        self.assertEquals(get_method("assertNotIn"),
                          get_method("failIfIn"))

        self.assertEquals(get_method("assertStartsWith"),
                          get_method("failUnlessStartsWith"))

        self.assertEquals(get_method("assertNotStartsWith"),
                          get_method("failIfStartsWith"))

        self.assertEquals(get_method("assertEndsWith"),
                          get_method("failUnlessEndsWith"))

        self.assertEquals(get_method("assertNotEndsWith"),
                          get_method("failIfEndsWith"))

        self.assertEquals(get_method("assertApproximates"),
                          get_method("failUnlessApproximates"))

        self.assertEquals(get_method("assertNotApproximates"),
                          get_method("failIfApproximates"))

        self.assertEquals(get_method("assertMethodsMatch"),
                          get_method("failUnlessMethodsMatch"))

    def test_twisted_trial_aliases(self):
        get_method = MockerTestCase.__dict__.get

        self.assertEquals(get_method("assertIdentical"),
                          get_method("assertIs"))

        self.assertEquals(get_method("assertNotIdentical"),
                          get_method("assertIsNot"))

        self.assertEquals(get_method("failUnlessIdentical"),
                          get_method("failUnlessIs"))

        self.assertEquals(get_method("failIfIdentical"),
                          get_method("failIfIs"))

    def test_missing_python23_aliases(self):
        self.assertEquals(MockerTestCase.assertTrue.im_func,
                          MockerTestCase.failUnless.im_func)

        self.assertEquals(MockerTestCase.assertFalse.im_func,
                          MockerTestCase.failIf.im_func)

    def test_make_file_returns_writable_filename(self):
        filename = self.test.makeFile()
        self.assertFalse(os.path.isfile(filename))
        open(filename, "w").write("Is writable!")

    def test_make_file_creates_file(self):
        filename = self.test.makeFile("")
        self.assertEquals(os.path.getsize(filename), 0)

    def test_make_file_cleansup_on_success(self):
        filename = self.test.makeFile()
        self.test.run()
        self.assertEquals(os.path.isfile(filename), False)

    def test_make_file_cleansup_on_failure(self):
        class MyTest(MockerTestCase):
            def test_method(self):
                raise AssertionError("BOOM!")
        test = MyTest("test_method")
        filename = test.makeFile()
        test.run()
        self.assertEquals(os.path.isfile(filename), False)

    def test_make_file_with_content(self):
        filename = self.test.makeFile("content")
        self.assertEquals(open(filename).read(), "content")

    def test_make_file_with_prefix(self):
        filename = self.test.makeFile(prefix="prefix-")
        self.assertTrue(os.path.basename(filename).startswith("prefix-"))

    def test_make_file_with_suffix(self):
        filename = self.test.makeFile(suffix="-suffix")
        self.assertTrue(os.path.basename(filename).endswith("-suffix"))

    def test_make_file_with_dirname(self):
        dirname = tempfile.mkdtemp()
        try:
            filename = self.test.makeFile(dirname=dirname)
            self.assertEquals(os.path.dirname(filename), dirname)
        finally:
            shutil.rmtree(dirname)

    def test_make_file_with_basename(self):
        filename = self.test.makeFile(basename="basename")
        self.assertEquals(os.path.basename(filename), "basename")
        self.test.run()
        self.assertFalse(os.path.exists(filename))

    def test_make_file_with_basename_and_dirname(self):
        dirname = tempfile.mkdtemp()
        try:
            filename = self.test.makeFile(dirname=dirname, basename="basename")
            self.assertEquals(os.path.dirname(filename), dirname)
            self.assertEquals(os.path.basename(filename), "basename")
        finally:
            shutil.rmtree(dirname)

    def test_make_file_with_path(self):
        path = tempfile.mktemp()
        try:
            filename = self.test.makeFile("", path=path)
            self.assertEquals(filename, path)
            self.assertEquals(os.path.getsize(filename), 0)
            self.test.run()
            self.assertFalse(os.path.exists(filename))
        finally:
            if os.path.isfile(path):
                os.unlink(path)

    def test_make_dir_returns_dirname(self):
        dirname = self.test.makeDir()
        self.assertEquals(os.path.isdir(dirname), True)

    def test_make_dir_cleansup_on_success(self):
        dirname = self.test.makeDir()
        self.test.run()
        self.assertEquals(os.path.isdir(dirname), False)

    def test_make_dir_cleansup_on_failure(self):
        class MyTest(MockerTestCase):
            def test_method(self):
                raise AssertionError("BOOM!")
        test = MyTest("test_method")
        dirname = test.makeDir()
        test.run()
        self.assertEquals(os.path.isdir(dirname), False)

    def test_make_dir_with_prefix(self):
        dirname = self.test.makeDir(prefix="prefix-")
        self.assertTrue(os.path.basename(dirname).startswith("prefix-"))

    def test_make_dir_with_suffix(self):
        dirname = self.test.makeDir(suffix="-suffix")
        self.assertTrue(os.path.basename(dirname).endswith("-suffix"))

    def test_make_dir_with_dirname(self):
        dirname = tempfile.mkdtemp()
        try:
            path = self.test.makeDir(dirname=dirname)
            self.assertEquals(os.path.dirname(path), dirname)
        finally:
            if os.path.exists(dirname):
                shutil.rmtree(dirname)

    def test_make_dir_with_path(self):
        path = tempfile.mktemp()
        try:
            self.assertEquals(self.test.makeDir(path=path), path)
            self.assertEquals(os.path.isdir(path), True)
            self.test.run()
            self.assertEquals(os.path.isdir(path), False)
        finally:
            if os.path.exists(path):
                shutil.rmtree(path)


class MockerTest(TestCase):

    def setUp(self):
        self.recorded = []
        self.mocker = CleanMocker()
        def recorder(mocker, event):
            self.recorded.append((mocker, event))
        self.mocker.add_recorder(recorder)

        self.action = Action("getattr", ("attr",), {},
                             Path(Mock(self.mocker, name="mock")))
        self.path = self.action.path + self.action

    def test_default_is_recording(self):
        self.assertTrue(self.mocker.is_recording())

    def test_replay(self):
        calls = []
        event = self.mocker.add_event(Event())
        task = event.add_task(Task())
        task.replay = lambda: calls.append("replay")
        task.restore = lambda: calls.append("restore")
        self.mocker.replay()
        self.assertFalse(self.mocker.is_recording())
        self.assertEquals(calls, ["replay"])
        self.mocker.replay()
        self.assertEquals(calls, ["replay", "restore", "replay"])

    def test_restore(self):
        calls = []
        event = self.mocker.add_event(Event())
        task = event.add_task(Task())
        task.replay = lambda: calls.append("replay")
        task.restore = lambda: calls.append("restore")
        self.mocker.replay()
        self.mocker.restore()
        self.mocker.restore()
        self.assertTrue(self.mocker.is_recording())
        self.assertEquals(calls, ["replay", "restore"])

    def test_reset(self):
        calls = []
        event = self.mocker.add_event(Event())
        task = event.add_task(Task())
        task.restore = lambda: calls.append("restore")
        self.mocker.replay()
        self.mocker.reset()
        self.mocker.reset()
        self.assertEquals(calls, ["restore"])
        self.assertEquals(self.mocker.get_events(), [])

    def test_reset_removes_ordering(self):
        self.mocker.order()
        self.mocker.reset()
        self.assertFalse(self.mocker.is_ordering())

    def test_verify(self):
        class MyEvent(object):
            def __init__(self, id, failed):
                self.id = id
                self.failed = failed
            def verify(self):
                if self.failed:
                    raise AssertionError("%d failed\n- Line 1\n- Line 2\n"
                                         % self.id)

        self.mocker.add_event(MyEvent(1, True))
        self.mocker.add_event(MyEvent(2, False))
        self.mocker.add_event(MyEvent(3, True))

        try:
            self.mocker.verify()
        except AssertionError, e:
            message = os.linesep.join(["[Mocker] Unmet expectations:",
                                       "",
                                       "=> 1 failed",
                                       " - Line 1",
                                       " - Line 2",
                                       "",
                                       "=> 3 failed",
                                       " - Line 1",
                                       " - Line 2",
                                       ""])
            self.assertEquals(str(e), message)
        else:
            self.fail("AssertionError not raised")

    def test_verify_errors_need_good_messages(self):
        class MyEvent(object):
            def verify(self):
                raise AssertionError()
        self.mocker.add_event(MyEvent())
        self.assertRaises(RuntimeError, self.mocker.verify)

    def test_mocker_as_context_manager(self):
        calls = []
        throw = False
        class MyEvent(Event):
            def verify(self):
                calls.append("verify")
                if throw:
                    raise AssertionError("Some problem")
            def replay(self):
                calls.append("replay")
            def restore(self):
                calls.append("restore")

        event = MyEvent()
        self.mocker.add_event(event)

        self.assertEquals(calls, [])

        mocker = self.mocker.__enter__()
        self.assertTrue(mocker is self.mocker)
        self.assertEquals(calls, ["replay"])

        # Verify without errors.
        del calls[:]
        result = self.mocker.__exit__(None, None, None)
        self.assertEquals(result, False)
        self.assertEquals(calls, ["restore", "verify"])

        throw = True

        # Verify raising an error.
        self.mocker.replay()
        del calls[:]
        self.assertRaises(AssertionError,
                          self.mocker.__exit__, None, None, None)
        self.assertEquals(calls, ["restore", "verify"])

        # An exception happened in the 'with' block.  Verify won't raise.
        self.mocker.replay()
        del calls[:]
        result = self.mocker.__exit__(AssertionError, None, None)
        self.assertEquals(result, False)
        self.assertEquals(calls, ["restore"])

    def test_add_recorder_on_instance(self):
        obj1 = object()
        obj2 = object()
        mocker = CleanMocker()
        self.assertEquals(mocker.add_recorder(obj1), obj1)
        self.assertEquals(mocker.add_recorder(obj2), obj2)
        self.assertEquals(mocker.get_recorders(), [obj1, obj2])
        mocker = CleanMocker()
        self.assertEquals(mocker.add_recorder(obj1), obj1)
        self.assertEquals(mocker.get_recorders(), [obj1])

    def test_add_recorder_on_class(self):
        class MyMocker(CleanMocker):
            pass
        obj1 = object()
        obj2 = object()
        self.assertEquals(MyMocker.add_recorder(obj1), obj1)
        self.assertEquals(MyMocker.add_recorder(obj2), obj2)
        mocker = MyMocker()
        self.assertEquals(mocker.get_recorders(), [obj1, obj2])
        mocker = MyMocker()
        self.assertEquals(mocker.get_recorders(), [obj1, obj2])

    def test_add_recorder_on_subclass(self):
        class MyMocker1(CleanMocker):
            pass
        obj1 = object()
        MyMocker1.add_recorder(obj1)
        class MyMocker2(MyMocker1):
            pass
        obj2 = object()
        MyMocker2.add_recorder(obj2)
        self.assertEquals(MyMocker1.get_recorders(), [obj1])
        self.assertEquals(MyMocker2.get_recorders(), [obj1, obj2])

    def test_remove_recorder_on_instance(self):
        obj1 = object()
        obj2 = object()
        obj3 = object()
        class MyMocker(CleanMocker):
            pass
        MyMocker.add_recorder(obj1)
        MyMocker.add_recorder(obj2)
        MyMocker.add_recorder(obj3)
        mocker = MyMocker()
        mocker.remove_recorder(obj2)
        self.assertEquals(mocker.get_recorders(), [obj1, obj3])
        self.assertEquals(MyMocker.get_recorders(), [obj1, obj2, obj3])

    def test_remove_recorder_on_class(self):
        class MyMocker(CleanMocker):
            pass
        obj1 = object()
        obj2 = object()
        self.assertEquals(MyMocker.add_recorder(obj1), obj1)
        self.assertEquals(MyMocker.add_recorder(obj2), obj2)
        MyMocker.remove_recorder(obj1)
        self.assertEquals(MyMocker.get_recorders(), [obj2])

    def test_mock(self):
        mock = self.mocker.mock()
        self.assertEquals(mock.__mocker_name__, None)
        self.assertEquals(mock.__mocker_spec__, None)
        self.assertEquals(mock.__mocker_type__, None)
        self.assertEquals(mock.__mocker_count__, True)

    def test_mock_with_name(self):
        mock = self.mocker.mock(name="name")
        self.assertEquals(mock.__mocker_name__, "name")

    def test_mock_with_spec(self):
        class C(object): pass
        mock = self.mocker.mock(spec=C)
        self.assertEquals(mock.__mocker_spec__, C)

    def test_mock_with_type(self):
        class C(object): pass
        mock = self.mocker.mock(type=C)
        self.assertEquals(mock.__mocker_type__, C)

    def test_mock_with_spec_and_type(self):
        class C(object): pass
        mock = self.mocker.mock(C)
        self.assertEquals(mock.__mocker_spec__, C)
        self.assertEquals(mock.__mocker_type__, C)

    def test_mock_with_count(self):
        class C(object): pass
        mock = self.mocker.mock(count=False)
        self.assertEquals(mock.__mocker_count__, False)

    def test_proxy(self):
        original = object()
        mock = self.mocker.proxy(original)
        self.assertEquals(type(mock), Mock)
        self.assertEquals(mock.__mocker_object__, original)
        self.assertEquals(mock.__mocker_path__.root_object, original)
        self.assertEquals(mock.__mocker_count__, True)

    def test_proxy_with_count(self):
        original = object()
        mock = self.mocker.proxy(original, count=False)
        self.assertEquals(mock.__mocker_count__, False)

    def test_proxy_with_spec(self):
        original = object()
        class C(object): pass
        mock = self.mocker.proxy(original, C)
        self.assertEquals(mock.__mocker_object__, original)
        self.assertEquals(mock.__mocker_spec__, C)

    def test_proxy_with_type(self):
        original = object()
        class C(object): pass
        mock = self.mocker.proxy(original, type=C)
        self.assertEquals(mock.__mocker_type__, C)

    def test_proxy_spec_defaults_to_the_object_itself(self):
        original = object()
        mock = self.mocker.proxy(original)
        self.assertEquals(mock.__mocker_spec__, original)

    def test_proxy_type_defaults_to_the_object_type(self):
        original = object()
        mock = self.mocker.proxy(original)
        self.assertEquals(mock.__mocker_type__, object)

    def test_proxy_with_spec_and_type_none(self):
        original = object()
        mock = self.mocker.proxy(original, spec=None, type=None)
        self.assertEquals(mock.__mocker_spec__, None)
        self.assertEquals(mock.__mocker_type__, None)

    def test_proxy_with_passthrough_false(self):
        original = object()
        class C(object): pass
        mock = self.mocker.proxy(original, C, passthrough=False)
        self.assertEquals(mock.__mocker_object__, original)
        self.assertEquals(mock.__mocker_spec__, C)
        self.assertEquals(mock.__mocker_passthrough__, False)

    def test_proxy_with_submodule_string(self):
        from os import path
        module = self.mocker.proxy("os.path")
        self.assertEquals(type(module), Mock)
        self.assertEquals(type(module.__mocker_object__), ModuleType)
        self.assertEquals(module.__mocker_name__, "os.path")
        self.assertEquals(module.__mocker_object__, path)

    def test_proxy_with_module_function_string(self):
        mock = self.mocker.proxy("os.path.join.func_name")
        self.assertEquals(mock.__mocker_object__, "join")

    def test_proxy_with_string_and_name(self):
        module = self.mocker.proxy("os.path", name="mock")
        self.assertEquals(module.__mocker_name__, "mock")

    def test_proxy_with_unexistent_module(self):
        self.assertRaises(ImportError, self.mocker.proxy, "unexistent.module")

    def test_replace(self):
        from os import path
        obj = object()
        proxy = self.mocker.replace(obj, spec=object, name="obj", count=False,
                                    passthrough=False)
        self.assertEquals(type(proxy), Mock)
        self.assertEquals(type(proxy.__mocker_object__), object)
        self.assertEquals(proxy.__mocker_object__, obj)
        self.assertEquals(proxy.__mocker_spec__, object)
        self.assertEquals(proxy.__mocker_name__, "obj")
        self.assertEquals(proxy.__mocker_count__, False)
        (event,) = self.mocker.get_events()
        self.assertEquals(type(event), ReplayRestoreEvent)
        (task,) = event.get_tasks()
        self.assertEquals(type(task), ProxyReplacer)
        self.assertTrue(task.mock is proxy)
        self.assertTrue(task.mock.__mocker_object__ is obj)
        self.assertTrue(proxy is not obj)

    def test_replace_with_submodule_string(self):
        from os import path
        module = self.mocker.replace("os.path")
        self.assertEquals(type(module), Mock)
        self.assertEquals(type(module.__mocker_object__), ModuleType)
        self.assertEquals(module.__mocker_name__, "os.path")
        self.assertEquals(module.__mocker_object__, path)
        (event,) = self.mocker.get_events()
        (task,) = event.get_tasks()
        self.assertEquals(type(task), ProxyReplacer)
        self.assertTrue(task.mock is module)
        self.assertTrue(task.mock.__mocker_object__ is path)
        self.assertTrue(module is not path)

    def test_replace_with_module_function_string(self):
        mock = self.mocker.replace("os.path.join.func_name")
        self.assertEquals(mock.__mocker_object__, "join")

    def test_replace_with_string_and_name(self):
        module = self.mocker.replace("os.path", name="mock")
        self.assertEquals(module.__mocker_name__, "mock")

    def test_replace_with_type(self):
        original = object()
        class C(object): pass
        mock = self.mocker.replace(original, type=C)
        self.assertEquals(mock.__mocker_type__, C)

    def test_replace_spec_defaults_to_the_object_itself(self):
        original = object()
        mock = self.mocker.replace(original)
        self.assertEquals(mock.__mocker_spec__, original)

    def test_replace_type_defaults_to_the_object_type(self):
        original = object()
        mock = self.mocker.replace(original)
        self.assertEquals(mock.__mocker_type__, object)

    def test_replace_with_spec_and_type_none(self):
        original = object()
        mock = self.mocker.replace(original, spec=None, type=None)
        self.assertEquals(mock.__mocker_spec__, None)
        self.assertEquals(mock.__mocker_type__, None)

    def test_replace_with_passthrough_false(self):
        original = object()
        class C(object): pass
        mock = self.mocker.replace(original, passthrough=False)
        self.assertEquals(mock.__mocker_passthrough__, False)

    def test_add_and_get_event(self):
        self.mocker.add_event(41)
        self.assertEquals(self.mocker.add_event(42), 42)
        self.assertEquals(self.mocker.get_events(), [41, 42])

    def test_recording(self):
        obj = self.mocker.mock()
        obj.attr()

        self.assertEquals(len(self.recorded), 2)

        action1 = Action("getattr", ("attr",), {})
        action2 = Action("call", (), {})

        mocker1, event1 = self.recorded[0]
        self.assertEquals(mocker1, self.mocker)
        self.assertEquals(type(event1), Event)
        self.assertTrue(event1.path.matches(Path(obj, None, [action1])))

        mocker2, event2 = self.recorded[1]
        self.assertEquals(mocker2, self.mocker)
        self.assertEquals(type(event2), Event)
        self.assertTrue(event2.path.matches(Path(obj, None,
                                                 [action1, action2])))

        self.assertEquals(self.mocker.get_events(), [event1, event2])

    def test_recording_result_path(self):
        obj = self.mocker.mock()
        result = obj.attr()
        path = Path(obj, None, [Action("getattr", ("attr",), {}),
                                Action("call", (), {})])
        self.assertTrue(result.__mocker_path__.matches(path))

    def test_replaying_no_events(self):
        self.mocker.replay()
        try:
            self.mocker.act(self.path)
        except AssertionError, e:
            pass
        else:
            self.fail("AssertionError not raised")
        self.assertEquals(str(e), "[Mocker] Unexpected expression: mock.attr")

    def test_replaying_matching(self):
        calls = []
        class MyTask(Task):
            def matches(_, path):
                calls.append("matches")
                self.assertTrue(self.path.matches(path))
                return True
            def run(_, path):
                calls.append("run")
                self.assertTrue(self.path.matches(path))
                return "result"
        event = Event()
        event.add_task(MyTask())
        self.mocker.add_event(event)
        self.mocker.replay()
        self.assertEquals(self.mocker.act(self.path), "result")
        self.assertEquals(calls, ["matches", "run"])

    def test_replaying_none_matching(self):
        calls = []
        class MyTask(Task):
            def matches(_, path):
                self.assertTrue(self.path.matches(path))
                calls.append("matches")
                return False
        event = Event()
        event.add_task(MyTask())
        self.mocker.add_event(event)
        self.mocker.replay()
        self.assertRaises(AssertionError, self.mocker.act, self.path)
        self.assertEquals(calls, ["matches"])

    def test_replay_order(self):
        """
        When playing back, the precedence of events is as follows:

        1. Events with may_run() true
        2. Events with satisfied() false
        3. Events with has_run() false

        """
        class MyTaskBase(Task):
            postpone = 2
            def may_run(self, path):
                if not self.postpone:
                    return True
                self.postpone -= 1
            def run(self, path):
                return self.__class__.__name__
        class MyTask1(MyTaskBase): pass
        class MyTask2(MyTaskBase): pass
        class MyTask3(MyTaskBase):
            raised = False
            def verify(self):
                if not self.postpone and not self.raised:
                    self.raised = True
                    raise AssertionError("An error")
        class MyTask4(MyTaskBase):
            postpone = 0
        class MyTask5(MyTaskBase):
            postpone = 1

        event1 = self.mocker.add_event(Event())
        event1.add_task(MyTask1())
        event2 = self.mocker.add_event(Event())
        event2.add_task(MyTask2())
        event3 = self.mocker.add_event(Event())
        event3.add_task(MyTask3())
        event4 = self.mocker.add_event(Event())
        event4.add_task(MyTask4())
        event5 = self.mocker.add_event(Event())
        event5.add_task(MyTask5())
        self.mocker.replay()

        # Labels: [M]ay run, [S]atisfied, [H]as run

        # State: 1=S 2=S 3= 4=MS 5=S
        self.assertEquals(self.mocker.act(self.path), "MyTask4")
        # State: 1=S 2=S 3= 4=MSH 5=S
        self.assertEquals(self.mocker.act(self.path), "MyTask4")
        # State: 1=MS 2=MS 3=M 4=MSH 5=MS
        self.assertEquals(self.mocker.act(self.path), "MyTask3")
        # State: 1=MS 2=MS 3=MSH 4=MSH 5=MS
        self.assertEquals(self.mocker.act(self.path), "MyTask1")
        # State: 1=MSH 2=MS 3=MSH 4=MSH 5=MS
        self.assertEquals(self.mocker.act(self.path), "MyTask2")
        # State: 1=MSH 2=MSH 3=MSH 4=MSH 5=MS
        self.assertEquals(self.mocker.act(self.path), "MyTask5")
        # State: 1=MSH 2=MSH 3=MSH 4=MSH 5=MSH
        self.assertEquals(self.mocker.act(self.path), "MyTask1")

    def test_recorder_decorator(self):
        result = recorder(42)
        try:
            self.assertEquals(result, 42)
            self.assertEquals(Mocker.get_recorders()[-1], 42)
            self.assertEquals(MockerBase.get_recorders(), [])
        finally:
            Mocker.remove_recorder(42)

    def test_result(self):
        event1 = self.mocker.add_event(Event())
        event2 = self.mocker.add_event(Event())
        self.mocker.result(123)
        self.assertEquals(event2.run(self.path), 123)

    def test_throw(self):
        class MyException(Exception): pass
        event1 = self.mocker.add_event(Event())
        event2 = self.mocker.add_event(Event())
        self.mocker.throw(MyException)
        self.assertRaises(MyException, event2.run, self.path)

    def test_call(self):
        event1 = self.mocker.add_event(Event())
        event2 = self.mocker.add_event(Event())
        self.mocker.call(lambda *args, **kwargs: 123)
        self.assertEquals(event2.run(self.path), 123)

    def test_count(self):
        event1 = self.mocker.add_event(Event())
        event2 = self.mocker.add_event(Event())
        event2.add_task(ImplicitRunCounter(1))
        self.mocker.count(2, 3)
        self.assertEquals(len(event1.get_tasks()), 0)
        (task,) = event2.get_tasks()
        self.assertEquals(type(task), RunCounter)
        self.assertEquals(task.min, 2)
        self.assertEquals(task.max, 3)
        self.mocker.count(4)
        self.assertEquals(len(event1.get_tasks()), 0)
        (task,) = event2.get_tasks()
        self.assertEquals(type(task), RunCounter)
        self.assertEquals(task.min, 4)
        self.assertEquals(task.max, 4)

    def test_order(self):
        mock1 = self.mocker.mock()
        mock2 = self.mocker.mock()
        mock3 = self.mocker.mock()
        mock4 = self.mocker.mock()
        result1 = mock1.attr1(1)
        result2 = mock2.attr2(2)
        result3 = mock3.attr3(3)
        result4 = mock4.attr4(4)

        # Try to spoil the logic which decides which task to reuse.
        other_task = Task()
        for event in self.mocker.get_events():
            event.add_task(other_task)

        self.mocker.order(result1, result2, result3)
        self.mocker.order(result1, result4)
        self.mocker.order(result2, result4)
        events = self.mocker.get_events()
        self.assertEquals(len(events), 8)

        self.assertEquals(events[0].get_tasks(), [other_task])
        other_task_, task1 = events[1].get_tasks()
        self.assertEquals(type(task1), Orderer)
        self.assertEquals(task1.path, events[1].path)
        self.assertEquals(task1.get_dependencies(), [])
        self.assertEquals(other_task_, other_task)

        self.assertEquals(events[2].get_tasks(), [other_task])
        other_task_, task3 = events[3].get_tasks()
        self.assertEquals(type(task3), Orderer)
        self.assertEquals(task3.path, events[3].path)
        self.assertEquals(task3.get_dependencies(), [task1])
        self.assertEquals(other_task_, other_task)

        self.assertEquals(events[4].get_tasks(), [other_task])
        other_task_, task5 = events[5].get_tasks()
        self.assertEquals(type(task5), Orderer)
        self.assertEquals(task5.path, events[5].path)
        self.assertEquals(task5.get_dependencies(), [task3])
        self.assertEquals(other_task_, other_task)

        self.assertEquals(events[6].get_tasks(), [other_task])
        other_task_, task7 = events[7].get_tasks()
        self.assertEquals(type(task7), Orderer)
        self.assertEquals(task7.path, events[7].path)
        self.assertEquals(task7.get_dependencies(), [task1, task3])
        self.assertEquals(other_task_, other_task)

    def test_after(self):
        mock1 = self.mocker.mock()
        mock2 = self.mocker.mock()
        mock3 = self.mocker.mock()
        result1 = mock1.attr1(1)
        result2 = mock2.attr2(2)
        result3 = mock3.attr3(3)

        # Try to spoil the logic which decides which task to reuse.
        other_task = Task()
        for event in self.mocker.get_events():
            event.add_task(other_task)

        self.mocker.after(result1, result2)

        events = self.mocker.get_events()
        self.assertEquals(len(events), 6)

        self.assertEquals(events[0].get_tasks(), [other_task])
        other_task_, task1 = events[1].get_tasks()
        self.assertEquals(type(task1), Orderer)
        self.assertEquals(task1.path, events[1].path)
        self.assertEquals(task1.get_dependencies(), [])
        self.assertEquals(other_task_, other_task)

        self.assertEquals(events[2].get_tasks(), [other_task])
        other_task_, task3 = events[3].get_tasks()
        self.assertEquals(type(task3), Orderer)
        self.assertEquals(task3.path, events[3].path)
        self.assertEquals(task3.get_dependencies(), [])
        self.assertEquals(other_task_, other_task)

        self.assertEquals(events[4].get_tasks(), [other_task])
        other_task_, task5 = events[5].get_tasks()
        self.assertEquals(type(task5), Orderer)
        self.assertEquals(task5.path, events[5].path)
        self.assertEquals(task5.get_dependencies(), [task1, task3])
        self.assertEquals(other_task_, other_task)

    def test_before(self):
        mock1 = self.mocker.mock()
        mock2 = self.mocker.mock()
        mock3 = self.mocker.mock()
        result1 = mock1.attr1(1)
        result2 = mock2.attr2(2)
        result3 = mock3.attr3(3)

        # Try to spoil the logic which decides which task to reuse.
        other_task = Task()
        for event in self.mocker.get_events():
            event.add_task(other_task)

        self.mocker.before(result1, result2)

        events = self.mocker.get_events()
        self.assertEquals(len(events), 6)

        self.assertEquals(events[4].get_tasks(), [other_task])
        other_task_, task5 = events[5].get_tasks()
        self.assertEquals(type(task5), Orderer)
        self.assertEquals(task5.path, events[5].path)
        self.assertEquals(task5.get_dependencies(), [])
        self.assertEquals(other_task_, other_task)

        self.assertEquals(events[0].get_tasks(), [other_task])
        other_task_, task1 = events[1].get_tasks()
        self.assertEquals(type(task1), Orderer)
        self.assertEquals(task1.path, events[1].path)
        self.assertEquals(task1.get_dependencies(), [task5])
        self.assertEquals(other_task_, other_task)

        self.assertEquals(events[2].get_tasks(), [other_task])
        other_task_, task3 = events[3].get_tasks()
        self.assertEquals(type(task3), Orderer)
        self.assertEquals(task3.path, events[3].path)
        self.assertEquals(task3.get_dependencies(), [task5])
        self.assertEquals(other_task_, other_task)

    def test_default_ordering(self):
        self.assertEquals(self.mocker.is_ordering(), False)

    def test_order_without_arguments(self):
        self.mocker.order()
        self.assertEquals(self.mocker.is_ordering(), True)

    def test_order_with_context_manager(self):
        with_manager = self.mocker.order()
        self.assertEquals(self.mocker.is_ordering(), True)
        with_manager.__enter__()
        self.assertEquals(self.mocker.is_ordering(), True)
        with_manager.__exit__(None, None, None)
        self.assertEquals(self.mocker.is_ordering(), False)

    def test_unorder(self):
        self.mocker.order()
        self.mocker.unorder()
        self.assertEquals(self.mocker.is_ordering(), False)

    def test_ordered_events(self):
        mock = self.mocker.mock()

        # Ensure that the state is correctly reset between
        # different ordered blocks.
        self.mocker.order()

        mock.a

        self.mocker.unorder()
        self.mocker.order()

        mock.x.y.z

        events = self.mocker.get_events()

        (task1,) = events[1].get_tasks()
        (task2,) = events[2].get_tasks()
        (task3,) = events[3].get_tasks()

        self.assertEquals(type(task1), Orderer)
        self.assertEquals(type(task2), Orderer)
        self.assertEquals(type(task3), Orderer)

        self.assertEquals(task1.path, events[1].path)
        self.assertEquals(task2.path, events[2].path)
        self.assertEquals(task3.path, events[3].path)

        self.assertEquals(task1.get_dependencies(), [])
        self.assertEquals(task2.get_dependencies(), [task1])
        self.assertEquals(task3.get_dependencies(), [task2])

    def test_nospec(self):
        event1 = self.mocker.add_event(Event())
        event2 = self.mocker.add_event(Event())
        task1 = event1.add_task(SpecChecker(None))
        task2 = event2.add_task(Task())
        task3 = event2.add_task(SpecChecker(None))
        task4 = event2.add_task(Task())
        self.mocker.nospec()
        self.assertEquals(event1.get_tasks(), [task1])
        self.assertEquals(event2.get_tasks(), [task2, task4])

    def test_passthrough(self):
        obj = object()
        mock = self.mocker.proxy(obj)
        event1 = self.mocker.add_event(Event(Path(mock, obj)))
        event2 = self.mocker.add_event(Event(Path(mock, obj)))
        self.mocker.passthrough()
        self.assertEquals(event1.get_tasks(), [])
        (task,) = event2.get_tasks()
        self.assertEquals(type(task), PathExecuter)

    def test_passthrough_fails_on_unproxied(self):
        mock = self.mocker.mock()
        event1 = self.mocker.add_event(Event(Path(mock)))
        event2 = self.mocker.add_event(Event(Path(mock)))
        self.assertRaises(TypeError, self.mocker.passthrough)

    def test_passthrough(self):
        obj = object()
        mock = self.mocker.proxy(obj)
        event = self.mocker.add_event(Event(Path(mock, obj)))
        result_callback = object()
        self.mocker.passthrough(result_callback)
        (task,) = event.get_tasks()
        self.assertEquals(task.get_result_callback(), result_callback)

    def test_on(self):
        obj = self.mocker.mock()
        self.mocker.on(obj.attr).result(123)
        self.mocker.replay()
        self.assertEquals(obj.attr, 123)

    def test_patch(self):
        class C(object): pass
        mock = self.mocker.patch(C)
        self.assertEquals(type(C.__mocker_mock__), Mock)
        self.assertTrue(C.__mocker_mock__ is mock)
        self.assertTrue(mock.__mocker_object__ is C)
        self.assertEquals(type(mock.__mocker_patcher__), Patcher)
        self.assertEquals(mock.__mocker_passthrough__, True)
        self.assertEquals(mock.__mocker_spec__, C)
        (event,) = self.mocker.get_events()
        self.assertEquals(type(event), ReplayRestoreEvent)
        (task,) = event.get_tasks()
        self.assertTrue(task is mock.__mocker_patcher__)

    def test_patch_without_spec(self):
        class C(object): pass
        mock = self.mocker.patch(C, spec=None)
        self.assertEquals(mock.__mocker_spec__, None)


class ActionTest(TestCase):

    def setUp(self):
        self.mock = Mock(None, name="mock")

    def test_create(self):
        objects = [object() for i in range(4)]
        action = Action(*objects)
        self.assertEquals(action.kind, objects[0])
        self.assertEquals(action.args, objects[1])
        self.assertEquals(action.kwargs, objects[2])
        self.assertEquals(action.path, objects[3])

    def test_repr(self):
        self.assertEquals(repr(Action("kind", "args", "kwargs")),
                          "Action('kind', 'args', 'kwargs')")
        self.assertEquals(repr(Action("kind", "args", "kwargs", "path")),
                          "Action('kind', 'args', 'kwargs', 'path')")

    def test_execute_unknown(self):
        self.assertRaises(RuntimeError, Action("unknown", (), {}).execute, None)

    def test_execute_getattr(self):
        class C(object):
            pass
        obj = C()
        obj.attr = C()
        action = Action("getattr", ("attr",), {})
        self.assertEquals(action.execute(obj), obj.attr)

    def test_execute_setattr(self):
        class C(object):
            pass
        obj = C()
        action = Action("setattr", ("attr", "value"), {})
        action.execute(obj)
        self.assertEquals(getattr(obj, "attr", None), "value")

    def test_execute_delattr(self):
        class C(object):
            pass
        obj = C()
        obj.attr = "value"
        action = Action("delattr", ("attr",), {})
        action.execute(obj)
        self.assertEquals(getattr(obj, "attr", None), None)

    def test_execute_call(self):
        obj = lambda a, b: a+b
        action = Action("call", (1,), {"b": 2})
        self.assertEquals(action.execute(obj), 3)

    def test_execute_contains(self):
        obj = ["a"]
        action = Action("contains", ("a",), {})
        self.assertEquals(action.execute(obj), True)
        action = Action("contains", ("b",), {})
        self.assertEquals(action.execute(obj), False)

    def test_execute_getitem(self):
        obj = {"a": 1}
        action = Action("getitem", ("a",), {})
        self.assertEquals(action.execute(obj), 1)
        action = Action("getitem", ("b",), {})
        self.assertRaises(KeyError, action.execute, obj)

    def test_execute_setitem(self):
        obj = {}
        action = Action("setitem", ("a", 1), {})
        action.execute(obj)
        self.assertEquals(obj, {"a": 1})

    def test_execute_delitem(self):
        obj = {"a": 1, "b": 2}
        action = Action("delitem", ("a",), {})
        action.execute(obj)
        self.assertEquals(obj, {"b": 2})

    def test_execute_len(self):
        obj = [1, 2, 3]
        action = Action("len", (), {})
        self.assertEquals(action.execute(obj), 3)

    def test_execute_nonzero(self):
        obj = []
        action = Action("nonzero", (), {})
        self.assertEquals(action.execute(obj), False)
        obj = [1]
        action = Action("nonzero", (), {})
        self.assertEquals(action.execute(obj), True)

    def test_execute_iter(self):
        obj = [1, 2, 3]
        action = Action("iter", (), {})
        result = action.execute(obj)
        self.assertEquals(type(result), type(iter(obj)))
        self.assertEquals(list(result), obj)

    def test_execute_caching(self):
        values = iter(range(10))
        obj = lambda: values.next()
        action = Action("call", (), {})
        self.assertEquals(action.execute(obj), 0)
        self.assertEquals(action.execute(obj), 0)
        obj = lambda: values.next()
        self.assertEquals(action.execute(obj), 1)

    def test_equals(self):
        obj1 = object()
        obj2 = object()

        self.assertEquals(Action("kind", (), {}, obj1),
                          Action("kind", (), {}, obj2))
        self.assertNotEquals(Action("kind", (), {}, obj1),
                             Action("dnik", (), {}, obj2))
        self.assertNotEquals(Action("kind", (), {}, obj1),
                             Action("kind", (1,), {}, obj2))
        self.assertNotEquals(Action("kind", (), {}, obj1),
                             Action("kind", (), {"a": 1}, obj2))
        self.assertNotEquals(Action("kind", (ANY,), {}, obj1),
                             Action("kind", (1,), {}, obj2))
        self.assertEquals(Action("kind", (CONTAINS(1),), {}, obj1),
                          Action("kind", (CONTAINS(1),), {}, obj2))

    def test_matches(self):
        obj1 = object()
        obj2 = object()

        action1 = Action("kind", (), {}, obj1)
        action2 = Action("kind", (), {}, obj2)
        self.assertTrue(action1.matches(action2))

        action1 = Action("kind", (), {}, obj1)
        action2 = Action("dnik", (), {}, obj2)
        self.assertFalse(action1.matches(action2))

        action1 = Action("kind", (), {}, obj1)
        action2 = Action("kind", (1,), {}, obj2)
        self.assertFalse(action1.matches(action2))

        action1 = Action("kind", (), {}, obj1)
        action2 = Action("kind", (), {"a": 1}, obj2)
        self.assertFalse(action1.matches(action2))

        action1 = Action("kind", (ARGS,), {}, obj1)
        action2 = Action("kind", (), {}, obj2)
        self.assertTrue(action1.matches(action2))

        action1 = Action("kind", (ARGS,), {"a": 1}, obj1)
        action2 = Action("kind", (), {}, obj2)
        self.assertFalse(action1.matches(action2))


class PathTest(TestCase):

    def setUp(self):
        class StubMocker(object):
            def act(self, path):
                pass
        self.mocker = StubMocker()
        self.mock = Mock(self.mocker, name="obj")
        self.object = object()

    def test_create(self):
        mock = object()
        path = Path(mock)
        self.assertEquals(path.root_mock, mock)
        self.assertEquals(path.root_object, None)
        self.assertEquals(path.actions, ())

    def test_create_with_object(self):
        mock = object()
        path = Path(mock, self.object)
        self.assertEquals(path.root_mock, mock)
        self.assertEquals(path.root_object, self.object)

    def test_create_with_actions(self):
        mock = object()
        path = Path(mock, self.object, [1,2,3])
        self.assertEquals(path.root_mock, mock)
        self.assertEquals(path.root_object, self.object)
        self.assertEquals(path.actions, (1,2,3))

    def test_add(self):
        mock = object()
        path = Path(mock, self.object, [1,2,3])
        result = path + 4
        self.assertTrue(result is not path)
        self.assertEquals(result.root_mock, mock)
        self.assertEquals(result.root_object, self.object)
        self.assertEquals(result.actions, (1,2,3,4))

    def test_parent_path(self):
        path1 = Path(self.mock)
        path2 = path1 + Action("getattr", ("attr",), {}, path1)
        path3 = path2 + Action("getattr", ("attr",), {}, path2)

        self.assertEquals(path1.parent_path, None)
        self.assertEquals(path2.parent_path, path1)
        self.assertEquals(path3.parent_path, path2)

    def test_equals(self):
        mock = object()
        obj = object()
        obj1 = object()
        obj2 = object()

        # Not the *same* mock.
        path1 = Path([], obj, [])
        path2 = Path([], obj, [])
        self.assertNotEquals(path1, path2)

        # Not the *same* object.
        path1 = Path(mock, [], [])
        path2 = Path(mock, [], [])
        self.assertNotEquals(path1, path2)

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(mock, obj, [Action("kind", (), {}, obj2)])
        self.assertEquals(path1, path2)

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(mock, obj, [Action("dnik", (), {}, obj2)])
        self.assertNotEquals(path1, path2)

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(object(), obj, [Action("kind", (), {}, obj2)])
        self.assertNotEquals(path1, path2)

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(mock, obj, [Action("kind", (1,), {}, obj2)])
        self.assertNotEquals(path1, path2)

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(mock, obj, [Action("kind", (), {"a": 1}, obj2)])
        self.assertNotEquals(path1, path2)

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(mock, obj, [])
        self.assertNotEquals(path1, path2)

        path1 = Path(mock, obj, [Action("kind", (ANY,), {}, obj1)])
        path2 = Path(mock, obj, [Action("kind", (1,), {}, obj2)])
        self.assertNotEquals(path1, path2)

        path1 = Path(mock, obj, [Action("kind", (CONTAINS(1),), {}, obj1)])
        path2 = Path(mock, obj, [Action("kind", (CONTAINS(1),), {}, obj2)])
        self.assertEquals(path1, path2)

    def test_matches(self):
        obj = object()
        mock = object()
        obj1 = object()
        obj2 = object()

        # Not the *same* mock.
        path1 = Path([], obj, [])
        path2 = Path([], obj, [])
        self.assertFalse(path1.matches(path2))

        path1 = Path(mock, obj1, [])
        path2 = Path(mock, obj2, [])
        self.assertTrue(path1.matches(path2))

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(mock, obj, [Action("kind", (), {}, obj2)])
        self.assertTrue(path1.matches(path2))

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(mock, obj, [Action("dnik", (), {}, obj2)])
        self.assertFalse(path1.matches(path2))

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(object(), [Action("kind", (), {}, obj2)])
        self.assertFalse(path1.matches(path2))

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(mock, obj, [Action("kind", (1,), {}, obj2)])
        self.assertFalse(path1.matches(path2))

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(mock, obj, [Action("kind", (), {"a": 1}, obj2)])
        self.assertFalse(path1.matches(path2))

        path1 = Path(mock, obj, [Action("kind", (), {}, obj1)])
        path2 = Path(mock, obj, [])
        self.assertFalse(path1.matches(path2))

        path1 = Path(mock, obj, [Action("kind", (ARGS,), {}, obj1)])
        path2 = Path(mock, obj, [Action("kind", (), {}, obj2)])
        self.assertTrue(path1.matches(path2))

        path1 = Path(mock, obj, [Action("kind", (ARGS,), {"a": 1}, obj1)])
        path2 = Path(mock, obj, [Action("kind", (), {}, obj2)])
        self.assertFalse(path1.matches(path2))

    def test_str(self):
        path = Path(self.mock, [])
        self.assertEquals(str(path), "obj")

    def test_str_unnamed(self):
        mock = Mock(self.mocker)
        path = Path(mock, [])
        self.assertEquals(str(path), "<mock>")

    def test_str_auto_named(self):
        named_mock = Mock(self.mocker)
        named_mock.attr
        path = Path(named_mock, [])
        self.assertEquals(str(path), "named_mock")

    def test_str_getattr(self):
        path = Path(self.mock, None, [Action("getattr", ("attr",), {})])
        self.assertEquals(str(path), "obj.attr")

        path += Action("getattr", ("x",), {})
        self.assertEquals(str(path), "obj.attr.x")

    def test_str_getattr_call(self):
        path = Path(self.mock, None, [Action("getattr", ("x",), {}),
                                      Action("getattr", ("y",), {}),
                                      Action("call", ("z",), {})])
        self.assertEquals(str(path), "obj.x.y('z')")

    def test_str_setattr(self):
        path = Path(self.mock, None,
                    [Action("setattr", ("attr", "value"), {})])
        self.assertEquals(str(path), "obj.attr = 'value'")

    def test_str_delattr(self):
        path = Path(self.mock, None, [Action("delattr", ("attr",), {})])
        self.assertEquals(str(path), "del obj.attr")

    def test_str_call(self):
        path = Path(self.mock, None, [Action("call", (), {})])
        self.assertEquals(str(path), "obj()")

        path = Path(self.mock, None,
                    [Action("call", (1, "2"), {"a": 3, "b": "4"})])
        self.assertEquals(str(path), "obj(1, '2', a=3, b='4')")

    def test_str_contains(self):
        path = Path(self.mock, None, [Action("contains", ("value",), {})])
        self.assertEquals(str(path), "'value' in obj")

    def test_str_getitem(self):
        path = Path(self.mock, None, [Action("getitem", ("key",), {})])
        self.assertEquals(str(path), "obj['key']")

    def test_str_setitem(self):
        path = Path(self.mock, None, [Action("setitem", ("key", "value"), {})])
        self.assertEquals(str(path), "obj['key'] = 'value'")

    def test_str_delitem(self):
        path = Path(self.mock, None, [Action("delitem", ("key",), {})])
        self.assertEquals(str(path), "del obj['key']")

    def test_str_len(self):
        path = Path(self.mock, None, [Action("len", (), {})])
        self.assertEquals(str(path), "len(obj)")

    def test_str_nonzero(self):
        path = Path(self.mock, None, [Action("nonzero", (), {})])
        self.assertEquals(str(path), "bool(obj)")

    def test_str_iter(self):
        path = Path(self.mock, None, [Action("iter", (), {})])
        self.assertEquals(str(path), "iter(obj)")

    def test_str_raises_on_unknown(self):
        path = Path(self.mock, None, [Action("unknown", (), {})])
        self.assertRaises(RuntimeError, str, path)

    def test_execute(self):
        class C(object):
            pass
        obj = C()
        obj.x = C()
        obj.x.y = lambda a, b: a+b
        path = Path(self.mock, None, [Action("getattr", ("x",), {}),
                                      Action("getattr", ("y",), {}),
                                      Action("call", (1,), {"b": 2})])
        self.assertEquals(path.execute(obj), 3)


class MatchParamsTest(TestCase):

    def true(self, *args):
        self.assertTrue(match_params(*args), repr(args))

    def false(self, *args):
        self.assertFalse(match_params(*args), repr(args))
    
    def test_any_repr(self):
        self.assertEquals(repr(ANY), "ANY")

    def test_any_equals(self):
        self.assertEquals(ANY, ANY)
        self.assertNotEquals(ANY, ARGS)
        self.assertNotEquals(ANY, object())

    def test_any_matches(self):
        self.assertTrue(ANY.matches(1))
        self.assertTrue(ANY.matches(42))
        self.assertTrue(ANY.matches(object()))

    def test_is_repr(self):
        self.assertEquals(repr(IS("obj")), "IS('obj')")

    def test_is_equals(self):
        l1 = []
        l2 = []
        self.assertNotEquals(IS(l1), l2)
        self.assertEquals(IS(l1), IS(l1))
        self.assertNotEquals(IS(l1), IS(l2))

    def test_is_matches(self):
        l1 = []
        l2 = []
        self.assertTrue(IS(l1).matches(l1))
        self.assertFalse(IS(l1).matches(l2))
        self.assertFalse(IS(l1).matches(ANY))

    def test_contains_repr(self):
        self.assertEquals(repr(CONTAINS("obj")), "CONTAINS('obj')")

    def test_contains_equals(self):
        self.assertEquals(CONTAINS([1]), CONTAINS([1]))
        self.assertNotEquals(CONTAINS(1), CONTAINS([1]))

    def test_contains_matches(self):
        self.assertTrue(CONTAINS(1).matches([1]))
        self.assertFalse(CONTAINS([1]).matches([1]))
        self.assertFalse(CONTAINS(1).matches(object()))

    def test_contains_matches_with_contains(self):
        """Can't be iterated, but has contains hook."""
        class C(object):
            def __contains__(self, value):
                return True
        self.assertTrue(CONTAINS(1).matches(C()))

    def test_in_repr(self):
        self.assertEquals(repr(IN("obj")), "IN('obj')")

    def test_in_equals(self):
        self.assertEquals(IN([1]), IN([1]))
        self.assertNotEquals(IN([1]), IN(1))

    def test_in_matches(self):
        self.assertTrue(IN([1]).matches(1))
        self.assertFalse(IN([1]).matches([1]))
        self.assertFalse(IN([1]).matches(object()))

    def test_match_repr(self):
        self.assertEquals(repr(MATCH("obj")), "MATCH('obj')")

    def test_match_equals(self):
        obj1, obj2 = [], []
        self.assertEquals(MATCH(obj1), MATCH(obj1))
        self.assertNotEquals(MATCH(obj1), MATCH(obj2))

    def test_match_matches(self):
        self.assertTrue(MATCH(lambda x: x > 10).matches(15))
        self.assertFalse(MATCH(lambda x: x > 10).matches(5))

    def test_normal(self):
        self.true((), {}, (), {})
        self.true((1, 2), {"a": 3}, (1, 2), {"a": 3})
        self.false((1,), {}, (), {})
        self.false((), {}, (1,), {})
        self.false((1, 2), {"a": 3}, (1, 2), {"a": 4})
        self.false((1, 2), {"a": 3}, (1, 3), {"a": 3})

    def test_any(self):
        self.true((1, 2), {"a": ANY}, (1, 2), {"a": 4})
        self.true((1, ANY), {"a": 3}, (1, 3), {"a": 3})
        self.false((ANY,), {}, (), {})

    def test_special_args_matching(self):
        self.true((1, IN([2])), {}, (1, 2), {})
        self.true((1, 2), {"a": IN([3])}, (1, 2), {"a": 3})
        self.false((1, IN([2])), {}, (1, 3), {})
        self.false((1, 2), {"a": IN([3])}, (1, 2), {"a": 4})

    def test_args_alone(self):
        self.true((ARGS,), {}, (), {})
        self.true((ARGS,), {}, (1, 2), {})
        self.false((ARGS,), {}, (1, 2), {"a": 2})
        self.false((ARGS,), {}, (), {"a": 2})
        self.true((ARGS,), {"a": 1}, (), {"a": 1})
        self.true((ARGS,), {"a": 1}, (1, 2), {"a": 1})
        self.false((ARGS,), {"a": 1}, (), {"a": 1, "b": 2})
        self.false((ARGS,), {"a": 1}, (1, 2), {"a": 1, "b": 2})
        self.false((ARGS,), {"a": 1}, (), {})

    def test_kwargs_alone(self):
        self.true((KWARGS,), {}, (), {})
        self.false((KWARGS,), {}, (1, 2), {})
        self.false((KWARGS,), {}, (1, 2), {"a": 2})
        self.true((KWARGS,), {}, (), {"a": 2})
        self.true((KWARGS,), {"a": 1}, (), {"a": 1})
        self.false((KWARGS,), {"a": 1}, (1, 2), {"a": 1})
        self.true((KWARGS,), {"a": 1}, (), {"a": 1, "b": 2})
        self.false((KWARGS,), {"a": 1}, (1, 2), {"a": 1, "b": 2})
        self.false((KWARGS,), {"a": 1}, (), {})

    def test_args_kwargs(self):
        self.true((ARGS, KWARGS), {}, (), {})
        self.true((ARGS, KWARGS), {}, (1, 2), {})
        self.true((ARGS, KWARGS), {}, (1, 2), {"a": 2})
        self.true((ARGS, KWARGS), {}, (), {"a": 2})
        self.true((ARGS, KWARGS), {"a": 1}, (), {"a": 1})
        self.true((ARGS, KWARGS), {"a": 1}, (1, 2), {"a": 1})
        self.true((ARGS, KWARGS), {"a": 1}, (), {"a": 1, "b": 2})
        self.true((ARGS, KWARGS), {"a": 1}, (1, 2), {"a": 1, "b": 2})
        self.false((ARGS, KWARGS), {"a": 1}, (), {})

    def test_args_at_start(self):
        self.true((ARGS, 3, 4), {}, (3, 4), {})
        self.true((ARGS, 3, 4), {}, (1, 2, 3, 4), {})
        self.true((ARGS, 3, 4), {"a": 1}, (3, 4), {"a": 1})
        self.false((ARGS, 3, 4), {"a": 1}, (1, 2, 3, 4), {"a": 1, "b": 2})
        self.false((ARGS, 3, 4), {}, (), {})
        self.false((ARGS, 3, 4), {}, (3, 5), {})
        self.false((ARGS, 3, 4), {}, (5, 5), {})
        self.false((ARGS, 3, 4), {}, (3, 4, 5), {})
        self.false((ARGS, 3, 4), {"a": 1}, (), {})
        self.false((ARGS, 3, 4), {"a": 1}, (3, 4), {})
        self.false((ARGS, 3, 4), {"a": 1}, (3, 4), {"b": 2})

    def test_args_at_end(self):
        self.true((1, 2, ARGS), {}, (1, 2), {})
        self.true((1, 2, ARGS), {}, (1, 2, 3, 4), {})
        self.true((1, 2, ARGS), {"a": 1}, (1, 2), {"a": 1})
        self.false((1, 2, ARGS), {"a": 1}, (1, 2, 3, 4), {"a": 1, "b": 2})
        self.false((1, 2, ARGS), {}, (), {})
        self.false((1, 2, ARGS), {}, (1, 3), {})
        self.false((1, 2, ARGS), {}, (3, 3), {})
        self.false((1, 2, ARGS), {"a": 1}, (), {})
        self.false((1, 2, ARGS), {"a": 1}, (1, 2), {})
        self.false((1, 2, ARGS), {"a": 1}, (1, 2), {"b": 2})

    def test_args_at_middle(self):
        self.true((1, ARGS, 4), {}, (1, 4), {})
        self.true((1, ARGS, 4), {}, (1, 2, 3, 4), {})
        self.true((1, ARGS, 4), {"a": 1}, (1, 4), {"a": 1})
        self.false((1, ARGS, 4), {"a": 1}, (1, 2, 3, 4), {"a": 1, "b": 2})
        self.false((1, ARGS, 4), {}, (), {})
        self.false((1, ARGS, 4), {}, (1, 5), {})
        self.false((1, ARGS, 4), {}, (5, 5), {})
        self.false((1, ARGS, 4), {"a": 1}, (), {})
        self.false((1, ARGS, 4), {"a": 1}, (1, 4), {})
        self.false((1, ARGS, 4), {"a": 1}, (1, 4), {"b": 2})

    def test_args_multiple(self):
        self.true((ARGS, 3, ARGS, 6, ARGS), {},
                  (1, 2, 3, 4, 5, 6), {})
        self.true((ARGS, ARGS, ARGS), {}, (1, 2, 3, 4, 5, 6), {})
        self.true((ARGS, ARGS, ARGS), {},  (), {})
        self.false((ARGS, 3, ARGS, 6, ARGS), {},
                   (1, 2, 3, 4, 5), {})
        self.false((ARGS, 3, ARGS, 6, ARGS), {},
                   (1, 2, 4, 5, 6), {})


class MockTest(TestCase):

    def setUp(self):
        self.paths = []
        class StubMocker(object):
            _recording = True
            def is_recording(self):
                return self._recording
            def replay(self):
                self._recording = False
            def act(_, path):
                self.paths.append(path)
                return 42
        self.StubMocker = StubMocker
        self.mocker = StubMocker()
        self.mock = Mock(self.mocker)

    def test_default_attributes(self):
        self.assertEquals(self.mock.__mocker__, self.mocker)
        self.assertEquals(self.mock.__mocker_path__, Path(self.mock))
        self.assertEquals(self.mock.__mocker_name__, None)
        self.assertEquals(self.mock.__mocker_spec__, None)
        self.assertEquals(self.mock.__mocker_type__, None)
        self.assertEquals(self.mock.__mocker_object__, None)
        self.assertEquals(self.mock.__mocker_passthrough__, False)
        self.assertEquals(self.mock.__mocker_patcher__, None)
        self.assertEquals(self.mock.__mocker_replace__, False)
        self.assertEquals(self.mock.__mocker_count__, True)

    def test_path(self):
        path = object()
        self.assertEquals(Mock(self.mocker, path).__mocker_path__, path)

    def test_object(self):
        mock = Mock(self.mocker, object="foo")
        self.assertEquals(mock.__mocker_object__, "foo")
        self.assertEquals(mock.__mocker_path__.root_object, "foo")

    def test_passthrough(self):
        mock = Mock(self.mocker, object="foo", passthrough=True)
        self.assertEquals(mock.__mocker_object__, "foo")
        self.assertEquals(mock.__mocker_passthrough__, True)

    def test_spec(self):
        C = object()
        self.assertEquals(Mock(self.mocker, spec=C).__mocker_spec__, C)

    def test_class_without_type(self):
        mock = Mock(self.mocker)
        self.assertEquals(mock.__class__, Mock)
        self.mocker.replay()
        self.assertEquals(mock.__class__, Mock)

    def test_class_with_type_when_recording(self):
        class C(object): pass
        mock = Mock(self.mocker, type=C)
        self.assertEquals(mock.__mocker_type__, C)
        self.assertEquals(mock.__class__, Mock)
        self.assertEquals(isinstance(mock, Mock), True)

    def test_class_with_type_when_replaying(self):
        class C(object): pass
        mock = Mock(self.mocker, type=C)
        self.mocker.replay()
        self.assertEquals(mock.__mocker_type__, C)
        self.assertEquals(mock.__class__, C)
        self.assertEquals(isinstance(mock, C), True)

    def test_auto_naming(self):
        named_mock = self.mock
        named_mock.attr
        another_name = named_mock
        named_mock = None # Can't find this one anymore.
        another_name.attr
        self.assertEquals(another_name.__mocker_name__, "named_mock")

    def test_auto_naming_on_self(self):
        self.named_mock = self.mock
        del self.mock
        self.named_mock.attr
        self.assertEquals(self.named_mock.__mocker_name__, "named_mock")

    def test_auto_naming_on_bad_self(self):
        self_ = self
        self = object() # No __dict__
        self_.named_mock = self_.mock
        self_.named_mock.attr
        self_.assertEquals(self_.named_mock.__mocker_name__, None)

    def test_auto_naming_without_getframe(self):
        getframe = sys._getframe
        sys._getframe = None
        try:
            self.named_mock = self.mock
            self.named_mock.attr
            self.assertEquals(self.named_mock.__mocker_name__, None)
        finally:
            sys._getframe = getframe

    def test_getattr(self):
        self.assertEquals(self.mock.attr, 42)
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("getattr", ("attr",), {}))

    def test_setattr(self):
        self.mock.attr = 24
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("setattr", ("attr", 24), {}))

    def test_delattr(self):
        del self.mock.attr
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("delattr", ("attr",), {}))

    def test_call(self):
        self.mock(1, a=2)
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("call", (1,), {"a": 2}))

    def test_contains(self):
        self.assertEquals("value" in self.mock, True) # True due to 42.
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("contains", ("value",), {}))

    def test_getitem(self):
        self.assertEquals(self.mock["key"], 42)
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("getitem", ("key",), {}))

    def test_setitem(self):
        self.mock["key"] = "value"
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("setitem", ("key", "value"), {}))

    def test_delitem(self):
        del self.mock["key"]
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("delitem", ("key",), {}))

    def test_len(self):
        self.assertEquals(len(self.mock), 42)
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("len", (), {}))

    def test_len_with_mock_result(self):
        self.mocker.act = lambda path: Mock(self.mocker)
        self.assertEquals(len(self.mock), 0)

    def test_len_transforms_match_error_to_attribute_error(self):
        """
        list() uses len() as a hint. When we mock iter(), it shouldn't
        explode due to the lack of len().
        """
        def raise_error(path):
            raise MatchError("Kaboom!")

        self.mocker.act = raise_error
        try:
            len(self.mock)
        except AttributeError, e:
            self.assertEquals(str(e), "Kaboom!")
        except MatchError:
            self.fail("Expected AttributeError, not MatchError.")
        else:
            self.fail("AttributeError not raised.")

    def test_nonzero(self):
        self.assertEquals(bool(self.mock), True) # True due to 42.
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("nonzero", (), {}))

    def test_nonzero_returns_true_on_match_error(self):
        """
        When an object doesn't define a boolean behavior explicitly, it
        should be handled as a true value by default, as Python usually
        does.
        """
        def raise_error(path):
            raise MatchError("Kaboom!")
        self.mocker.act = raise_error
        self.assertEquals(bool(self.mock), True)

    def test_iter(self):
        result_mock = Mock(self.mocker)
        self.mocker.act = lambda path: self.paths.append(path) or result_mock
        result = iter(self.mock)
        self.assertEquals(type(result), type(iter([])))
        self.assertEquals(list(result), [])
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertEquals(path, self.mock.__mocker_path__ + 
                                Action("iter", (), {}))

    def test_passthrough_on_unexpected(self):
        class StubMocker(object):
            def act(self, path):
                if path.actions[-1].args == ("x",):
                    raise MatchError
                return 42
        class C(object):
            x = 123
            y = 321

        mock = Mock(StubMocker(), object=C())
        self.assertRaises(MatchError, getattr, mock, "x", 42)
        self.assertEquals(mock.y, 42)

        mock = Mock(StubMocker(), passthrough=True)
        self.assertRaises(MatchError, getattr, mock, "x", 42)
        self.assertEquals(mock.y, 42)

        mock = Mock(StubMocker(), object=C(), passthrough=True)
        self.assertEquals(mock.x, 123)
        self.assertEquals(mock.y, 42)

        mock = Mock(StubMocker(), passthrough=True)
        act = mock.__mocker_act__
        self.assertEquals(act("getattr", ("x",), 42, object=C()), 123)
        self.assertEquals(act("getattr", ("y",), 42, object=C()), 42)

    def test_act_with_object(self):
        obj = object()
        self.mock.__mocker_act__("kind", object=obj)
        (path,) = self.paths
        self.assertEquals(type(path), Path)
        self.assertTrue(path.parent_path is self.mock.__mocker_path__)
        self.assertTrue(path.root_object is obj)

    def test_reraise_assertion(self):
        class StubMocker(object):
            def act(self, path):
                message = os.linesep.join(["An", "- error", "- happened"])
                raise AssertionError(message)
        mock = Mock(StubMocker())
        try:
            mock.__mocker_act__("kind")
        except AssertionError, e:
            message = os.linesep.join(["[Mocker] Unmet expectation:",
                                       "",
                                       "=> An",
                                       " - error",
                                       " - happened",
                                       ""])
            self.assertEquals(str(e), message)
        else:
            self.fail("AssertionError not raised")

    def test_action_execute_and_path_str(self):
        """Check for kind support on Action.execute() and Path.__str__()."""
        mocker = Mocker()
        check = []
        for name, attr in Mock.__dict__.iteritems():
            if not name.startswith("__mocker_") and hasattr(attr, "__call__"):
                mock = mocker.mock()
                args = ["arg"] * (attr.func_code.co_argcount - 1)
                try:
                    attr(mock, *args)
                except:
                    pass
                else:
                    path = mocker.get_events()[-1].path
                    check.append((path, path.actions[-1]))

        for path, action in check:
            kind = action.kind

            try:
                str(path)
            except RuntimeError:
                self.fail("Kind %r not supported by Path.__str__()" % kind)

            try:
                action.execute(object())
            except RuntimeError:
                self.fail("Kind %r not supported by Action.execute()" % kind)
            except:
                pass


class EventTest(TestCase):

    def setUp(self):
        self.event = Event()

    def test_default_path(self):
        self.assertEquals(self.event.path, None)

    def test_path(self):
        path = object()
        event = Event(path)
        self.assertEquals(event.path, path)

    def test_add_and_get_tasks(self):
        task1 = self.event.add_task(Task())
        task2 = self.event.add_task(Task())
        self.assertEquals(self.event.get_tasks(), [task1, task2])

    def test_remove_task(self):
        task1 = self.event.add_task(Task())
        task2 = self.event.add_task(Task())
        task3 = self.event.add_task(Task())
        self.event.remove_task(task2)
        self.assertEquals(self.event.get_tasks(), [task1, task3])

    def test_default_matches(self):
        self.assertEquals(self.event.matches(None), False)

    def test_default_run(self):
        self.assertEquals(self.event.run(None), None)

    def test_default_satisfied(self):
        self.assertEquals(self.event.satisfied(), True)

    def test_default_verify(self):
        self.assertEquals(self.event.verify(), None)

    def test_default_replay(self):
        self.assertEquals(self.event.replay(), None)

    def test_default_restore(self):
        self.assertEquals(self.event.restore(), None)

    def test_matches_false(self):
        task1 = self.event.add_task(Task())
        task1.matches = lambda path: True
        task2 = self.event.add_task(Task())
        task2.matches = lambda path: False
        task3 = self.event.add_task(Task())
        task3.matches = lambda path: True
        self.assertEquals(self.event.matches(None), False)

    def test_matches_true(self):
        task1 = self.event.add_task(Task())
        task1.matches = lambda path: True
        task2 = self.event.add_task(Task())
        task2.matches = lambda path: True
        self.assertEquals(self.event.matches(None), True)

    def test_matches_argument(self):
        calls = []
        task = self.event.add_task(Task())
        task.matches = lambda path: calls.append(path)
        self.event.matches(42)
        self.assertEquals(calls, [42])

    def test_run(self):
        calls = []
        task1 = self.event.add_task(Task())
        task1.run = lambda path: calls.append(path) or True
        task2 = self.event.add_task(Task())
        task2.run = lambda path: calls.append(path) or False
        task3 = self.event.add_task(Task())
        task3.run = lambda path: calls.append(path) or None
        self.assertEquals(self.event.run(42), False)
        self.assertEquals(calls, [42, 42, 42])

    def test_run_errors(self):
        class MyTask(object):
            def __init__(self, id, failed):
                self.id = id
                self.failed = failed
            def run(self, path):
                if self.failed:
                    raise AssertionError("%d failed" % self.id)
        event = Event("i.am.a.path")
        event.add_task(MyTask(1, True))
        event.add_task(MyTask(2, False))
        event.add_task(MyTask(3, True))

        try:
            event.run("i.am.a.path")
        except AssertionError, e:
            message = os.linesep.join(["i.am.a.path",
                                       "- 1 failed",
                                       "- 3 failed"])
            self.assertEquals(str(e), message)
        else:
            self.fail("AssertionError not raised")

    def test_run_errors_with_different_path_representation(self):
        """When the path representation isn't the same it's shown up."""
        class MyTask(object):
            def __init__(self, id, failed):
                self.id = id
                self.failed = failed
            def run(self, path):
                if self.failed:
                    raise AssertionError("%d failed" % self.id)
        event = Event("i.am.a.path")
        event.add_task(MyTask(1, True))
        event.add_task(MyTask(2, False))
        event.add_task(MyTask(3, True))

        try:
            event.run(42)
        except AssertionError, e:
            message = os.linesep.join(["i.am.a.path",
                                       "- Run: 42", # <==
                                       "- 1 failed",
                                       "- 3 failed"])
            self.assertEquals(str(e), message)
        else:
            self.fail("AssertionError not raised")

    def test_run_errors_need_good_messages(self):
        class MyTask(Task):
            def run(self, path):
                raise AssertionError()
        self.event.add_task(MyTask())
        self.assertRaises(RuntimeError, self.event.run, 42)

    def test_has_run(self):
        self.assertFalse(self.event.has_run())
        self.event.run(None)
        self.assertTrue(self.event.has_run())

    def test_has_run_reset_on_replay(self):
        self.event.run(None)
        self.event.replay()
        self.assertFalse(self.event.has_run())

    def test_may_run(self):
        calls = []
        task1 = Task()
        task1.may_run = lambda path: calls.append((1, path)) or True
        task2 = Task()
        task2.may_run = lambda path: calls.append((2, path))

        self.assertEquals(self.event.may_run(42), True)

        self.event.add_task(task1)
        self.assertEquals(self.event.may_run(42), True)
        self.assertEquals(calls, [(1, 42)])

        del calls[:]
        self.event.add_task(task2)
        self.event.add_task(task1) # Should return on first false.
        self.assertEquals(self.event.may_run(42), False)
        self.assertEquals(calls, [(1, 42), (2, 42)])

    def test_satisfied_false(self):
        def raise_error():
            raise AssertionError("An error")
        task1 = self.event.add_task(Task())
        task2 = self.event.add_task(Task())
        task2.verify = raise_error
        task3 = self.event.add_task(Task())
        self.assertEquals(self.event.satisfied(), False)

    def test_satisfied_true(self):
        task1 = self.event.add_task(Task())
        task1.satisfied = lambda: True
        task2 = self.event.add_task(Task())
        task2.satisfied = lambda: True
        self.assertEquals(self.event.satisfied(), True)

    def test_verify(self):
        class MyTask(object):
            def __init__(self, id, failed):
                self.id = id
                self.failed = failed
            def verify(self):
                if self.failed:
                    raise AssertionError("%d failed" % self.id)
        event = Event("i.am.a.path")
        event.add_task(MyTask(1, True))
        event.add_task(MyTask(2, False))
        event.add_task(MyTask(3, True))

        try:
            event.verify()
        except AssertionError, e:
            message = os.linesep.join(["i.am.a.path",
                                       "- 1 failed",
                                       "- 3 failed"])
            self.assertEquals(str(e), message)
        else:
            self.fail("AssertionError not raised")

    def test_verify_errors_need_good_messages(self):
        class MyTask(Task):
            def verify(self):
                raise AssertionError()
        self.event.add_task(MyTask())
        self.assertRaises(RuntimeError, self.event.verify)

    def test_replay(self):
        calls = []
        task1 = self.event.add_task(Task())
        task2 = self.event.add_task(Task())
        task1.replay = lambda: calls.append("task1")
        task2.replay = lambda: calls.append("task2")
        self.event.replay()
        self.assertEquals(calls, ["task1", "task2"])

    def test_restore(self):
        calls = []
        task1 = self.event.add_task(Task())
        task2 = self.event.add_task(Task())
        task1.restore = lambda: calls.append("task1")
        task2.restore = lambda: calls.append("task2")
        self.event.restore()
        self.assertEquals(calls, ["task1", "task2"])


class ReplayRestoreEventTest(TestCase):

    def setUp(self):
        self.event = ReplayRestoreEvent()

    def test_never_matches(self):
        self.assertEquals(self.event.matches(None), False)
        self.event.add_task(Task())
        self.assertEquals(self.event.matches(None), False)


class TaskTest(TestCase):

    def setUp(self):
        self.task = Task()

    def test_default_matches(self):
        self.assertEquals(self.task.matches(None), True)

    def test_default_may_run(self):
        self.assertEquals(self.task.may_run(None), True)

    def test_default_run(self):
        self.assertEquals(self.task.run(None), None)

    def test_default_verify(self):
        self.assertEquals(self.task.verify(), None)

    def test_default_replay(self):
        self.assertEquals(self.task.replay(), None)

    def test_default_restore(self):
        self.assertEquals(self.task.restore(), None)


class OnRestoreCallerTest(TestCase):

    def setUp(self):
        self.mocker = CleanMocker()
        self.mock = self.mocker.mock()

    def test_is_task(self):
        self.assertTrue(isinstance(OnRestoreCaller(None), Task))

    def test_restore(self):
        calls = []
        task = OnRestoreCaller(lambda: calls.append("callback"))
        self.assertEquals(calls, [])
        task.restore()
        self.assertEquals(calls, ["callback"])
        task.restore()
        self.assertEquals(calls, ["callback", "callback"])


class PathMatcherTest(TestCase):

    def setUp(self):
        self.mocker = CleanMocker()
        self.mock = self.mocker.mock()

    def test_is_task(self):
        self.assertTrue(isinstance(PathMatcher(None), Task))

    def test_create(self):
        path = object()
        task = PathMatcher(path)
        self.assertEquals(task.path, path)

    def test_matches(self):
        path = Path(self.mock, None, [Action("getattr", ("attr1",), {})])
        task = PathMatcher(path)
        action = Action("getattr", (), {}, Path(self.mock))
        self.assertFalse(task.matches(action.path + action))
        action = Action("getattr", ("attr1",), {}, Path(self.mock))
        self.assertTrue(task.matches(action.path + action))

    def test_recorder(self):
        path = Path(self.mock, [Action("call", (), {})])
        event = Event(path)
        path_matcher_recorder(self.mocker, event)
        (task,) = event.get_tasks()
        self.assertEquals(type(task), PathMatcher)
        self.assertTrue(task.path is path)

    def test_is_standard_recorder(self):
        self.assertTrue(path_matcher_recorder in Mocker.get_recorders())


class RunCounterTest(TestCase):

    def setUp(self):
        self.mocker = CleanMocker()
        self.mock = self.mocker.mock()
        self.action = Action("getattr", ("attr",), {}, Path(self.mock))
        self.path = Path(self.mock, [self.action])
        self.event = Event(self.path)

    def test_is_task(self):
        self.assertTrue(isinstance(RunCounter(1), Task))

    def test_create_one_argument(self):
        task = RunCounter(2)
        self.assertEquals(task.min, 2)
        self.assertEquals(task.max, 2)

    def test_create_min_max(self):
        task = RunCounter(2, 3)
        self.assertEquals(task.min, 2)
        self.assertEquals(task.max, 3)

    def test_create_unbounded(self):
        task = RunCounter(2, None)
        self.assertEquals(task.min, 2)
        self.assertEquals(task.max, sys.maxint)

    def test_run_one_argument(self):
        task = RunCounter(2)
        task.run(self.path)
        task.run(self.path)
        self.assertRaises(AssertionError, task.run, self.path)

    def test_run_two_arguments(self):
        task = RunCounter(1, 2)
        task.run(self.path)
        task.run(self.path)
        self.assertRaises(AssertionError, task.run, self.path)

    def test_may_run(self):
        task = RunCounter(1)
        self.assertEquals(task.may_run(None), True)
        task.run(self.path)
        self.assertEquals(task.may_run(None), False)

    def test_verify(self):
        task = RunCounter(2)
        self.assertRaises(AssertionError, task.verify)
        task.run(self.path)
        self.assertRaises(AssertionError, task.verify)
        task.run(self.path)
        task.verify()
        self.assertRaises(AssertionError, task.run, self.path)
        self.assertRaises(AssertionError, task.verify)

    def test_verify_two_arguments(self):
        task = RunCounter(1, 2)
        self.assertRaises(AssertionError, task.verify)
        task.run(self.path)
        task.verify()
        task.run(self.path)
        task.verify()
        self.assertRaises(AssertionError, task.run, self.path)
        self.assertRaises(AssertionError, task.verify)

    def test_verify_unbound(self):
        task = RunCounter(1, None)
        self.assertRaises(AssertionError, task.verify)
        task.run(self.path)
        task.verify()
        task.run(self.path)
        task.verify()

    def test_reset_on_replay(self):
        task = RunCounter(1, 1)
        task.run(self.path)
        self.assertRaises(AssertionError, task.run, self.path)
        task.replay()
        self.assertRaises(AssertionError, task.verify)
        task.run(self.path)
        self.assertRaises(AssertionError, task.run, self.path)

    def test_recorder(self):
        run_counter_recorder(self.mocker, self.event)
        (task,) = self.event.get_tasks()
        self.assertEquals(type(task), ImplicitRunCounter)
        self.assertTrue(task.min == 1)
        self.assertTrue(task.max == 1)

    def test_recorder_wont_record_when_count_is_false(self):
        self.mock.__mocker_count__ = False
        run_counter_recorder(self.mocker, self.event)
        self.assertEquals(self.event.get_tasks(), [])

    def test_removal_recorder(self):
        """
        Events created by getattr actions which lead to other events
        may be repeated any number of times.
        """
        path1 = Path(self.mock)
        path2 = path1 + Action("getattr", ("attr",), {}, path1)
        path3 = path2 + Action("getattr", ("attr",), {}, path2)
        path4 = path3 + Action("call", (), {}, path3)
        path5 = path4 + Action("call", (), {}, path4)

        event3 = self.mocker.add_event(Event(path3))
        event2 = self.mocker.add_event(Event(path2))
        event5 = self.mocker.add_event(Event(path5))
        event4 = self.mocker.add_event(Event(path4))

        event2.add_task(RunCounter(1))
        event2.add_task(ImplicitRunCounter(1))
        event2.add_task(RunCounter(1))
        event3.add_task(RunCounter(1))
        event3.add_task(ImplicitRunCounter(1))
        event3.add_task(RunCounter(1))
        event4.add_task(RunCounter(1))
        event4.add_task(ImplicitRunCounter(1))
        event4.add_task(RunCounter(1))
        event5.add_task(RunCounter(1))
        event5.add_task(ImplicitRunCounter(1))
        event5.add_task(RunCounter(1))
        
        # First, when the previous event isn't a getattr.

        run_counter_removal_recorder(self.mocker, event5)

        self.assertEquals(len(event2.get_tasks()), 3)
        self.assertEquals(len(event3.get_tasks()), 3)
        self.assertEquals(len(event4.get_tasks()), 3)
        self.assertEquals(len(event5.get_tasks()), 3)

        # Now, for real.

        run_counter_removal_recorder(self.mocker, event4)

        self.assertEquals(len(event2.get_tasks()), 3)
        self.assertEquals(len(event3.get_tasks()), 2)
        self.assertEquals(len(event4.get_tasks()), 3)
        self.assertEquals(len(event5.get_tasks()), 3)

        task1, task2 = event3.get_tasks()
        self.assertEquals(type(task1), RunCounter)
        self.assertEquals(type(task2), RunCounter)

    def test_removal_recorder_with_obj(self):

        self.mocker.add_recorder(run_counter_recorder)
        self.mocker.add_recorder(run_counter_removal_recorder)

        obj = self.mocker.mock()

        obj.x.y()()

        events = self.mocker.get_events()
        self.assertEquals(len(events), 4)
        self.assertEquals(len(events[0].get_tasks()), 0)
        self.assertEquals(len(events[1].get_tasks()), 0)
        self.assertEquals(len(events[2].get_tasks()), 1)
        self.assertEquals(len(events[3].get_tasks()), 1)

    def test_reset_on_replay_with_mock(self):
        mock = self.mocker.mock()
        mock()
        self.mocker.count(1)
        self.mocker.replay()
        mock()
        self.assertRaises(AssertionError, mock)
        self.mocker.replay()
        mock()
        self.assertRaises(AssertionError, mock)

    def test_is_standard_recorder(self):
        self.assertTrue(run_counter_recorder in Mocker.get_recorders())
        self.assertTrue(run_counter_removal_recorder in Mocker.get_recorders())


class MockReturnerTest(TestCase):

    def setUp(self):
        self.mocker = CleanMocker()
        self.mock = self.mocker.mock()
        self.action = Action("getattr", ("attr",), {}, Path(self.mock))
        self.path = Path(self.mock, [self.action])
        self.event = Event(self.path)

    def test_is_task(self):
        self.assertTrue(isinstance(MockReturner(self.mocker), Task))

    def test_create(self):
        task = MockReturner(self.mocker)
        mock = task.run(self.path)
        self.assertTrue(isinstance(mock, Mock))
        self.assertEquals(mock.__mocker__, self.mocker)
        self.assertTrue(mock.__mocker_path__.matches(self.path))

    def test_recorder(self):
        path1 = Path(self.mock)
        path2 = path1 + Action("getattr", ("attr",), {}, path1)
        path3 = path2 + Action("getattr", ("attr",), {}, path2)
        path4 = path3 + Action("call", (), {}, path3)

        event2 = self.mocker.add_event(Event(path2))
        event3 = self.mocker.add_event(Event(path3))
        event4 = self.mocker.add_event(Event(path4))

        self.assertEquals(len(event2.get_tasks()), 0)
        self.assertEquals(len(event3.get_tasks()), 0)
        self.assertEquals(len(event4.get_tasks()), 0)

        # Calling on 4 should add it only to the parent.

        mock_returner_recorder(self.mocker, event4)

        self.assertEquals(len(event2.get_tasks()), 0)
        self.assertEquals(len(event3.get_tasks()), 1)
        self.assertEquals(len(event4.get_tasks()), 0)

        (task,) = event3.get_tasks()
        self.assertEquals(type(task), MockReturner)
        self.assertEquals(task.mocker, self.mocker)

        # Calling on it again shouldn't do anything.

        mock_returner_recorder(self.mocker, event4)

        self.assertEquals(len(event2.get_tasks()), 0)
        self.assertEquals(len(event3.get_tasks()), 1)
        self.assertEquals(len(event4.get_tasks()), 0)

    def test_is_standard_recorder(self):
        self.assertTrue(mock_returner_recorder in Mocker.get_recorders())


class FunctionRunnerTest(TestCase):

    def setUp(self):
        self.mocker = CleanMocker()
        self.mock = self.mocker.mock()
        self.action = Action("call", (1, 2), {"c": 3}, Path(self.mock))
        self.path = Path(self.mock, None, [self.action])
        self.event = Event(self.path)

    def test_is_task(self):
        self.assertTrue(isinstance(FunctionRunner(None), Task))

    def test_run(self):
        task = FunctionRunner(lambda *args, **kwargs: repr((args, kwargs)))
        result = task.run(self.path)
        self.assertEquals(result, "((1, 2), {'c': 3})")


class PathExecuterTest(TestCase):

    def setUp(self):
        self.mocker = CleanMocker()

    def test_is_task(self):
        self.assertTrue(isinstance(PathExecuter(), Task))

    def test_run(self):
        class C(object):
            pass
        obj = C()
        obj.x = C()
        obj.x.y = lambda a, b: a+b

        path = Path(None, obj, [Action("getattr", ("x",), {}),
                                Action("getattr", ("y",), {}),
                                Action("call", (1,), {"b": 2})])

        task = PathExecuter()
        self.assertEquals(task.run(path), 3)

    def test_run_with_result_callback(self):
        class C(object):
            def x(self, arg):
                return 41 + arg
        obj = C()

        path = Path(None, obj, [Action("getattr", ("x",), {}),
                                Action("call", (1,), {})])

        calls = []
        result_callback = lambda result: calls.append(result)
        task = PathExecuter(result_callback)
        self.assertEquals(task.get_result_callback(), result_callback)
        self.assertEquals(task.run(path), 42)
        self.assertEquals(calls, [42])


class OrdererTest(TestCase):

    def setUp(self):
        self.mocker = CleanMocker()
        self.mock = self.mocker.mock()
        self.action = Action("call", (1, 2, Path(self.mock)), {"c": 3})
        self.path = Path(self.mock, [self.action])

    def test_is_task(self):
        self.assertTrue(isinstance(Orderer(self.path), Task))

    def test_path(self):
        self.assertEquals(Orderer(self.path).path, self.path)

    def test_has_run(self):
        orderer = Orderer(self.path)
        self.assertFalse(orderer.has_run())
        orderer.run(self.path)
        self.assertTrue(orderer.has_run())

    def test_reset_on_replay(self):
        orderer = Orderer(self.path)
        orderer.run(self.path)
        orderer.replay()
        self.assertFalse(orderer.has_run())

    def test_reset_on_replay_with_mock(self):
        self.mocker.add_recorder(path_matcher_recorder)
        mock = self.mocker.mock()
        self.mocker.order(mock(1), mock(2))
        self.mocker.replay()
        mock(1)
        mock(2)
        self.mocker.replay()
        self.assertRaises(AssertionError, mock, 2)

    def test_add_and_get_dependencies(self):
        orderer = Orderer(self.path)
        orderer.add_dependency(1)
        orderer.add_dependency(2)
        self.assertEquals(orderer.get_dependencies(), [1, 2])

    def test_may_run(self):
        orderer1 = Orderer(self.path)
        orderer2 = Orderer(self.path)
        orderer2.add_dependency(orderer1)
        self.assertFalse(orderer2.may_run(None))
        self.assertTrue(orderer1.may_run(None))
        orderer1.run(self.path)
        self.assertTrue(orderer2.may_run(None))

    def test_run_with_missing_dependency(self):
        orderer1 = Orderer("path1")
        orderer2 = Orderer("path2")
        orderer2.add_dependency(orderer1)
        try:
            orderer2.run(None)
        except AssertionError, e:
            self.assertEquals(str(e), "Should be after: path1")
        else:
            self.fail("AssertionError not raised")


class SpecCheckerTest(TestCase):

    def setUp(self):
        class C(object):
            def __call__(self, a, b, c=3): pass
            def normal(self, a, b, c=3): pass
            def varargs(self, a, b, c=3, *args): pass
            def varkwargs(self, a, b, c=3, **kwargs): pass
            def varargskwargs(self, a, b, c=3, *args, **kwargs): pass
            def klass(cls, a, b, c=3): pass
            klass = classmethod(klass)
            def static(a, b, c=3): pass
            static = staticmethod(static)
            def noargs(self): pass
            def klassnoargs(cls): pass
            klassnoargs = classmethod(klassnoargs)
            def staticnoargs(): pass
            staticnoargs = staticmethod(staticnoargs)
        self.cls = C
        self.mocker = CleanMocker()
        self.mock = self.mocker.mock(self.cls)

    def path(self, *args, **kwargs):
        action = Action("call", args, kwargs, Path(self.mock))
        return action.path + action

    def good(self, method_names, args_expr):
        if type(method_names) is not list:
            method_names = [method_names]
        for method_name in method_names:
            task = SpecChecker(getattr(self.cls, method_name, None))
            path = eval("self.path(%s)" % args_expr)
            self.assertEquals(task.may_run(path), True)
            try:
                task.run(path)
            except AssertionError:
                self.fail("AssertionError raised with self.cls.%s(%s)"
                          % (method_name, args_expr))

    def bad(self, method_names, args_expr):
        if type(method_names) is not list:
            method_names = [method_names]
        for method_name in method_names:
            task = SpecChecker(getattr(self.cls, method_name, None))
            path = eval("self.path(%s)" % args_expr)
            self.assertEquals(task.may_run(path), False)
            try:
                task.run(path)
            except AssertionError:
                pass
            else:
                self.fail("AssertionError not raised with self.cls.%s(%s)"
                          % (method_name, args_expr))

    def test_get_method(self):
        task = SpecChecker(self.cls.noargs)
        self.assertEquals(task.get_method(), self.cls.noargs)

    def test_is_standard_recorder(self):
        self.assertTrue(spec_checker_recorder in Mocker.get_recorders())

    def test_is_task(self):
        self.assertTrue(isinstance(SpecChecker(self.cls.normal), Task))

    def test_error_message(self):
        task = SpecChecker(self.cls.normal)
        try:
            task.run(self.path(1))
        except AssertionError, e:
            self.assertEquals(str(e), "Specification is normal(a, b, c=3): "
                                      "'b' not provided")
        else:
            self.fail("AssertionError not raised")

    def test_verify_unexistent_method(self):
        task = SpecChecker(None)
        try:
            task.verify()
        except AssertionError, e:
            self.assertEquals(str(e), "Method not found in real specification")
        else:
            self.fail("AssertionError not raised")

    def test_unsupported_object_for_getargspec(self):
        from zlib import adler32
        # If that fails, this test has to change because either adler32 has
        # changed, or the implementation of getargspec has changed.
        self.assertRaises(TypeError, inspect.getargspec, adler32)
        try:
            task = SpecChecker(adler32)
            task.run(self.path("asd"))
        except TypeError, e:
            self.fail("TypeError: %s" % str(e))

    def test_recorder(self):
        self.mocker.add_recorder(spec_checker_recorder)
        obj = self.mocker.mock(spec=self.cls)
        obj.noargs()
        getattr, call = self.mocker.get_events()
        self.assertEquals(getattr.get_tasks(), [])
        (task,) = call.get_tasks()
        self.assertEquals(type(task), SpecChecker)
        self.assertEquals(task.get_method(), self.cls.noargs)

    def test_recorder_with_unexistent_method(self):
        self.mocker.add_recorder(spec_checker_recorder)
        obj = self.mocker.mock(spec=self.cls)
        obj.unexistent()
        getattr, call = self.mocker.get_events()
        self.assertEquals(getattr.get_tasks(), [])
        (task,) = call.get_tasks()
        self.assertEquals(type(task), SpecChecker)
        self.assertEquals(task.get_method(), None)

    def test_recorder_second_action_isnt_call(self):
        self.mocker.add_recorder(spec_checker_recorder)
        obj = self.mocker.mock(spec=self.cls)
        obj.noargs.x
        event1, event2 = self.mocker.get_events()
        self.assertEquals(event1.get_tasks(), [])
        self.assertEquals(event2.get_tasks(), [])

    def test_recorder_first_action_isnt_getattr(self):
        self.mocker.add_recorder(spec_checker_recorder)
        obj = self.mocker.mock(spec=self.cls)
        obj.__mocker_act__("anyother", ("attr",))()
        event1, event2 = self.mocker.get_events()
        self.assertEquals(event1.get_tasks(), [])
        self.assertEquals(event2.get_tasks(), [])

    def test_recorder_more_than_two_actions(self):
        self.mocker.add_recorder(spec_checker_recorder)
        obj = self.mocker.mock(spec=self.cls)
        obj.noargs().x
        event1, event2, event3 = self.mocker.get_events()
        self.assertEquals(len(event1.get_tasks()), 0)
        self.assertEquals(len(event2.get_tasks()), 1)
        self.assertEquals(len(event3.get_tasks()), 0)

    def test_recorder_with_call_on_object(self):
        self.mocker.add_recorder(spec_checker_recorder)
        obj = self.mocker.mock(spec=self.cls)
        obj()
        (call,) = self.mocker.get_events()
        (task,) = call.get_tasks()
        self.assertEquals(type(task), SpecChecker)
        self.assertEquals(task.get_method(), self.cls.__call__)

    def test_recorder_more_than_one_action_with_direct_call(self):
        self.mocker.add_recorder(spec_checker_recorder)
        obj = self.mocker.mock(spec=self.cls)
        obj().x
        event1, event2 = self.mocker.get_events()
        self.assertEquals(len(event1.get_tasks()), 1)
        self.assertEquals(len(event2.get_tasks()), 0)

    def test_noargs(self):
        methods = ["noargs", "klassnoargs", "staticnoargs"]
        self.good(methods, "")
        self.bad(methods, "1")
        self.bad(methods, "a=1")

    def test_args_and_kwargs(self):
        methods = ["__call__", "normal", "varargs", "varkwargs",
                   "varargskwargs", "static", "klass"]
        self.good(methods, "1, 2")
        self.good(methods, "1, 2, 3")
        self.good(methods, "1, b=2")
        self.good(methods, "1, b=2, c=3")
        self.good(methods, "a=1, b=2")
        self.good(methods, "a=1, b=2, c=3")

    def test_too_much(self):
        methods = ["__call__", "normal", "static", "klass"]
        self.bad(methods, "1, 2, 3, 4")
        self.bad(methods, "1, 2, d=4")

    def test_missing(self):
        methods = ["__call__", "normal", "varargs", "varkwargs",
                   "varargskwargs", "static", "klass"]
        self.bad(methods, "")
        self.bad(methods, "1")
        self.bad(methods, "c=3")
        self.bad(methods, "a=1")
        self.bad(methods, "b=2, c=3")

    def test_duplicated_argument(self):
        methods = ["__call__", "normal", "varargs", "varkwargs",
                   "varargskwargs", "static", "klass"]
        self.bad(methods, "1, 2, b=2")

    def test_varargs(self):
        self.good("varargs", "1, 2, 3, 4")
        self.bad("varargs", "1, 2, 3, 4, d=3")

    def test_varkwargs(self):
        self.good("varkwargs", "1, 2, d=3")
        self.bad("varkwargs", "1, 2, 3, 4, d=3")

    def test_varargskwargs(self):
        self.good("varargskwargs", "1, 2, 3, 4, d=3")

    def test_unexistent(self):
        self.bad("unexistent", "")


class ProxyReplacerTest(TestCase):

    def setUp(self):
        self.mocker = CleanMocker()
        import calendar
        self.mock = Mock(self.mocker, object=calendar)
        self.task = ProxyReplacer(self.mock)

    def tearDown(self):
        self.task.restore()

    def test_is_task(self):
        self.assertTrue(isinstance(ProxyReplacer(None), Task))

    def test_mock(self):
        mock = object()
        task = ProxyReplacer(mock)
        self.assertEquals(task.mock, mock)

    def test_defaults_to_not_installed(self):
        import calendar
        self.assertEquals(type(calendar), ModuleType)

    def test_install(self):
        self.task.replay()
        import calendar
        self.assertEquals(type(calendar), Mock)
        self.assertTrue(calendar is self.mock)

    def test_install_protects_mock(self):
        self.task.replay()
        self.assertEquals(type(self.mock.__mocker_object__), ModuleType)

    def test_install_protects_path(self):
        self.task.replay()
        self.assertEquals(type(self.mock.__mocker_path__.root_object),
                          ModuleType)

    def test_deinstall_protects_task(self):
        self.task.replay()
        self.task.restore()
        self.assertEquals(type(self.task.mock), Mock)

    def test_install_protects_anything_with_mocker_replace_false(self):
        class C(object):
            def __init__(self):
                import calendar
                self.calendar = calendar
                self.__mocker_replace__ = False
        obj = C()
        self.task.replay()
        self.assertEquals(type(self.mock.__mocker_path__.root_object),
                          ModuleType)

    def test_install_on_object(self):
        class C(object):
            def __init__(self):
                import calendar
                self.calendar = calendar
        obj = C()
        self.task.replay()
        self.assertEquals(type(obj.calendar), Mock)
        self.assertTrue(obj.calendar is self.mock)

    def test_install_on_submodule(self):
        from os import path
        import os
        mock = Mock(self.mocker, object=path)
        task = ProxyReplacer(mock)
        task.replay()
        try:
            self.assertEquals(type(os.path), Mock)
            self.assertTrue(os.path is mock)
        finally:
            task.restore()

    def test_uninstall_on_restore(self):
        self.task.replay()
        self.task.restore()
        import calendar
        self.assertEquals(type(calendar), ModuleType)
        self.assertEquals(calendar.__name__, "calendar")

    def test_uninstall_from_object(self):
        class C(object):
            def __init__(self):
                import calendar
                self.calendar = calendar
        obj = C()
        self.task.replay()
        self.task.restore()
        self.assertEquals(type(obj.calendar), ModuleType)
        self.assertEquals(obj.calendar.__name__, "calendar")

    def test_uninstall_from_submodule(self):
        from os import path
        import os
        mock = Mock(self.mocker, object=path)
        task = ProxyReplacer(mock)
        self.assertEquals(type(os.path), ModuleType)
        task.replay()
        task.restore()
        self.assertEquals(type(os.path), ModuleType)


class PatcherTest(TestCase):

    def setUp(self):
        self.mocker = Mocker()
        self.patcher = Patcher()
        self.C = type("C", (object,), {})
        self.D = type("D", (self.C,), {})
        self.E = type("E", (), {})

        class MockStub(object):
            def __mocker_act__(self, kind, args=(), kwargs={}, object=None):
                return (kind, args, kwargs, object)

        self.MockStub = MockStub

    def test_is_task(self):
        self.assertTrue(isinstance(Patcher(), Task))

    def test_undefined_repr(self):
        self.assertEquals(repr(Undefined), "Undefined")

    def test_is_monitoring_unseen_class_kind(self):
        self.assertFalse(self.patcher.is_monitoring(self.C, "kind"))

    def test_monitor_class(self):
        self.patcher.monitor(self.C, "kind")
        self.assertTrue(self.patcher.is_monitoring(self.C, "kind"))

    def test_monitor_subclass(self):
        self.patcher.monitor(self.C, "kind")
        self.assertTrue(self.patcher.is_monitoring(self.D, "kind"))

    def test_monitor_unknown_class(self):
        self.patcher.monitor(self.C, "kind")
        self.assertFalse(self.patcher.is_monitoring(self.E, "kind"))

    def test_is_monitoring_unseen_instance(self):
        obj = self.E()
        self.patcher.monitor(self.C, "kind")
        self.assertFalse(self.patcher.is_monitoring(obj, "kind"))

    def test_is_monitoring_instance_explicitly_monitored(self):
        obj = self.C()
        self.patcher.monitor(obj, "kind")
        self.assertTrue(self.patcher.is_monitoring(obj, "kind"))

    def test_is_monitoring_instance_monitored_by_class(self):
        obj = self.D()
        self.patcher.monitor(self.D, "kind")
        self.assertTrue(self.patcher.is_monitoring(obj, "kind"))

    def test_patch_attr(self):
        self.patcher.patch_attr(self.C, "attr", "patch")
        self.assertEquals(self.C.__dict__.get("attr"), "patch")

    def test_patch_attr_and_restore(self):
        self.patcher.patch_attr(self.C, "attr", "patch")
        self.patcher.restore()
        self.assertTrue("attr" not in self.C.__dict__)

    def test_patch_attr_and_restore_to_original(self):
        self.C.attr = "original"
        self.patcher.patch_attr(self.C, "attr", "patch")
        self.patcher.restore()
        self.assertEquals(self.C.__dict__.get("attr"), "original")

    def test_get_unpatched_attr_unpatched_undefined(self):
        self.assertEquals(self.patcher.get_unpatched_attr(self.C, "attr"),
                          Undefined)

    def test_get_unpatched_attr_unpatched(self):
        self.C.attr = "original"
        self.assertEquals(self.patcher.get_unpatched_attr(self.C, "attr"),
                          "original")

    def test_get_unpatched_attr_defined_on_superclass(self):
        self.C.attr = "original"
        self.assertEquals(self.patcher.get_unpatched_attr(self.D, "attr"),
                          "original")

    def test_get_unpatched_attr_defined_on_superclass_patched_on_sub(self):
        self.C.attr = "original"
        self.patcher.patch_attr(self.D, "attr", "patch")
        self.assertEquals(self.patcher.get_unpatched_attr(self.D, "attr"),
                          "original")

    def test_get_unpatched_attr_patched_originally_undefined(self):
        self.patcher.patch_attr(self.C, "attr", "patch")
        self.assertEquals(self.patcher.get_unpatched_attr(self.C, "attr"),
                          Undefined)

    def test_get_unpatched_attr_patched(self):
        self.C.attr = "original"
        self.patcher.patch_attr(self.C, "attr", "patch")
        self.assertEquals(self.patcher.get_unpatched_attr(self.C, "attr"),
                          "original")

    def test_get_unpatched_attr_on_instance_originally_undefined(self):
        self.assertEquals(self.patcher.get_unpatched_attr(self.C(), "attr"),
                          Undefined)

    def test_get_unpatched_attr_on_instance(self):
        self.C.attr = "original"
        self.assertEquals(self.patcher.get_unpatched_attr(self.D(), "attr"),
                          "original")

    def test_get_unpatched_attr_on_instance_defined_on_superclass(self):
        self.C.attr = "original"
        self.patcher.patch_attr(self.C, "attr", "patch")
        self.assertEquals(self.patcher.get_unpatched_attr(self.D(), "attr"),
                          "original")

    def test_get_unpatched_attr_on_instance_with_descriptor(self):
        self.C.attr = property(lambda self: "original")
        self.patcher.patch_attr(self.C, "attr", "patch")
        self.assertEquals(self.patcher.get_unpatched_attr(self.D(), "attr"),
                          "original")

    def test_get_unpatched_attr_on_subclass_with_descriptor(self):
        calls = []
        class Property(object):
            def __get__(self, obj, cls):
                calls.append((obj, cls))
                return "original"
        self.C.attr = Property()
        self.patcher.patch_attr(self.C, "attr", "patch")
        self.assertEquals(self.patcher.get_unpatched_attr(self.D, "attr"),
                          "original")
        self.assertEquals(calls, [(None, self.D)])

    def test_get_unpatched_attr_on_instance_with_fake_descriptor(self):
        class BadProperty(object):
            def __init__(self):
                # On real, __get__ must be on the class, not on the instance.
                self.__get__ = lambda self, obj, cls=None: "original"
        prop = BadProperty()
        self.C.attr = prop
        self.patcher.patch_attr(self.C, "attr", "patch")
        self.assertEquals(self.patcher.get_unpatched_attr(self.D(), "attr"),
                          prop)

    def test_replay_with_monitored_class(self):
        self.patcher.monitor(self.C, "call")
        self.patcher.replay()
        self.assertEquals(type(self.C.__dict__["__call__"]), PatchedMethod)

    def test_replay_with_monitored_instance(self):
        self.patcher.monitor(self.C(), "call")
        self.patcher.replay()
        self.assertEquals(type(self.C.__dict__["__call__"]), PatchedMethod)

    def test_replay_getattr(self):
        self.patcher.monitor(self.C, "getattr")
        self.patcher.replay()
        self.assertEquals(type(self.C.__dict__["__getattribute__"]),
                          PatchedMethod)

    def test_restore(self):
        self.patcher.monitor(self.C, "call")
        self.patcher.replay()
        self.patcher.restore()
        self.assertTrue("__call__" not in self.C.__dict__)

    def test_restore_twice_does_nothing(self):
        self.patcher.monitor(self.C, "call")
        self.patcher.replay()
        self.patcher.restore()
        self.C.__call__ = "original"
        self.patcher.restore()
        self.assertTrue(self.C.__dict__.get("__call__"), "original")

    def test_patched_call_on_instance(self):
        self.patcher.monitor(self.C, "call")
        obj = self.C()
        obj.__mocker_mock__ = self.MockStub()
        self.patcher.replay()
        result = obj(1, a=2)
        self.assertEquals(result, ("call", (1,), {"a": 2}, obj))

    def test_patched_call_on_class(self):
        self.patcher.monitor(self.C, "call")
        self.C.__mocker_mock__ = self.MockStub()
        self.patcher.replay()
        obj = self.C()
        result = obj(1, a=2)
        self.assertEquals(result, ("call", (1,), {"a": 2}, obj))

    def test_patched_call_on_class_edge_case(self):
        """Only "getattr" kind should passthrough on __mocker_* arguments."""
        self.patcher.monitor(self.C, "call")
        self.C.__mocker_mock__ = self.MockStub()
        self.patcher.replay()
        obj = self.C()
        result = obj("__mocker_mock__")
        self.assertEquals(result, ("call", ("__mocker_mock__",), {}, obj))

    def test_patched_getattr_on_class(self):
        self.patcher.monitor(self.C, "getattr")
        self.C.__mocker_mock__ = self.MockStub()
        self.patcher.replay()
        obj = self.C()
        result = obj.attr
        self.assertEquals(result, ("getattr", ("attr",), {}, obj))

    def test_patched_getattr_on_unmonitored_object(self):
        obj1 = self.C()
        obj1.__mocker_mock__ = self.MockStub()
        self.patcher.monitor(obj1, "getattr")
        obj2 = self.C()
        obj2.attr = "original"
        self.patcher.replay()
        self.assertEquals(obj1.attr, ("getattr", ("attr",), {}, obj1))
        self.assertEquals(obj2.attr, "original")

    def test_patched_getattr_on_different_instances(self):
        def build_getattr(original):
            def __getattribute__(self, name):
                if name == "attr":
                    return original
                return object.__getattribute__(self, name)
            return __getattribute__
        self.C.__getattribute__ = build_getattr("originalC")
        self.D.__getattribute__ = build_getattr("originalD")

        class MockStub(object):
            def __init__(self, id):
                self.id = id
            def __mocker_act__(self, kind, args=(), kwargs={}, object=None):
                return self.id

        obj1, obj2, obj3, obj4, obj5, obj6 = [self.C() for i in range(6)]
        obj7, obj8, obj9 = [self.D() for i in range(3)]

        obj2.__mocker_mock__ = MockStub(2)
        self.patcher.monitor(obj2, "getattr")
        obj5.__mocker_mock__ = MockStub(5)
        self.patcher.monitor(obj5, "getattr")
        obj8.__mocker_mock__ = MockStub(8)
        self.patcher.monitor(obj8, "getattr")

        self.patcher.replay()
        self.assertEquals(obj1.attr, "originalC")
        self.assertEquals(obj2.attr, 2)
        self.assertEquals(obj3.attr, "originalC")
        self.assertEquals(obj4.attr, "originalC")
        self.assertEquals(obj5.attr, 5)
        self.assertEquals(obj6.attr, "originalC")
        self.assertEquals(obj7.attr, "originalD")
        self.assertEquals(obj8.attr, 8)
        self.assertEquals(obj9.attr, "originalD")

    def test_patched_getattr_execute_getattr(self):
        class C(object):
            def __getattribute__(self, attr):
                if attr == "attr":
                    return "original"
        action = Action("getattr", ("attr",), {})
        obj = C()
        self.patcher.monitor(obj, "getattr")
        self.patcher.replay()
        self.assertEquals(self.patcher.execute(action, obj), "original")

    def test_execute_getattr_on_unexistent(self):
        action = Action("getattr", ("attr",), {})
        obj = self.C()
        self.patcher.monitor(obj, "getattr")
        self.patcher.replay()
        self.assertRaises(AttributeError, self.patcher.execute, action, obj)

    def test_patched_real_getattr_on_different_instances(self):
        def build_getattr(original):
            def __getattr__(self, name):
                if name == "attr":
                    return original
                return object.__getattr__(self, name)
            return __getattr__
        self.C.__getattr__ = build_getattr("originalC")
        self.D.__getattr__ = build_getattr("originalD")

        class MockStub(object):
            def __init__(self, id):
                self.id = id
            def __mocker_act__(self, kind, args=(), kwargs={}, object=None):
                return self.id

        obj1, obj2, obj3, obj4, obj5, obj6 = [self.C() for i in range(6)]
        obj7, obj8, obj9 = [self.D() for i in range(3)]

        obj2.__mocker_mock__ = MockStub(2)
        self.patcher.monitor(obj2, "getattr")
        obj5.__mocker_mock__ = MockStub(5)
        self.patcher.monitor(obj5, "getattr")
        obj8.__mocker_mock__ = MockStub(8)
        self.patcher.monitor(obj8, "getattr")

        self.patcher.replay()
        self.assertEquals(obj1.attr, "originalC")
        self.assertEquals(obj2.attr, 2)
        self.assertEquals(obj3.attr, "originalC")
        self.assertEquals(obj4.attr, "originalC")
        self.assertEquals(obj5.attr, 5)
        self.assertEquals(obj6.attr, "originalC")
        self.assertEquals(obj7.attr, "originalD")
        self.assertEquals(obj8.attr, 8)
        self.assertEquals(obj9.attr, "originalD")

    def test_patched_real_getattr_execute_getattr(self):
        class C(object):
            def __getattr__(self, attr):
                if attr == "attr":
                    return "original"
        action = Action("getattr", ("attr",), {})
        obj = C()
        self.patcher.monitor(obj, "getattr")
        self.patcher.replay()
        self.assertEquals(self.patcher.execute(action, obj), "original")

    def test_execute_call(self):
        class C(object):
            def __call__(self, *args, **kwargs):
                return (args, kwargs)
        action = Action("call", (1,), {"a": 2})
        obj = C()
        self.patcher.monitor(obj, "call")
        self.patcher.replay()
        self.assertEquals(self.patcher.execute(action, obj), ((1,), {"a": 2}))

    def test_recorder_class_getattr(self):
        self.C.method = lambda: None
        mock = self.mocker.patch(self.C)
        mock.method()
        self.mocker.result("mocked")
        self.mocker.replay()
        self.assertEquals(self.C().method(), "mocked")
        self.assertRaises(AssertionError, self.C().method)

    def test_recorder_instance_getattr(self):
        self.C.attr = "original"
        obj1 = self.C()
        obj2 = self.C()
        mock = self.mocker.patch(obj1)
        mock.attr
        self.mocker.result("mocked")
        self.mocker.replay()
        self.assertEquals(obj1.attr, "mocked")
        self.assertRaises(AssertionError, getattr, obj1, "attr")
        self.assertEquals(obj2.attr, "original")
        self.assertRaises(AttributeError, getattr, obj1, "unexistent")

    def test_recorder_passthrough(self):
        class C(object):
            def __init__(self):
                self.result = "original" # Value on object's dictionary.
            def method(self):
                return self.result
        mock = self.mocker.patch(C)
        mock.method()
        self.mocker.passthrough()
        self.mocker.replay()
        obj = C()
        self.assertEquals(obj.method(), "original")
        self.assertRaises(AssertionError, obj.method)
