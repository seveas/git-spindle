import threading

__all__ = ['Singleton']

class Singleton(object):
    """Classes inheriting from Singleton will be singletons. Only one instance
       will ever exist. When creating a second instance, the __init__ method is
       replaced to avoid it being run multiple times. The second and later
       times an instance is created, the first instance is returned"""

    __singleton = None
    __orig_init_code = None
    __orig_init = None

    def __new__(cls, *args, **kwargs):
        """Check whether an instance has already been created. If not, create
           it. If it is, disable __init__ and return the first instance"""
        with threading.RLock():
            if cls.__singleton is None:
                # Create the singleton object once
                cls.__singleton = super(Singleton, cls).__new__(cls)
            elif not isinstance(cls.__singleton, cls):
                # This must be a subclass of a singleton subclass. Create it properly.
                # Temporarily restore __init__ of the base class so it runs once
                # for the subclass.
                if cls.__orig_init_code:
                    cls.__singleton.__class__.__init__.__func__.__code__ = cls.__orig_init_code
                    cls.__singleton.__class__.__orig_init_code = None
                elif cls.__orig_init:
                    cls.__singleton.__class__.__init__ = cls.__orig_init
                    cls.__singleton.__class__.__orig_init = None
                # Create the singleton object once
                cls.__singleton = super(Singleton, cls).__new__(cls)
            elif not cls.__orig_init_code and not cls.__orig_init:
                # Disable the __init__ method at the second instantiation by
                # replacing its __code__. This way the __doc__ etc. stay intact
                if hasattr(cls.__init__, '__func__'):
                    cls.__orig_init_code = cls.__init__.__func__.__code__
                    cls.__init__.__func__.__code__ = (lambda *args, **kwargs: None).__code__
                else:
                    # Must be a wrapper. We have no choice but to disable it completely
                    cls.__orig_init =cls.__init__
                    cls.__init__ = lambda *args, **kwargs: None

        return cls.__singleton

    def __reduce_ex__(self, protocol):
        import warnings
        warnings.warn("Unpickling singletons might result in non-singletons", RuntimeWarning)
        return super(Singleton, self).__reduce_ex__(protocol)

if __name__ == '__main__':
    import unittest

    # Create a few classes
    class Sub1(Singleton):
        def __init__(self, var):
            self.var = var
    class Sub2(Sub1):
        pass
    class Sub3(Singleton):
        def __init__(self, var):
            self.var = var
    class Sub4(Singleton):
        pass
    class List(Singleton, list):
        pass
    class List2(List):
        pass

    class SingletonTest(unittest.TestCase):

        def testbuiltin(self):
            # Test subclassing of list
            a = List([0,1])
            b = List([1,2])
            self.assertTrue(a is b)
            self.assertEqual(a, [0,1])

        def testsubbuiltin(self):
            # Test subclassing of subclasses of (Singleton, list)
            a = List2([0,1])
            b = List2([1,2])
            self.assertTrue(a is b)
            self.assertEqual(a, [0,1])

        def testnoinit(self):
            # Test classes that have no __init__ method
            a = Sub4()
            b = Sub4()
            self.assertTrue(a is b)

        def testoneclass(self):
            # Test that two instances are actually the same and that __init__
            # is not run twice
            a = Sub1(1)
            b = Sub1(2)
            self.assertTrue(a is b)
            self.assertEqual(a.var, 1)
            self.assertEqual(b.var, 1)

        def testsubclasses(self):
            # Test that subclasses are not treated as equal. Test that creating
            # a subclass mangles the superclass' __init__ correctly
            b = Sub2(3)
            a = Sub1(4)
            self.assertFalse(a is b)
            self.assertEqual(a.var, 1)
            self.assertEqual(b.var, 3)

        def testtwoclasses(self):
            # Test that two instances differ and __init__ is run for both
            a = Sub1(5)
            b = Sub3(6)
            self.assertFalse(a is b)
            self.assertEqual(a.var, 1)
            self.assertEqual(b.var, 6)

    unittest.main()
