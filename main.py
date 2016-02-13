import webapp2
from handlers import MainHandler, VnosHandler, UrediHandler, KoncanaOpravilaHndler, PonoviOpraviloHandler
from handlers import AdminHandler, AdminPodrobnoHandler

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler, name="osnovna-stran"),
    webapp2.Route('/dodaj-opravilo', VnosHandler),
    webapp2.Route('/opravilo/<opravilo_id:\d+>', UrediHandler),
    webapp2.Route('/seznam-koncanih', KoncanaOpravilaHndler, name='seznam-koncanih'),
    webapp2.Route('/opravilo/<opravilo_id:\d+>/ponovi', PonoviOpraviloHandler),
    webapp2.Route('/admin', AdminHandler, name='admin'),
    webapp2.Route('/opravilo/<opravilo_id:\d+>/administracija', AdminPodrobnoHandler),
], debug=True)


