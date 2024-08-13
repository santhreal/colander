import unittest

import colander
import tests


def invalid_exc(func, *arg, **kw):
    from colander import Invalid

    try:
        func(*arg, **kw)
    except Invalid as e:
        return e
    else:
        raise AssertionError('Invalid not raised')  # pragma: no cover


class FunctionalBase:
    def test_deserialize_ok(self):

        data = {
            'int': '10',
            'ob': 'tests',
            'seq': [('1', 's'), ('2', 's'), ('3', 's'), ('4', 's')],
            'seq2': [{'key': '1', 'key2': '2'}, {'key': '3', 'key2': '4'}],
            'tup': ('1', 's'),
        }
        schema = self._makeSchema()
        result = schema.deserialize(data)
        self.assertEqual(result['int'], 10)
        self.assertEqual(result['ob'], tests)
        self.assertEqual(
            result['seq'], [(1, 's'), (2, 's'), (3, 's'), (4, 's')]
        )
        self.assertEqual(
            result['seq2'], [{'key': 1, 'key2': 2}, {'key': 3, 'key2': 4}]
        )
        self.assertEqual(result['tup'], (1, 's'))

    def test_flatten_ok(self):

        appstruct = {
            'int': 10,
            'ob': tests,
            'seq': [(1, 's'), (2, 's'), (3, 's'), (4, 's')],
            'seq2': [{'key': 1, 'key2': 2}, {'key': 3, 'key2': 4}],
            'tup': (1, 's'),
        }
        schema = self._makeSchema()
        result = schema.flatten(appstruct)

        expected = {
            'schema.seq.2.tupstring': 's',
            'schema.seq2.0.key2': 2,
            'schema.ob': tests,
            'schema.seq2.1.key2': 4,
            'schema.seq.1.tupstring': 's',
            'schema.seq2.0.key': 1,
            'schema.seq.1.tupint': 2,
            'schema.seq.0.tupstring': 's',
            'schema.seq.3.tupstring': 's',
            'schema.seq.3.tupint': 4,
            'schema.seq2.1.key': 3,
            'schema.int': 10,
            'schema.seq.0.tupint': 1,
            'schema.tup.tupint': 1,
            'schema.tup.tupstring': 's',
            'schema.seq.2.tupint': 3,
        }

        for k, v in expected.items():
            self.assertEqual(result[k], v)
        for k, v in result.items():
            self.assertEqual(expected[k], v)

    def test_flatten_mapping_has_no_name(self):

        appstruct = {
            'int': 10,
            'ob': tests,
            'seq': [(1, 's'), (2, 's'), (3, 's'), (4, 's')],
            'seq2': [{'key': 1, 'key2': 2}, {'key': 3, 'key2': 4}],
            'tup': (1, 's'),
        }
        schema = self._makeSchema(name='')
        result = schema.flatten(appstruct)

        expected = {
            'seq.2.tupstring': 's',
            'seq2.0.key2': 2,
            'ob': tests,
            'seq2.1.key2': 4,
            'seq.1.tupstring': 's',
            'seq2.0.key': 1,
            'seq.1.tupint': 2,
            'seq.0.tupstring': 's',
            'seq.3.tupstring': 's',
            'seq.3.tupint': 4,
            'seq2.1.key': 3,
            'int': 10,
            'seq.0.tupint': 1,
            'tup.tupint': 1,
            'tup.tupstring': 's',
            'seq.2.tupint': 3,
        }

        for k, v in expected.items():
            self.assertEqual(result[k], v)
        for k, v in result.items():
            self.assertEqual(expected[k], v)

    def test_unflatten_ok(self):

        fstruct = {
            'schema.seq.2.tupstring': 's',
            'schema.seq2.0.key2': 2,
            'schema.ob': tests,
            'schema.seq2.1.key2': 4,
            'schema.seq.1.tupstring': 's',
            'schema.seq2.0.key': 1,
            'schema.seq.1.tupint': 2,
            'schema.seq.0.tupstring': 's',
            'schema.seq.3.tupstring': 's',
            'schema.seq.3.tupint': 4,
            'schema.seq2.1.key': 3,
            'schema.int': 10,
            'schema.seq.0.tupint': 1,
            'schema.tup.tupint': 1,
            'schema.tup.tupstring': 's',
            'schema.seq.2.tupint': 3,
        }
        schema = self._makeSchema()
        result = schema.unflatten(fstruct)

        expected = {
            'int': 10,
            'ob': tests,
            'seq': [(1, 's'), (2, 's'), (3, 's'), (4, 's')],
            'seq2': [{'key': 1, 'key2': 2}, {'key': 3, 'key2': 4}],
            'tup': (1, 's'),
        }

        for k, v in expected.items():
            self.assertEqual(result[k], v)
        for k, v in result.items():
            self.assertEqual(expected[k], v)

    def test_unflatten_mapping_no_name(self):

        fstruct = {
            'seq.2.tupstring': 's',
            'seq2.0.key2': 2,
            'ob': tests,
            'seq2.1.key2': 4,
            'seq.1.tupstring': 's',
            'seq2.0.key': 1,
            'seq.1.tupint': 2,
            'seq.0.tupstring': 's',
            'seq.3.tupstring': 's',
            'seq.3.tupint': 4,
            'seq2.1.key': 3,
            'int': 10,
            'seq.0.tupint': 1,
            'tup.tupint': 1,
            'tup.tupstring': 's',
            'seq.2.tupint': 3,
        }
        schema = self._makeSchema(name='')
        result = schema.unflatten(fstruct)

        expected = {
            'int': 10,
            'ob': tests,
            'seq': [(1, 's'), (2, 's'), (3, 's'), (4, 's')],
            'seq2': [{'key': 1, 'key2': 2}, {'key': 3, 'key2': 4}],
            'tup': (1, 's'),
        }

        for k, v in expected.items():
            self.assertEqual(result[k], v)
        for k, v in result.items():
            self.assertEqual(expected[k], v)

    def test_flatten_unflatten_roundtrip(self):

        appstruct = {
            'int': 10,
            'ob': tests,
            'seq': [(1, 's'), (2, 's'), (3, 's'), (4, 's')],
            'seq2': [{'key': 1, 'key2': 2}, {'key': 3, 'key2': 4}],
            'tup': (1, 's'),
        }
        schema = self._makeSchema(name='')
        self.assertEqual(
            schema.unflatten(schema.flatten(appstruct)), appstruct
        )

    def test_set_value(self):

        appstruct = {
            'int': 10,
            'ob': tests,
            'seq': [(1, 's'), (2, 's'), (3, 's'), (4, 's')],
            'seq2': [{'key': 1, 'key2': 2}, {'key': 3, 'key2': 4}],
            'tup': (1, 's'),
        }
        schema = self._makeSchema()
        schema.set_value(appstruct, 'seq2.1.key', 6)
        self.assertEqual(appstruct['seq2'][1], {'key': 6, 'key2': 4})

    def test_get_value(self):

        appstruct = {
            'int': 10,
            'ob': tests,
            'seq': [(1, 's'), (2, 's'), (3, 's'), (4, 's')],
            'seq2': [{'key': 1, 'key2': 2}, {'key': 3, 'key2': 4}],
            'tup': (1, 's'),
        }
        schema = self._makeSchema()
        self.assertEqual(
            schema.get_value(appstruct, 'seq'),
            [(1, 's'), (2, 's'), (3, 's'), (4, 's')],
        )
        self.assertEqual(schema.get_value(appstruct, 'seq2.1.key'), 3)

    def test_invalid_asdict(self):
        expected = {
            'schema.int': '20 is greater than maximum value 10',
            'schema.ob': 'The dotted name "no.way.this.exists" '
            'cannot be imported',
            'schema.seq.0.0': '"q" is not a number',
            'schema.seq.1.0': '"w" is not a number',
            'schema.seq.2.0': '"e" is not a number',
            'schema.seq.3.0': '"r" is not a number',
            'schema.seq2.0.key': '"t" is not a number',
            'schema.seq2.0.key2': '"y" is not a number',
            'schema.seq2.1.key': '"u" is not a number',
            'schema.seq2.1.key2': '"i" is not a number',
            'schema.tup.0': '"s" is not a number',
        }
        data = {
            'int': '20',
            'ob': 'no.way.this.exists',
            'seq': [('q', 's'), ('w', 's'), ('e', 's'), ('r', 's')],
            'seq2': [{'key': 't', 'key2': 'y'}, {'key': 'u', 'key2': 'i'}],
            'tup': ('s', 's'),
        }
        schema = self._makeSchema()
        e = invalid_exc(schema.deserialize, data)
        errors = e.asdict()
        self.assertEqual(errors, expected)

    def test_invalid_asdict_translation_callback(self):
        from translationstring import TranslationString

        expected = {
            'schema.int': 'translated',
            'schema.ob': 'translated',
            'schema.seq.0.0': 'translated',
            'schema.seq.1.0': 'translated',
            'schema.seq.2.0': 'translated',
            'schema.seq.3.0': 'translated',
            'schema.seq2.0.key': 'translated',
            'schema.seq2.0.key2': 'translated',
            'schema.seq2.1.key': 'translated',
            'schema.seq2.1.key2': 'translated',
            'schema.tup.0': 'translated',
        }
        data = {
            'int': '20',
            'ob': 'no.way.this.exists',
            'seq': [('q', 's'), ('w', 's'), ('e', 's'), ('r', 's')],
            'seq2': [{'key': 't', 'key2': 'y'}, {'key': 'u', 'key2': 'i'}],
            'tup': ('s', 's'),
        }
        schema = self._makeSchema()
        e = invalid_exc(schema.deserialize, data)

        def translation_function(string):
            return TranslationString('translated')

        errors = e.asdict(translate=translation_function)
        self.assertEqual(errors, expected)


class TestImperative(unittest.TestCase, FunctionalBase):
    def _makeSchema(self, name='schema'):

        integer = colander.SchemaNode(
            colander.Integer(), name='int', validator=colander.Range(0, 10)
        )

        ob = colander.SchemaNode(
            colander.GlobalObject(package=colander), name='ob'
        )

        tup = colander.SchemaNode(
            colander.Tuple(),
            colander.SchemaNode(colander.Integer(), name='tupint'),
            colander.SchemaNode(colander.String(), name='tupstring'),
            name='tup',
        )

        seq = colander.SchemaNode(colander.Sequence(), tup, name='seq')

        seq2 = colander.SchemaNode(
            colander.Sequence(),
            colander.SchemaNode(
                colander.Mapping(),
                colander.SchemaNode(colander.Integer(), name='key'),
                colander.SchemaNode(colander.Integer(), name='key2'),
                name='mapping',
            ),
            name='seq2',
        )

        schema = colander.SchemaNode(
            colander.Mapping(), integer, ob, tup, seq, seq2, name=name
        )

        return schema


class TestDeclarative(unittest.TestCase, FunctionalBase):
    def _makeSchema(self, name='schema'):
        class TupleSchema(colander.TupleSchema):
            tupint = colander.SchemaNode(colander.Int())
            tupstring = colander.SchemaNode(colander.String())

        class MappingSchema(colander.MappingSchema):
            key = colander.SchemaNode(colander.Int())
            key2 = colander.SchemaNode(colander.Int())

        class SequenceOne(colander.SequenceSchema):
            tup = TupleSchema()

        class SequenceTwo(colander.SequenceSchema):
            mapping = MappingSchema()

        class MainSchema(colander.MappingSchema):
            int = colander.SchemaNode(
                colander.Int(), validator=colander.Range(0, 10)
            )
            ob = colander.SchemaNode(colander.GlobalObject(package=colander))
            seq = SequenceOne()
            tup = TupleSchema()
            seq2 = SequenceTwo()

        schema = MainSchema(name=name)
        return schema


class TestUltraDeclarative(unittest.TestCase, FunctionalBase):
    def _makeSchema(self, name='schema'):
        class IntSchema(colander.SchemaNode):
            schema_type = colander.Int

        class StringSchema(colander.SchemaNode):
            schema_type = colander.String

        class TupleSchema(colander.TupleSchema):
            tupint = IntSchema()
            tupstring = StringSchema()

        class MappingSchema(colander.MappingSchema):
            key = IntSchema()
            key2 = IntSchema()

        class SequenceOne(colander.SequenceSchema):
            tup = TupleSchema()

        class SequenceTwo(colander.SequenceSchema):
            mapping = MappingSchema()

        class IntSchemaRanged(IntSchema):
            validator = colander.Range(0, 10)

        class GlobalObjectSchema(colander.SchemaNode):
            def schema_type(self):
                return colander.GlobalObject(package=colander)

        class MainSchema(colander.MappingSchema):
            int = IntSchemaRanged()
            ob = GlobalObjectSchema()
            seq = SequenceOne()
            tup = TupleSchema()
            seq2 = SequenceTwo()

        MainSchema.name = name

        schema = MainSchema()
        return schema


class TestDeclarativeWithInstantiate(unittest.TestCase, FunctionalBase):
    def _makeSchema(self, name='schema'):

        # an unlikely usage, but goes to test passing
        # parameters to instantiation works
        @colander.instantiate(name=name)
        class schema(colander.MappingSchema):
            int = colander.SchemaNode(
                colander.Int(), validator=colander.Range(0, 10)
            )
            ob = colander.SchemaNode(colander.GlobalObject(package=colander))

            @colander.instantiate()
            class seq(colander.SequenceSchema):
                @colander.instantiate()
                class tup(colander.TupleSchema):
                    tupint = colander.SchemaNode(colander.Int())
                    tupstring = colander.SchemaNode(colander.String())

            @colander.instantiate()
            class tup(colander.TupleSchema):
                tupint = colander.SchemaNode(colander.Int())
                tupstring = colander.SchemaNode(colander.String())

            @colander.instantiate()
            class seq2(colander.SequenceSchema):
                @colander.instantiate()
                class mapping(colander.MappingSchema):
                    key = colander.SchemaNode(colander.Int())
                    key2 = colander.SchemaNode(colander.Int())

        return schema


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
