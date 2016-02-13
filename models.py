from google.appengine.ext import ndb

class Task(ndb.Model):
    naloga = ndb.StringProperty()
    opis = ndb.TextProperty()
    prioriteta = ndb.StringProperty(indexed=True)
    termin = ndb.DateTimeProperty()
    kreirano = ndb.DateTimeProperty(auto_now_add=True)
    izvajalec = ndb.StringProperty()
    finished = ndb.BooleanProperty(default=False)
    izbrisan = ndb.BooleanProperty(default=False)



