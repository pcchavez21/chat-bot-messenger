import webapp2
import json
import logging
from google.appengine.api import urlfetch
from bot import Bot
import yaml
from user_events import UserEventsDao

VERIFY_TOKEN = "Chat-Bot-Token"
ACCESS_TOKEN = "EAAGeq2v8uccBAK2PfBAjbvVZAU6rwCE6HmPiZAV2kLj7qhkzo4onDZAJgVmschL7cWzU36xRWhmZA9UjA5WZARQwc7Xe7imFyBZB9KUwAMOhxBFKaAUuwUldNYBC6jrWKgXh9tl7OZBJVZBUhGbDOQhl57YxKbYRdfDnC38yl9YjzQZDZD"

class MainPage(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        super(MainPage, self).__init__(request, response)
        logging.info("Instanciando Bot")
        tree = yaml.load(open('tree.yaml'))
        logging.info("Tree: %r", tree)
        self.bot = Bot(send_message, UserEventsDao(), tree) 
        


    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        mode = self.request.get("hub.mode")
        if mode == "subscribe":
            challenge = self.request.get("hub.challenge")
            verify_token = self.request.get("hub.verify_token")
            if verify_token == VERIFY_TOKEN:
                self.response.write(challenge)
        else:
            self.response.write("Chat-bot very soon")
    def post(self):
        logging.info("Informacion obtenida desde messenger: %s", self.request.body)
        data = json.loads(self.request.body)

        if data["object"] == "page":

            for entry in data["entry"]:
                for messaging_event in entry["messaging"]:
                    sender_id = messaging_event["sender"]["id"]
                    #obtenemos el id del emisor.
                    recipient_id = messaging_event["recipient"]["id"]

                    if messaging_event.get("message"):
                        is_admin = False
                        message = messaging_event["message"]
                        if message.get('is_echo'):
                            if message.get('app_id'): # bot
                                continue
                            else: # admin
                                # se debe desactivar el bot
                                is_admin = True
                        message_text = message.get("text", "")
                        logging.info("Mensaje obtenido: %s", message_text )
                        # bot handle
                        if is_admin:
                            user_id = recipient_id
                        else:
                            user_id = sender_id
                        self.bot.handle(user_id, message_text, is_admin)
                        # send_message(sender_id, "Hola, soy un bot")
                    
                    if messaging_event.get("postback"):
                        message_text = messaging_event['postback']['payload']
                        # bot handle
                        self.bot.handle(sender_id, message_text)
                        logging.info("Post-back obtenido: %s", message_text)

def send_message(recipient_id, message_text, possible_answers):
    logging.info("Enviando mensaje a %r: %s", recipient_id, message_text)
    headers = {
        "Content-Type": "application/json"
    }
    # creamos nuestro objeto de mensaje
    # message = {"text": message_text}
    # maxima cantidad de botones 3
    # maximo 20 caracteres de longitud
    message = get_postbacks_button_message(message_text, possible_answers)
    if message is None:
        message = {"text": message_text}

    raw_data = {
        "recipient": {
            "id": recipient_id
        },
        "message": message
    }
    data = json.dumps(raw_data)
    r = urlfetch.fetch("https://graph.facebook.com/v2.6/me/messages?access_token=%s" % ACCESS_TOKEN,
                        method=urlfetch.POST, headers=headers, payload=data)
    if r.status_code != 200:
        logging.error("Error %r enviando mensaje: %s", r.status_code, r.content)

def get_postbacks_button_message(message_text, possible_answers):
    if possible_answers is None or len(possible_answers) > 3:
        return None
    
    buttons = []
    for answer in possible_answers:
        buttons.append({
            "type": "postback",
            "title": answer,
            "payload": answer
        })

    return{
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": message_text,
                    "buttons": buttons
                }
            }
        }



app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
