import unittest


def invalid_exc(func, *arg, **kw):
    from colander import Invalid

    try:
        func(*arg, **kw)
    except Invalid as e:
        return e
    else:
        raise AssertionError('Invalid not raised')  # pragma: no cover


class Test_null(unittest.TestCase):
    def test___nonzero__(self):
        from colander import null

        self.assertFalse(null)

    def test___repr__(self):
        from colander import null

        self.assertEqual(repr(null), '<colander.null>')

    def test_pickling(self):
        import pickle

        from colander import null

        self.assertTrue(pickle.loads(pickle.dumps(null)) is null)


class Test_required(unittest.TestCase):
    def test___repr__(self):
        from colander import required

        self.assertEqual(repr(required), '<colander.required>')

    def test_pickling(self):
        import pickle

        from colander import required

        self.assertTrue(pickle.loads(pickle.dumps(required)) is required)


class Test_drop(unittest.TestCase):
    def test___repr__(self):
        from colander import drop

        self.assertEqual(repr(drop), '<colander.drop>')

    def test_pickling(self):
        import pickle

        from colander import drop

        self.assertTrue(pickle.loads(pickle.dumps(drop)) is drop)


class Dummy:
    pass


class DummySchemaNode:
    def __init__(self, typ, name='', exc=None, default=None):
        self.typ = typ
        self.name = name
        self.exc = exc
        self.required = default is None
        self.default = default
        self.children = []

    def deserialize(self, val):
        from colander import Invalid

        if self.exc:
            raise Invalid(self, self.exc)
        return val

    def serialize(self, val):
        from colander import Invalid

        if self.exc:
            raise Invalid(self, self.exc)
        return val

    def __getitem__(self, name):
        for child in self.children:
            if child.name == name:
                return child


class DummyValidator:
    def __init__(self, msg=None, children=None):
        self.msg = msg
        self.children = children

    def __call__(self, node, value):
        from colander import Invalid

        if self.msg:
            e = Invalid(node, self.msg)
            self.children and e.children.extend(self.children)
            raise e


class DummyValidatorWithMsgNone:
    def __call__(self, node, value):
        from colander import Invalid

        e = Invalid(node)
        raise e


class Uncooperative:
    def __str__(self):
        raise ValueError('I wont cooperate')

    __unicode__ = __str__


class DummyType:
    def serialize(self, node, value):
        return value

    def deserialize(self, node, value):
        return value

    def flatten(self, node, appstruct, prefix='', listitem=False):
        if listitem:
            key = prefix.rstrip('.')
        else:
            key = prefix + 'appstruct'
        return {key: appstruct}

    def unflatten(self, node, paths, fstruct):
        assert paths == [node.name]
        return fstruct[node.name]
