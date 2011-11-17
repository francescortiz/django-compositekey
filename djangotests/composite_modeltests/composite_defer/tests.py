from __future__ import absolute_import

from django.db.models.query_utils import DeferredAttribute
from django.test import TestCase

from .models import Secondary, Primary, Child, BigChild


class DeferTests(TestCase):
    def assert_delayed(self, obj, num):
        count = 0
        for field in obj._meta.fields:
            if isinstance(obj.__class__.__dict__.get(field.attname),
                DeferredAttribute):
                count += 1
        self.assertEqual(count, num)

    def test_defer(self):
        # To all outward appearances, instances with deferred fields look the
        # same as normal instances when we examine attribute values. Therefore
        # we test for the number of deferred fields on returned instances (by
        # poking at the internals), as a way to observe what is going on.

        s1 = Secondary.objects.create(first="x1", second="y1")
        p1 = Primary.objects.create(name="p1", value="xx", related=s1)

        qs = Primary.objects.all()
        self.assert_delayed(qs.defer("name")[0], 0)
        self.assert_delayed(qs.defer("value")[0], 1)
        self.assert_delayed(qs.only("name")[0], 1)
        self.assert_delayed(qs.only("value")[0], 0)
        self.assert_delayed(qs.defer("related__first")[0], 0)

        # Using 'pk' with only() should result in 3 deferred fields, namely all
        # of them except the model's primary key see #15494
        self.assert_delayed(qs.only("pk")[0], 1)

        obj = qs.select_related().only("related__first")[0]
        self.assert_delayed(obj, 1)

        self.assertEqual(obj.related_id, s1.pk)

        # You can use 'pk' with reverse foreign key lookups.
        self.assert_delayed(s1.primary_set.all().only('pk')[0], 1)

        self.assert_delayed(qs.defer("value").extra(select={"a": 1})[0], 1)
        self.assert_delayed(qs.extra(select={"a": 1}).defer("value")[0], 1)
        self.assert_delayed(qs.defer("name").defer("value")[0], 1)
        self.assert_delayed(qs.only("name").only("value")[0], 0)
        self.assert_delayed(qs.only("name").defer("value")[0], 1)
        self.assert_delayed(qs.only("name", "value").defer("value")[0], 1)
        self.assert_delayed(qs.defer("name").only("value")[0], 0)

        obj = qs.only()[0]
        self.assert_delayed(qs.defer(None)[0], 0)
        self.assert_delayed(qs.only("name").defer(None)[0], 0)

        # User values() won't defer anything (you get the full list of
        # dictionaries back), but it still works.
        self.assertEqual(qs.defer("value").values()[0], {
            'name': u'x1',
            'related_second': u'y1',
            'related_first': u'x1'
        })
        self.assertEqual(qs.only("name").values()[0], {
            'name': u'x1',
            'related_second': u'y1',
            'related_first': u'x1'
        })

        # Using defer() and only() with get() is also valid.
        self.assert_delayed(qs.defer("name").get(pk=p1.pk), 0)
        self.assert_delayed(qs.only("name").get(pk=p1.pk), 1)

        # DOES THIS WORK?
        self.assert_delayed(qs.only("name").select_related("related")[0], 1)
        self.assert_delayed(qs.defer("related").select_related("related")[0], 0)

        # Saving models with deferred fields is possible (but inefficient,
        # since every field has to be retrieved first).
        obj = Primary.objects.defer("value").get(name="p1")
        obj.name = "a new name"
        obj.save()
        self.assertQuerysetEqual(
            Primary.objects.all(), [
                "a new name",
            ],
            lambda p: p.name
        )

        # Regression for #10572 - A subclass with no extra fields can defer
        # fields from the base class
        Child.objects.create(name="c1", value="foo", related=s1)
        # You can defer a field on a baseclass when the subclass has no fields
        obj = Child.objects.defer("value").get(name="c1")
        self.assert_delayed(obj, 1)
        self.assertEqual(obj.name, "c1")
        self.assertEqual(obj.value, "foo")
        obj.name = "c2"
        obj.save()

        # You can retrive a single column on a base class with no fields
        obj = Child.objects.only("name").get(name="c2")
        self.assert_delayed(obj, 3)
        self.assertEqual(obj.name, "c2")
        self.assertEqual(obj.value, "foo")
        obj.name = "cc"
        obj.save()

        BigChild.objects.create(name="b1", value="foo", related=s1, other="bar")
        # You can defer a field on a baseclass
        obj = BigChild.objects.defer("value").get(name="b1")
        self.assert_delayed(obj, 1)
        self.assertEqual(obj.name, "b1")
        self.assertEqual(obj.value, "foo")
        self.assertEqual(obj.other, "bar")
        obj.name = "b2"
        obj.save()

        # You can defer a field on a subclass
        obj = BigChild.objects.defer("other").get(name="b2")
        self.assert_delayed(obj, 1)
        self.assertEqual(obj.name, "b2")
        self.assertEqual(obj.value, "foo")
        self.assertEqual(obj.other, "bar")
        obj.name = "b3"
        obj.save()

        # You can retrieve a single field on a baseclass
        obj = BigChild.objects.only("name").get(name="b3")
        self.assert_delayed(obj, 4)
        self.assertEqual(obj.name, "b3")
        self.assertEqual(obj.value, "foo")
        self.assertEqual(obj.other, "bar")
        obj.name = "b4"
        obj.save()

        # You can retrieve a single field on a baseclass
        obj = BigChild.objects.only("other").get(name="b4")
        self.assert_delayed(obj, 4)
        self.assertEqual(obj.name, "b4")
        self.assertEqual(obj.value, "foo")
        self.assertEqual(obj.other, "bar")
        obj.name = "bb"
        obj.save()
