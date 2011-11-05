__author__ = 'aldaran'

from django.db import models
from compositekey import db

class Book(models.Model):
    id = db.MultipleFieldPrimaryKey(fields=["author", "name"])
    name = models.CharField(max_length=100)
    author = models.CharField(max_length=100)

    def __unicode__(self):
        return u"%s (by %s)" % (self.name, self.author)

class BookReal(Book):
    text = models.CharField(max_length=100)

    def __unicode__(self):
        return u"REAL: %s" % unicode(self.book_ptr)

class Library(models.Model):
    name = models.CharField(max_length=100)
    books = models.ManyToManyField(Book)

    def __unicode__(self):
        return u"Library: %s" % unicode(self.name)


class Biografy(models.Model):
    id = db.MultipleFieldPrimaryKey(fields=["book",])
    book = models.OneToOneField(Book)
    text = models.CharField(max_length=100)

    def __unicode__(self):
        return u"BIO: %s" % unicode(self.book)

class AbstractChapter(models.Model):
    id = db.MultipleFieldPrimaryKey(fields=["book", "number"])
    book = models.ForeignKey(Book, to_field="id",
                             fields_ext={
            "author": {"db_column" :"b_author", "name" : "_author"},
            "name"  : {"db_column" :"b_name"},
    },
    related_name="chapter_set")
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=100)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u"%s (%s) %s" % (self.book_name, self.number, self._author)

class Chapter(AbstractChapter):
    text = models.CharField(max_length=100)


class OldBook(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=100)
    author = models.CharField(max_length=100)

    def __unicode__(self):
        return u"%s (by %s)" % (self.name, self.author)

class OldBookReal(OldBook):
    text = models.CharField(max_length=100)

    def __unicode__(self):
        return u"REAL: %s" % unicode(self.oldbook_ptr)

class OldBiografy(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    book = models.OneToOneField(OldBook)
    text = models.CharField(max_length=100)

    def __unicode__(self):
        return u"BIO: %s" % unicode(self.book)

class OldLibrary(models.Model):
    name = models.CharField(max_length=100)
    books = models.ManyToManyField(OldBook)

    def __unicode__(self):
        return u"Library: %s" % unicode(self.name)

class AbstractOldChapter(models.Model):
    book = models.ForeignKey(OldBook, to_field="id")
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=100)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u"%s (%s) %s" % (self.book.name, self.number, self.book.author)

class OldChapter(AbstractOldChapter):
    text = models.CharField(max_length=100)
