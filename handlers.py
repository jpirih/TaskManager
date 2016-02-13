#!/usr/bin/env python
import os
import jinja2
import webapp2
import datetime
from models import Task
from google.appengine.api import users


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}
        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))

# osnovna stran aplikacije
class MainHandler(BaseHandler):
    def get(self):
        # preveri ali je uporabnik prijavljen
        uporabnik = users.get_current_user()
        # preveri ali je uporabnik administrator
        if uporabnik and uporabnik.nickname() == 'janko.pirih':
            logiran = True
            admin = True
            logout_url = users.create_logout_url('/')
            seznam = Task.query(Task.izbrisan == False, Task.izvajalec == uporabnik.nickname()).fetch()
            params = {'seznam':seznam, 'logiran': logiran, 'logout_url': logout_url, 'uporabnik': uporabnik, 'admin': admin}
        # uporabnik je prijavljen ni administrator
        elif uporabnik:
            logiran = True
            logout_url = users.create_logout_url('/')
            seznam = Task.query(Task.izbrisan == False, Task.izvajalec == uporabnik.nickname()).fetch()
            params = {'seznam':seznam, 'logiran': logiran, 'logout_url': logout_url, 'uporabnik': uporabnik}
        # uporabnik ni prijavljen
        else:
            logiran = False
            login_url = users.create_login_url('/')
            params = {'logiran': logiran, 'login_url': login_url}

        return self.render_template("hello.html", params=params)

# dodajanje opravila
class VnosHandler(BaseHandler):
    # uporabnik mora biti prijavljen
    def get(self):
        uporabnik = users.get_current_user()
        if uporabnik:
            params = {'uporabnik': uporabnik}
            return self.render_template('vnos_opravila.html', params=params)
        else:
            return self.redirect_to('osnovna-stran')
# pridobi podatke iz forme vnos
    def post(self):
        try:
            naloga = self.request.get('naloga')
            prioriteta = self.request.get('prioriteta')
            opis = self.request.get('opis')
            datum = self.request.get('termin')
            izvajalec = self.request.get('izvajalec')
# preveri obliko zapisa datuma ce je prazen doda trenutni datum in cas
            if datum == "":
                danes = datetime.datetime.now()
                termin_d = datetime.datetime.strftime(danes,'%d.%m.%Y %H:%M:%S')
                termin = datetime.datetime.strptime(termin_d, '%d.%m.%Y %H:%M:%S')
            else:
                termin = datetime.datetime.strptime(datum,'%d.%m.%Y %H:%M:%S')

            # kreiranje objekta opravilo in shranjevanje v bazo
            opravilo = Task(naloga=naloga, prioriteta=prioriteta, opis=opis, termin=termin, izvajalec=izvajalec)
            opravilo.put()
            # VSE OK vrne na seznam opravil
            return self.redirect_to('osnovna-stran')

        # V primerru napake javi opozoirilo in uporabnik mora napako odpraviti
        except ValueError:
            err = "Datum in ura obezno v formatu d.m.YYYY H:M:S Lahko pa je prazno"
            params = {'err': err}
            return self.render_template('vnos_opravila.html', params=params)

# kontroler za urejanje in zakljucevanje opravil
class UrediHandler(BaseHandler):
# uporabnik mora biti prijavljen - ureja lahko samo svoja opravila
    def get(self, opravilo_id):
        uporabnik = users.get_current_user()
        if uporabnik:
            opravilo = Task.get_by_id(int(opravilo_id))
            params = {'opravilo': opravilo}
            return self.render_template('podrobnosti_opravila.html', params=params)
        else:
            return self.redirect_to('osnovna-stran')

    # Ustrezno doloci status opravila glede na spremembe, ki jih je uporabnik dolocil v formi za urejanje
    # urejanje opisa, koncan da/ne, brisanje
    def post(self, opravilo_id):
        opravilo = Task.get_by_id(int(opravilo_id))
        finished = self.request.get('finished')
        opis = self.request.get('opis')

        opravilo.opis = opis
        if finished == 'da':
            opravilo.finished = True
            opravilo.spremeba_datum = datetime.datetime.utcnow()
            opravilo.put()
        elif finished == 'x':
            opravilo.izbrisan = True
            opravilo.put()
        else:
            opravilo.put()

        return self.redirect_to('osnovna-stran')

# kontroler za koncana opravila
class KoncanaOpravilaHndler(BaseHandler):
    def get(self):
        uporabnik = users.get_current_user()
        if uporabnik:
            seznam_koncano = Task.query(Task.finished == True, Task.izbrisan == False, Task.izvajalec == uporabnik.nickname()).fetch()
            params = {'seznam_koncano': seznam_koncano, 'uporabnik': uporabnik}
            return self.render_template('pregled-koncano.html', params=params)
        else:
            return self.redirect_to('osnovna-stran')

# kontroler za urejanje koncanih opravil
class PonoviOpraviloHandler(BaseHandler):
    def get(self, opravilo_id):
        uporabnik = users.get_current_user()
        if uporabnik:
            opravilo = Task.get_by_id(int(opravilo_id))
            params = {'opravilo':opravilo}

            return self.render_template('obnovi_opravilo.html', params=params)
        else:
            return self.redirect_to('osnovna-stran')

    def post(self, opravilo_id):
        opravilo = Task.get_by_id(int(opravilo_id))
        opis = self.request.get('opis')
        obnovi = self.request.get('finished')

        if obnovi == 'ne':
            opravilo.opis = opis
            opravilo.finished = False
            opravilo.put()
            return self.redirect_to('osnovna-stran')
        else:
            opravilo.izbrisan = True
            opravilo.put()
            return self.redirect_to('seznam-koncanih')

# Admin handler
class AdminHandler(BaseHandler):
    def get(self):
        uporabnik = users.get_current_user()
        if uporabnik and  uporabnik.nickname() == 'janko.pirih':
            seznam = Task.query().fetch()

            params = {'seznam': seznam, 'uporabnik':uporabnik}
            return self.render_template('admin.html', params=params)
        else:
            self.redirect_to('osnovna-stran')

# Kontroler skrbnik podrobno

class AdminPodrobnoHandler(BaseHandler):
    def get(self, opravilo_id):
        uporabnik = users.get_current_user()
        if uporabnik:
            opravilo = Task.get_by_id(int(opravilo_id))
            params = {'opravilo': opravilo}
            return self.render_template('admin_podrobno.html', params=params)
        else:
            return self.redirect_to('osnovna-stran')

    def post(self, opravilo_id):
        opravilo = Task.get_by_id(int(opravilo_id))
        opis = self.request.get('opis')
        status = self.request.get('status')

        if status == 'ne':
            opravilo.opis = opis
            opravilo.put()
        elif status == "da":
            opravilo.opis = opis
            opravilo.finished = True
            opravilo.put()
        elif status == "re-do":
            opravilo.opis = opis
            opravilo.izbrisan = False
            opravilo.finished = False
            opravilo.put()
        elif status == 'x':
            opravilo.opis = opis
            opravilo.izbrisan = True
            opravilo.put()
        elif status == "delete":
            opravilo.key.delete()

        return self.redirect_to('admin')

