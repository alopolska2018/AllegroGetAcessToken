import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser
import json
import keyring

# Dla ułatwienia, definiujemy domyślne |wartości (tak zwane stałe), są one uniwersalne
DEFAULT_OAUTH_URL = 'https://allegro.pl/auth/oauth'
DEFAULT_REDIRECT_URI = 'http://localhost:8000'
#
def get_client_id(allegro_login):
    client_id = keyring.get_password('client_id', allegro_login)
    return client_id

def get_client_secret(allegro_login):
    client_secret = keyring.get_password('client_secret', allegro_login)
    return client_secret

# client_id = '2915d92680534436bea101fa65f06ac7'
# api_key = client_id
# client_secret = 'J9THWoIkqq67tv8p9VcSCNXX6iaUcLGxW5v3Dlyxhw2LZM0DEH4TtNXgOsEQiq1a'


# Implementujemy funkcję, której parametry przyjmują kolejno:
#  - client_id (ClientID), api_key (API Key) oraz opcjonalnie redirect_uri i oauth_url
# (jeżeli ich nie podamy, zostaną użyte domyślne zdefiniowane wyżej)README.md
def get_access_code(client_id, api_key, redirect_uri=DEFAULT_REDIRECT_URI, oauth_url=DEFAULT_OAUTH_URL):
    # zmienna auth_url zawierać będzie zbudowany na podstawie podanych parametrów URL do zdobycia kodu
    auth_url = '{}/authorize' \
               '?response_type=code' \
               '&client_id={}' \
               '&api-key={}' \
               '&redirect_uri={}'.format(oauth_url, client_id, api_key, redirect_uri)

    # uzywamy narzędzia z modułu requests - urlparse - służy do spardowania podanego url
    # (oddzieli hostname od portu)
    parsed_redirect_uri = requests.utils.urlparse(redirect_uri)

    # definiujemy nasz serwer - który obsłuży odpowiedź allegro (redirect_uri)
    server_address = parsed_redirect_uri.hostname, parsed_redirect_uri.port

    # Ta klasa pomoże obsłużyć zdarzenie GET na naszym lokalnym serwerze
    # - odbierze żądanie (odpowiedź) z serwisu allegro
    class AllegroAuthHandler(BaseHTTPRequestHandler):
        def __init__(self, request, address, server):
            super().__init__(request, address, server)

        def do_GET(self):
            self.send_response(200, 'OK')
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            self.server.path = self.path
            self.server.access_code = self.path.rsplit('?code=', 1)[-1]

    # Wyświetli nam adres uruchomionego lokalnego serwera
    print('server_address:', server_address)

    # Uruchamiamy przeglądarkę, przechodząc na adres zdefiniowany do uzyskania kodu dostępu
    # wyświetlić się powinien formularz logowania do serwisu Allegro.pl
    webbrowser.open(auth_url)

    # Uruchamiamy nasz lokalny web server na maszynie na której uruchomiony zostanie skrypt
    # taki serwer dostępny będzie pod adresem http://localhost:8000 (server_address)
    httpd = HTTPServer(server_address, AllegroAuthHandler)
    print('Waiting for response with access_code from Allegro.pl (user authorization in progress)...')

    # Oczekujemy tylko jednego żądania
    httpd.handle_request()

    # Po jego otrzymaniu zamykamy nasz serwer (nie obsługujemy już żadnych żądań)
    httpd.server_close()

    # Klasa HTTPServer przechowuje teraz nasz access_code - wyciągamy go
    _access_code = httpd.access_code

    # Dla jasności co się dzieje - wyświetlamy go na ekranie
    print('Got an authorize code: ', _access_code)

    # i zwracamy jako rezultat działania naszej funkcji
    return _access_code


def sign_in(client_id, client_secret, access_code, api_key, redirect_uri=DEFAULT_REDIRECT_URI, oauth_url=DEFAULT_OAUTH_URL):
    token_url = oauth_url + '/token'

    access_token_data = {'grant_type': 'authorization_code',
                         'code': access_code,
                         'api-key': api_key,
                         'redirect_uri': redirect_uri}

    response = requests.post(url=token_url,
                             auth=requests.auth.HTTPBasicAuth(client_id, client_secret),
                             data=access_token_data)

    reponse_json = json.loads(response.content.decode('utf-8'))

    return reponse_json

def get_access_token(sign_in_response):

    access_token = sign_in_response['access_token']
    keyring.set_password('access_token', 'czemutaktanio', '{}'.format(access_token))

    return access_token


def get_refresh_token(sign_in_response):

    refresh_token = sign_in_response['refresh_token']
    keyring.set_password('refresh_token', 'czemutaktanio', '{}'.format(refresh_token))
    return refresh_token

if __name__ == "__main__":
    allegro_login = input("allegro_login: ")
    client_id = get_client_id(allegro_login)
    client_secret = get_client_secret(allegro_login)
    api_key = client_id
    access_code = get_access_code(client_id, api_key)
    sign_in_response = sign_in(client_id, client_secret, access_code, api_key)
    get_access_token(sign_in_response)
    get_refresh_token(sign_in_response)


