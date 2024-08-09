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


class TestSchemaNode(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from colander import SchemaNode

        return SchemaNode(*arg, **kw)

    def test_new_sets_order(self):
        node = self._makeOne(None)
        self.assertTrue(hasattr(node, '_order'))

    def test_ctor_no_title(self):
        child = DummySchemaNode(None, name='fred')
        node = self._makeOne(
            None,
            child,
            validator=1,
            default=2,
            name='name_a',
            missing='missing',
        )
        self.assertEqual(node.typ, None)
        self.assertEqual(node.children, [child])
        self.assertEqual(node.validator, 1)
        self.assertEqual(node.default, 2)
        self.assertEqual(node.missing, 'missing')
        self.assertEqual(node.name, 'name_a')
        self.assertEqual(node.title, 'Name A')

    def test_ctor_with_title(self):
        child = DummySchemaNode(None, name='fred')
        node = self._makeOne(
            None, child, validator=1, default=2, name='name', title='title'
        )
        self.assertEqual(node.typ, None)
        self.assertEqual(node.children, [child])
        self.assertEqual(node.validator, 1)
        self.assertEqual(node.default, 2)
        self.assertEqual(node.name, 'name')
        self.assertEqual(node.title, 'title')

    def test_ctor_with_description(self):
        node = self._makeOne(
            None,
            validator=1,
            default=2,
            name='name',
            title='title',
            description='desc',
        )
        self.assertEqual(node.description, 'desc')

    def test_ctor_with_widget(self):
        node = self._makeOne(None, widget='abc')
        self.assertEqual(node.widget, 'abc')

    def test_ctor_with_preparer(self):
        node = self._makeOne(None, preparer='abc')
        self.assertEqual(node.preparer, 'abc')

    def test_ctor_without_preparer(self):
        node = self._makeOne(None)
        self.assertEqual(node.preparer, None)

    def test_ctor_with_unknown_kwarg(self):
        node = self._makeOne(None, foo=1)
        self.assertEqual(node.foo, 1)

    def test_ctor_with_kwarg_typ(self):
        node = self._makeOne(typ='foo')
        self.assertEqual(node.typ, 'foo')

    def test_ctor_children_kwarg_typ(self):
        subnode1 = DummySchemaNode(None, name='sub1')
        subnode2 = DummySchemaNode(None, name='sub2')
        node = self._makeOne(subnode1, subnode2, typ='foo')
        self.assertEqual(node.children, [subnode1, subnode2])

    def test_ctor_without_type(self):
        self.assertRaises(NotImplementedError, self._makeOne)

    def test_required_true(self):
        node = self._makeOne(None)
        self.assertEqual(node.required, True)

    def test_required_false(self):
        node = self._makeOne(None, missing=1)
        self.assertEqual(node.required, False)

    def test_required_deferred(self):
        from colander import deferred

        node = self._makeOne(None, missing=deferred(lambda: '123'))
        self.assertEqual(node.required, True)

    def test_deserialize_no_validator(self):
        typ = DummyType()
        node = self._makeOne(typ)
        result = node.deserialize(1)
        self.assertEqual(result, 1)

    def test_deserialize_with_preparer(self):
        from colander import Invalid

        typ = DummyType()

        def preparer(value):
            return 'prepared_' + value

        def validator(node, value):
            if not value.startswith('prepared'):
                raise Invalid(node, 'not prepared')  # pragma: no cover

        node = self._makeOne(typ, preparer=preparer, validator=validator)
        self.assertEqual(node.deserialize('value'), 'prepared_value')

    def test_deserialize_with_multiple_preparers(self):
        from colander import Invalid

        typ = DummyType()

        def preparer1(value):
            return 'prepared1_' + value

        def preparer2(value):
            return 'prepared2_' + value

        def validator(node, value):
            if not value.startswith('prepared2_prepared1'):
                raise Invalid(node, 'not prepared')  # pragma: no cover

        node = self._makeOne(
            typ, preparer=[preparer1, preparer2], validator=validator
        )
        self.assertEqual(
            node.deserialize('value'), 'prepared2_prepared1_value'
        )

    def test_deserialize_preparer_before_missing_check(self):
        from colander import null

        typ = DummyType()

        def preparer(value):
            return null

        node = self._makeOne(typ, preparer=preparer)
        e = invalid_exc(node.deserialize, 1)
        self.assertEqual(e.msg, 'Required')

    def test_deserialize_with_validator(self):
        typ = DummyType()
        validator = DummyValidator(msg='Wrong')
        node = self._makeOne(typ, validator=validator)
        e = invalid_exc(node.deserialize, 1)
        self.assertEqual(e.msg, 'Wrong')

    def test_deserialize_with_unbound_validator(self):
        from colander import Invalid
        from colander import UnboundDeferredError
        from colander import deferred

        typ = DummyType()

        def validator(node, kw):
            def _validate(node, value):
                node.raise_invalid('Invalid')

            return _validate

        node = self._makeOne(typ, validator=deferred(validator))
        self.assertRaises(UnboundDeferredError, node.deserialize, None)
        self.assertRaises(Invalid, node.bind(foo='foo').deserialize, None)

    def test_deserialize_value_is_null_no_missing(self):
        from colander import Invalid
        from colander import null

        typ = DummyType()
        node = self._makeOne(typ)
        self.assertRaises(Invalid, node.deserialize, null)

    def test_deserialize_value_is_null_with_missing(self):
        from colander import null

        typ = DummyType()
        node = self._makeOne(typ)
        node.missing = 'abc'
        self.assertEqual(node.deserialize(null), 'abc')

    def test_deserialize_value_is_null_with_missing_msg(self):
        from colander import null

        typ = DummyType()
        node = self._makeOne(typ, missing_msg='Missing')
        e = invalid_exc(node.deserialize, null)
        self.assertEqual(e.msg, 'Missing')

    def test_deserialize_value_with_interpolated_missing_msg(self):
        from colander import null

        typ = DummyType()
        node = self._makeOne(
            typ, missing_msg='Missing attribute ${title}', name='name_a'
        )
        e = invalid_exc(node.deserialize, null)
        self.assertEqual(e.msg.interpolate(), 'Missing attribute Name A')

    def test_deserialize_noargs_uses_default(self):
        typ = DummyType()
        node = self._makeOne(typ)
        node.missing = 'abc'
        self.assertEqual(node.deserialize(), 'abc')

    def test_deserialize_null_can_be_used_as_missing(self):
        from colander import null

        typ = DummyType()
        node = self._makeOne(typ)
        node.missing = null
        self.assertEqual(node.deserialize(null), null)

    def test_deserialize_appstruct_deferred(self):
        from colander import Invalid
        from colander import deferred
        from colander import null

        typ = DummyType()
        node = self._makeOne(typ)
        node.missing = deferred(lambda: '123')
        self.assertRaises(Invalid, node.deserialize, null)

    def test_serialize(self):
        typ = DummyType()
        node = self._makeOne(typ)
        result = node.serialize(1)
        self.assertEqual(result, 1)

    def test_serialize_value_is_null_no_default(self):
        from colander import null

        typ = DummyType()
        node = self._makeOne(typ)
        result = node.serialize(null)
        self.assertEqual(result, null)

    def test_serialize_value_is_null_with_default(self):
        from colander import null

        typ = DummyType()
        node = self._makeOne(typ)
        node.default = 1
        result = node.serialize(null)
        self.assertEqual(result, 1)

    def test_serialize_noargs_uses_default(self):
        typ = DummyType()
        node = self._makeOne(typ)
        node.default = 'abc'
        self.assertEqual(node.serialize(), 'abc')

    def test_serialize_default_deferred(self):
        from colander import deferred
        from colander import null

        typ = DummyType()
        node = self._makeOne(typ)
        node.default = deferred(lambda: 'abc')
        self.assertEqual(node.serialize(), null)

    def test_add(self):
        node = self._makeOne(None)
        node.add(1)
        self.assertEqual(node.children, [1])

    def test_insert(self):
        node = self._makeOne(None)
        node.children = [99, 99]
        node.insert(1, 'foo')
        self.assertEqual(node.children, [99, 'foo', 99])

    def test_repr(self):
        node = self._makeOne(None, name='flub')
        result = repr(node)
        self.assertTrue(result.startswith('<colander.SchemaNode object at '))
        self.assertTrue(result.endswith("(named flub)>"))

    def test___getitem__success(self):
        node = self._makeOne(None)
        another = self._makeOne(None, name='another')
        node.add(another)
        self.assertEqual(node['another'], another)

    def test___getitem__failure(self):
        node = self._makeOne(None)
        self.assertRaises(KeyError, node.__getitem__, 'another')

    def test___delitem__success(self):
        node = self._makeOne(None)
        another = self._makeOne(None, name='another')
        node.add(another)
        del node['another']
        self.assertEqual(node.children, [])

    def test___delitem__failure(self):
        node = self._makeOne(None)
        self.assertRaises(KeyError, node.__delitem__, 'another')

    def test___setitem__override(self):
        node = self._makeOne(None)
        another = self._makeOne(None, name='another')
        node.add(another)
        andanother = self._makeOne(None, name='andanother')
        node['another'] = andanother
        self.assertEqual(node['another'], andanother)
        self.assertEqual(andanother.name, 'another')

    def test___setitem__no_override(self):
        another = self._makeOne(None, name='another')
        node = self._makeOne(None)
        node['another'] = another
        self.assertEqual(node['another'], another)
        self.assertEqual(node.children[0], another)

    def test___iter__(self):
        node = self._makeOne(None)
        node.children = ['a', 'b', 'c']
        it = node.__iter__()
        self.assertEqual(list(it), ['a', 'b', 'c'])

    def test___contains__(self):
        node = self._makeOne(None)
        another = self._makeOne(None, name='another')
        node.add(another)
        self.assertEqual('another' in node, True)
        self.assertEqual('b' in node, False)

    def test_clone(self):
        inner_typ = DummyType()
        outer_typ = DummyType()
        outer_node = self._makeOne(outer_typ, name='outer')
        inner_node = self._makeOne(inner_typ, name='inner')
        outer_node.foo = 1
        inner_node.foo = 2
        outer_node.children = [inner_node]
        outer_clone = outer_node.clone()
        self.assertFalse(outer_clone is outer_node)
        self.assertEqual(outer_clone.typ, outer_typ)
        self.assertEqual(outer_clone.name, 'outer')
        self.assertEqual(outer_node.foo, 1)
        self.assertEqual(len(outer_clone.children), 1)
        inner_clone = outer_clone.children[0]
        self.assertFalse(inner_clone is inner_node)
        self.assertEqual(inner_clone.typ, inner_typ)
        self.assertEqual(inner_clone.name, 'inner')
        self.assertEqual(inner_clone.foo, 2)

    def test_clone_with_modified_schema_instance(self):
        class Schema(colander.MappingSchema):
            n1 = colander.SchemaNode(colander.String())
            n2 = colander.SchemaNode(colander.String())

        def compare_children(schema, cloned):
            # children of the clone must match the cloned node's children and
            # have to be clones themselves.
            self.assertEqual(len(schema.children), len(cloned.children))
            for child, child_clone in zip(schema.children, cloned.children):
                self.assertIsNot(child, child_clone)
                for name in child.__dict__.keys():
                    self.assertEqual(
                        getattr(child, name), getattr(child_clone, name)
                    )

        # add a child node before cloning
        schema = Schema()
        schema.add(colander.SchemaNode(colander.String(), name='n3'))
        compare_children(schema, schema.clone())
        # remove a child node before cloning
        schema = Schema()
        del schema['n1']
        compare_children(schema, schema.clone())
        # reorder children before cloning
        schema = Schema()
        schema.children = list(reversed(schema.children))
        compare_children(schema, schema.clone())

    def test_clone_mapping_references(self):
        class Schema(colander.MappingSchema):
            n1 = colander.SchemaNode(colander.Mapping(unknown='preserve'))

        foo = {"n1": {"bar": {"baz": "qux"}}}
        bar = Schema().serialize(foo)
        bar["n1"]["bar"]["baz"] = "foobar"
        self.assertEqual(foo["n1"]["bar"]["baz"], "qux")

    def test_bind(self):
        from colander import deferred

        inner_typ = DummyType()
        outer_typ = DummyType()

        def dv(node, kw):
            self.assertTrue(node.name in ['outer', 'inner'])
            self.assertTrue('a' in kw)
            return '123'

        dv = deferred(dv)
        outer_node = self._makeOne(outer_typ, name='outer', missing=dv)
        inner_node = self._makeOne(
            inner_typ, name='inner', validator=dv, missing=dv
        )
        outer_node.children = [inner_node]
        outer_clone = outer_node.bind(a=1)
        self.assertFalse(outer_clone is outer_node)
        self.assertEqual(outer_clone.missing, '123')
        inner_clone = outer_clone.children[0]
        self.assertFalse(inner_clone is inner_node)
        self.assertEqual(inner_clone.missing, '123')
        self.assertEqual(inner_clone.validator, '123')

    def test_bind_with_after_bind(self):
        from colander import deferred

        inner_typ = DummyType()
        outer_typ = DummyType()

        def dv(node, kw):
            self.assertTrue(node.name in ['outer', 'inner'])
            self.assertTrue('a' in kw)
            return '123'

        dv = deferred(dv)

        def remove_inner(node, kw):
            self.assertEqual(kw, {'a': 1})
            del node['inner']

        outer_node = self._makeOne(
            outer_typ, name='outer', missing=dv, after_bind=remove_inner
        )
        inner_node = self._makeOne(
            inner_typ, name='inner', validator=dv, missing=dv
        )
        outer_node.children = [inner_node]
        outer_clone = outer_node.bind(a=1)
        self.assertFalse(outer_clone is outer_node)
        self.assertEqual(outer_clone.missing, '123')
        self.assertEqual(len(outer_clone.children), 0)
        self.assertEqual(len(outer_node.children), 1)

    def test_declarative_name_reassignment(self):
        # see https://github.com/Pylons/colander/issues/39

        class FnordSchema(colander.Schema):
            fnord = colander.SchemaNode(
                colander.Sequence(),
                colander.SchemaNode(colander.Integer(), name=''),
                name="fnord[]",
            )

        schema = FnordSchema()
        self.assertEqual(schema['fnord[]'].name, 'fnord[]')

    def test_cstruct_children(self):
        typ = DummyType()
        typ.cstruct_children = lambda *arg: ['foo']
        node = self._makeOne(typ)
        self.assertEqual(node.cstruct_children(None), ['foo'])

    def test_cstruct_children_warning(self):
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            typ = None
            node = self._makeOne(typ)
            self.assertEqual(node.cstruct_children(None), [])
            self.assertEqual(len(w), 1)

    def test_raise_invalid(self):

        typ = DummyType()
        node = self._makeOne(typ)
        self.assertRaises(colander.Invalid, node.raise_invalid, 'Wrong')


class TestSchemaNodeSubclassing(unittest.TestCase):
    def test_subclass_uses_validator_method(self):
        class MyNode(colander.SchemaNode):
            schema_type = colander.Int
            name = 'my'

            def validator(self, node, cstruct):
                if cstruct > 10:
                    self.raise_invalid('Wrong')

        node = MyNode()
        self.assertRaises(colander.Invalid, node.deserialize, 20)

    def test_subclass_uses_missing(self):
        class MyNode(colander.SchemaNode):
            schema_type = colander.Int
            name = 'my'
            missing = 10

        node = MyNode()
        result = node.deserialize(colander.null)
        self.assertEqual(result, 10)

    def test_subclass_uses_title(self):
        class MyNode(colander.SchemaNode):
            schema_type = colander.Int
            title = 'some title'

        node = MyNode(name='my')
        self.assertEqual(node.title, 'some title')

    def test_subclass_title_overwritten_by_constructor(self):
        class MyNode(colander.SchemaNode):
            schema_type = colander.Int
            title = 'some title'

        node = MyNode(name='my', title='other title')
        self.assertEqual(node.title, 'other title')

    def test_subelement_title_not_overwritten(self):
        class SampleNode(colander.SchemaNode):
            schema_type = colander.String
            title = 'Some Title'

        class SampleSchema(colander.Schema):
            node = SampleNode()

        schema = SampleSchema()
        self.assertEqual('Some Title', schema.children[0].title)

    def test_subclass_value_overridden_by_constructor(self):
        class MyNode(colander.SchemaNode):
            schema_type = colander.Int
            name = 'my'
            missing = 10

        node = MyNode(missing=5)
        result = node.deserialize(colander.null)
        self.assertEqual(result, 5)

    def test_method_values_can_rely_on_binding(self):
        class MyNode(colander.SchemaNode):
            schema_type = colander.Int

            def amethod(self):
                return self.bindings['request']

        node = MyNode()
        newnode = node.bind(request=True)
        self.assertEqual(newnode.amethod(), True)

    def test_nonmethod_values_can_rely_on_after_bind(self):
        class MyNode(colander.SchemaNode):
            schema_type = colander.Int

            def after_bind(self, node, kw):
                self.missing = kw['missing']

        node = MyNode()
        newnode = node.bind(missing=10)
        self.assertEqual(newnode.deserialize(colander.null), 10)

    def test_deferred_methods_dont_quite_work_yet(self):
        class MyNode(colander.SchemaNode):
            schema_type = colander.Int

            @colander.deferred
            def avalidator(self, node, kw):  # pragma: no cover
                def _avalidator(node, cstruct):
                    self.raise_invalid('Foo')

                return _avalidator

        node = MyNode()
        self.assertRaises(TypeError, node.bind)

    def test_nonmethod_values_can_be_deferred_though(self):
        def _missing(node, kw):
            return 10

        class MyNode(colander.SchemaNode):
            schema_type = colander.Int
            missing = colander.deferred(_missing)

        node = MyNode()
        bound_node = node.bind()
        self.assertEqual(bound_node.deserialize(colander.null), 10)

    def test_functions_can_be_deferred(self):
        class MyNode(colander.SchemaNode):
            schema_type = colander.Int

            @colander.deferred
            def missing(node, kw):
                return 10

        node = MyNode()
        bound_node = node.bind()
        self.assertEqual(bound_node.deserialize(colander.null), 10)

    def test_nodes_can_be_deffered(self):
        class MySchema(colander.MappingSchema):
            @colander.deferred
            def child(node, kw):
                return colander.SchemaNode(colander.String(), missing='foo')

        node = MySchema()
        bound_node = node.bind()
        self.assertEqual(bound_node.deserialize({}), {'child': 'foo'})

    def test_schema_child_names_conflict_with_value_names_notused(self):
        class MyNode(colander.SchemaNode):
            schema_type = colander.Mapping
            title = colander.SchemaNode(colander.String())

        node = MyNode()
        self.assertEqual(node.title, '')

    def test_schema_child_names_conflict_with_value_names_used(self):

        doesntmatter = colander.SchemaNode(colander.String(), name='name')

        class MyNode(colander.SchemaNode):
            schema_type = colander.Mapping
            name = 'fred'
            wontmatter = doesntmatter

        node = MyNode()
        self.assertEqual(node.name, 'fred')
        self.assertEqual(node['name'], doesntmatter)

    def test_schema_child_names_conflict_with_value_names_in_superclass(self):

        doesntmatter = colander.SchemaNode(colander.String(), name='name')
        _name = colander.SchemaNode(colander.String())

        class MyNode(colander.SchemaNode):
            schema_type = colander.Mapping
            name = 'fred'
            wontmatter = doesntmatter

        class AnotherNode(MyNode):
            name = _name

        node = AnotherNode()
        self.assertEqual(node.name, 'fred')
        self.assertEqual(node['name'], _name)

    def test_schema_child_names_conflict_with_value_names_in_subclass(self):
        class MyNode(colander.SchemaNode):
            name = colander.SchemaNode(colander.String(), id='name')

        class AnotherNode(MyNode):
            schema_type = colander.Mapping
            name = 'fred'
            doesntmatter = colander.SchemaNode(
                colander.String(), name='name', id='doesntmatter'
            )

        node = AnotherNode()
        self.assertEqual(node.name, 'fred')
        self.assertEqual(node['name'].id, 'doesntmatter')


class TestMappingSchemaInheritance(unittest.TestCase):
    def test_single_inheritance(self):
        class Friend(colander.Schema):
            rank = colander.SchemaNode(colander.Int(), id='rank')
            name = colander.SchemaNode(colander.String(), id='name')
            serial = colander.SchemaNode(colander.Bool(), id='serial2')

        class SpecialFriend(Friend):
            iwannacomefirst = colander.SchemaNode(
                colander.Int(), id='iwannacomefirst2'
            )

        class SuperSpecialFriend(SpecialFriend):
            iwannacomefirst = colander.SchemaNode(
                colander.String(), id='iwannacomefirst1'
            )
            another = colander.SchemaNode(colander.String(), id='another')
            serial = colander.SchemaNode(colander.Int(), id='serial1')

        inst = SuperSpecialFriend()
        self.assertEqual(
            [x.id for x in inst.children],
            ['rank', 'name', 'serial1', 'iwannacomefirst1', 'another'],
        )

    def test_single_inheritance_with_insert_before(self):
        class Friend(colander.Schema):
            rank = colander.SchemaNode(colander.Int(), id='rank')
            name = colander.SchemaNode(colander.String(), id='name')
            serial = colander.SchemaNode(
                colander.Bool(), insert_before='name', id='serial2'
            )

        class SpecialFriend(Friend):
            iwannacomefirst = colander.SchemaNode(
                colander.Int(), id='iwannacomefirst2'
            )

        class SuperSpecialFriend(SpecialFriend):
            iwannacomefirst = colander.SchemaNode(
                colander.String(), insert_before='rank', id='iwannacomefirst1'
            )
            another = colander.SchemaNode(colander.String(), id='another')
            serial = colander.SchemaNode(colander.Int(), id='serial1')

        inst = SuperSpecialFriend()
        self.assertEqual(
            [x.id for x in inst.children],
            ['iwannacomefirst1', 'rank', 'serial1', 'name', 'another'],
        )

    def test_single_inheritance2(self):
        class One(colander.Schema):
            a = colander.SchemaNode(colander.Int(), id='a1')
            b = colander.SchemaNode(colander.Int(), id='b1')
            d = colander.SchemaNode(colander.Int(), id='d1')

        class Two(One):
            a = colander.SchemaNode(colander.String(), id='a2')
            c = colander.SchemaNode(colander.String(), id='c2')
            e = colander.SchemaNode(colander.String(), id='e2')

        class Three(Two):
            b = colander.SchemaNode(colander.Bool(), id='b3')
            d = colander.SchemaNode(colander.Bool(), id='d3')
            f = colander.SchemaNode(colander.Bool(), id='f3')

        inst = Three()
        c = inst.children
        self.assertEqual(len(c), 6)
        result = [x.id for x in c]
        self.assertEqual(result, ['a2', 'b3', 'd3', 'c2', 'e2', 'f3'])

    def test_multiple_inheritance(self):
        class One(colander.Schema):
            a = colander.SchemaNode(colander.Int(), id='a1')
            b = colander.SchemaNode(colander.Int(), id='b1')
            d = colander.SchemaNode(colander.Int(), id='d1')

        class Two(colander.Schema):
            a = colander.SchemaNode(colander.String(), id='a2')
            c = colander.SchemaNode(colander.String(), id='c2')
            e = colander.SchemaNode(colander.String(), id='e2')

        class Three(Two, One):
            b = colander.SchemaNode(colander.Bool(), id='b3')
            d = colander.SchemaNode(colander.Bool(), id='d3')
            f = colander.SchemaNode(colander.Bool(), id='f3')

        inst = Three()
        c = inst.children
        self.assertEqual(len(c), 6)
        result = [x.id for x in c]
        self.assertEqual(result, ['a2', 'b3', 'd3', 'c2', 'e2', 'f3'])

    def test_insert_before_failure(self):
        class One(colander.Schema):
            a = colander.SchemaNode(colander.Int())
            b = colander.SchemaNode(colander.Int(), insert_before='c')

        self.assertRaises(KeyError, One)


class TestDeferred(unittest.TestCase):
    def _makeOne(self, wrapped):
        from colander import deferred

        return deferred(wrapped)

    def test_ctor(self):
        wrapped = lambda: 'foo'
        inst = self._makeOne(wrapped)
        self.assertEqual(inst.wrapped, wrapped)

    def test___call__(self):
        n = object()
        k = object()

        def wrapped(node, kw):
            self.assertEqual(node, n)
            self.assertEqual(kw, k)
            return 'abc'

        inst = self._makeOne(wrapped)
        result = inst(n, k)
        self.assertEqual(result, 'abc')

    def test_retain_func_details(self):
        def wrapped_func(node, kw):
            """Can you hear me now?"""
            pass  # pragma: no cover

        inst = self._makeOne(wrapped_func)
        self.assertEqual(inst.__doc__, 'Can you hear me now?')
        self.assertEqual(inst.__name__, 'wrapped_func')

    def test_w_callable_instance_no_name(self):
        class Wrapped:
            """CLASS"""

            def __call__(self, node, kw):
                """METHOD"""
                pass  # pragma: no cover

        wrapped = Wrapped()
        inst = self._makeOne(wrapped)
        self.assertEqual(inst.__doc__, wrapped.__doc__)
        self.assertFalse('__name__' in inst.__dict__)

    def test_w_callable_instance_no_name_or_doc(self):
        class Wrapped:
            def __call__(self, node, kw):
                pass  # pragma: no cover

        wrapped = Wrapped()
        inst = self._makeOne(wrapped)
        self.assertEqual(inst.__doc__, None)
        self.assertFalse('__name__' in inst.__dict__)

    def test_deferred_with_insert_before(self):
        def wrapped_func(node, kw):
            return colander.SchemaNode(
                colander.Int(),
                insert_before='name2',
            )

        deferred_node = self._makeOne(wrapped_func)

        class MySchema(colander.Schema):
            name2 = colander.SchemaNode(colander.Int())
            name3 = colander.SchemaNode(colander.Int())
            name1 = deferred_node
            name4 = colander.SchemaNode(colander.Int())

        inst = MySchema().bind()
        self.assertEqual(
            [x.name for x in inst.children],
            ['name1', 'name2', 'name3', 'name4'],
        )


class TestSchema(unittest.TestCase):
    def test_alias(self):
        from colander import MappingSchema
        from colander import Schema

        self.assertEqual(Schema, MappingSchema)

    def test_it(self):
        class MySchema(colander.Schema):
            thing_a = colander.SchemaNode(colander.String())
            thing2 = colander.SchemaNode(colander.String(), title='bar')

        node = MySchema(default='abc')
        self.assertTrue(hasattr(node, '_order'))
        self.assertEqual(node.default, 'abc')
        self.assertTrue(isinstance(node, colander.SchemaNode))
        self.assertEqual(node.typ.__class__, colander.Mapping)
        self.assertEqual(node.children[0].typ.__class__, colander.String)
        self.assertEqual(node.children[0].title, 'Thing A')
        self.assertEqual(node.children[1].title, 'bar')

    def test_title_munging(self):
        class MySchema(colander.Schema):
            thing1 = colander.SchemaNode(colander.String())
            thing2 = colander.SchemaNode(colander.String(), title=None)
            thing3 = colander.SchemaNode(colander.String(), title='')
            thing4 = colander.SchemaNode(colander.String(), title='thing2')

        node = MySchema()
        self.assertEqual(node.children[0].title, 'Thing1')
        self.assertEqual(node.children[1].title, None)
        self.assertEqual(node.children[2].title, '')
        self.assertEqual(node.children[3].title, 'thing2')

    def test_deserialize_drop(self):
        class MySchema(colander.Schema):
            a = colander.SchemaNode(colander.String())
            b = colander.SchemaNode(colander.String(), missing=colander.drop)

        node = MySchema()
        expected = {'a': 'test'}
        result = node.deserialize(expected)
        self.assertEqual(result, expected)

    def test_serialize_drop_default(self):
        class MySchema(colander.Schema):
            a = colander.SchemaNode(colander.String())
            b = colander.SchemaNode(colander.String(), default=colander.drop)

        node = MySchema()
        expected = {'a': 'foo'}
        result = node.serialize(expected)
        self.assertEqual(result, expected)

    def test_imperative_with_implicit_schema_type(self):

        node = colander.SchemaNode(colander.String())
        schema = colander.Schema(node)
        self.assertEqual(schema.schema_type, colander.Mapping)
        self.assertEqual(schema.children[0], node)

    def test_schema_with_cloned_nodes(self):
        test_node = colander.SchemaNode(colander.String())

        class TestSchema(colander.Schema):
            a = test_node.clone()
            b = test_node.clone()

        node = TestSchema()
        expected = {'a': 'foo', 'b': 'bar'}
        result = node.serialize(expected)
        self.assertEqual(result, expected)


class TestMappingSchema(unittest.TestCase):
    def test_succeed(self):
        import colander

        class MySchema(colander.MappingSchema):
            pass

        node = MySchema()
        self.assertTrue(isinstance(node, colander.SchemaNode))
        self.assertEqual(node.typ.__class__, colander.Mapping)

    def test_imperative_with_implicit_schema_type(self):
        import colander

        node = colander.SchemaNode(colander.String())
        schema = colander.MappingSchema(node)
        self.assertEqual(schema.schema_type, colander.Mapping)
        self.assertEqual(schema.children[0], node)

    def test_deserialize_missing_drop(self):
        import colander

        class MySchema(colander.MappingSchema):
            a = colander.SchemaNode(
                colander.String(), default='abc', missing=colander.drop
            )

        node = MySchema()
        result = node.deserialize({})
        self.assertEqual(result, {})
        result = node.deserialize({'a': colander.null})
        self.assertEqual(result, {})
        result = node.deserialize({'a': ''})
        self.assertEqual(result, {})

    def test_deserialize_missing_value(self):
        import colander

        class MySchema(colander.MappingSchema):
            a = colander.SchemaNode(
                colander.String(), default=colander.drop, missing='abc'
            )

        node = MySchema()
        result = node.deserialize({})
        self.assertEqual(result, {'a': 'abc'})
        result = node.deserialize({'a': colander.null})
        self.assertEqual(result, {'a': 'abc'})

    def test_serialize_default_drop(self):
        import colander

        class MySchema(colander.MappingSchema):
            a = colander.SchemaNode(
                colander.String(), default=colander.drop, missing='def'
            )

        node = MySchema()
        result = node.serialize({})
        self.assertEqual(result, {})
        result = node.serialize({'a': colander.null})
        self.assertEqual(result, {})

    def test_serialize_default_value(self):
        import colander

        class MySchema(colander.MappingSchema):
            a = colander.SchemaNode(
                colander.String(), default='abc', missing=colander.drop
            )

        node = MySchema()
        result = node.serialize({})
        self.assertEqual(result, {'a': 'abc'})
        result = node.serialize({'a': colander.null})
        self.assertEqual(result, {'a': 'abc'})

    def test_clone_with_mapping_schema(self):
        import colander

        thingnode = colander.SchemaNode(colander.String(), name='foo')
        schema = colander.MappingSchema(colander.Mapping(), thingnode)
        result = schema.clone()
        self.assertFalse(result.children[0] is thingnode)
        self.assertEqual(result.children[0].name, thingnode.name)


class TestSequenceSchema(unittest.TestCase):
    def test_succeed(self):

        _inner = colander.SchemaNode(colander.String())

        class MySchema(colander.SequenceSchema):
            inner = _inner

        node = MySchema()
        self.assertTrue(hasattr(node, '_order'))
        self.assertTrue(isinstance(node, colander.SchemaNode))
        self.assertEqual(node.typ.__class__, colander.Sequence)
        self.assertEqual(node.children[0], _inner)

    def test_fail_toomany(self):

        thingnode = colander.SchemaNode(colander.String())
        thingnode2 = colander.SchemaNode(colander.String())

        class MySchema(colander.SequenceSchema):
            thing = thingnode
            thing2 = thingnode2

        e = invalid_exc(MySchema)
        self.assertEqual(
            e.msg, 'Sequence schemas must have exactly one child node'
        )

    def test_fail_toofew(self):
        class MySchema(colander.SequenceSchema):
            pass

        e = invalid_exc(MySchema)
        self.assertEqual(
            e.msg, 'Sequence schemas must have exactly one child node'
        )

    def test_imperative_with_implicit_schema_type(self):

        node = colander.SchemaNode(colander.String())
        schema = colander.SequenceSchema(node)
        self.assertEqual(schema.schema_type, colander.Sequence)
        self.assertEqual(schema.children[0], node)

    def test_deserialize_missing_drop(self):
        import colander

        class MySchema(colander.SequenceSchema):
            a = colander.SchemaNode(
                colander.String(), default='abc', missing=colander.drop
            )

        node = MySchema()
        result = node.deserialize([None])
        self.assertEqual(result, [])
        result = node.deserialize([colander.null])
        self.assertEqual(result, [])
        result = node.deserialize([''])
        self.assertEqual(result, [])

    def test_deserialize_missing_value(self):
        import colander

        class MySchema(colander.SequenceSchema):
            a = colander.SchemaNode(
                colander.String(), default=colander.drop, missing='abc'
            )

        node = MySchema()
        result = node.deserialize([None])
        self.assertEqual(result, ['abc'])
        result = node.deserialize([colander.null])
        self.assertEqual(result, ['abc'])

    def test_serialize_default_drop(self):
        import colander

        class MySchema(colander.SequenceSchema):
            a = colander.SchemaNode(
                colander.String(), default=colander.drop, missing='abc'
            )

        node = MySchema()
        result = node.serialize([])
        self.assertEqual(result, [])
        result = node.serialize([colander.null])
        self.assertEqual(result, [])

    def test_serialize_default_value(self):
        import colander

        class MySchema(colander.SequenceSchema):
            a = colander.SchemaNode(
                colander.String(), default='abc', missing=colander.drop
            )

        node = MySchema()
        result = node.serialize([])
        self.assertEqual(result, [])
        result = node.serialize([colander.null])
        self.assertEqual(result, ['abc'])

    def test_clone_with_sequence_schema(self):

        thingnode = colander.SchemaNode(colander.String(), name='foo')
        schema = colander.SequenceSchema(colander.Sequence(), thingnode)
        clone = schema.clone()
        self.assertIsNot(schema, clone)
        self.assertEqual(schema.name, clone.name)
        self.assertEqual(len(schema.children), len(clone.children))
        self.assertIsNot(schema.children[0], clone.children[0])
        self.assertEqual(schema.children[0].name, clone.children[0].name)
        self.assertFalse(clone.children[0] is thingnode)
        self.assertEqual(clone.children[0].name, thingnode.name)


class TestTupleSchema(unittest.TestCase):
    def test_it(self):
        class MySchema(colander.TupleSchema):
            thing = colander.SchemaNode(colander.String())

        node = MySchema()
        self.assertTrue(hasattr(node, '_order'))
        self.assertTrue(isinstance(node, colander.SchemaNode))
        self.assertEqual(node.typ.__class__, colander.Tuple)
        self.assertEqual(node.children[0].typ.__class__, colander.String)

    def test_imperative_with_implicit_schema_type(self):

        node = colander.SchemaNode(colander.String())
        schema = colander.TupleSchema(node)
        self.assertEqual(schema.schema_type, colander.Tuple)
        self.assertEqual(schema.children[0], node)


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
