
import requests
import json


def _login(email, password):
    with open('static/private/apikey.txt') as f:
        api_key = f.read()

    uri = 'https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={}'.format(api_key)
    headers = {'Content-type': 'application/json'}
    data = json.dumps({'email': email,
                       'password': password,
                       'returnSecureToken': True})

    result = requests.post(url=uri,
                           headers=headers,
                           data=data,
                           )

    return result.json()


if __name__ == '__main__':
    print(_login('contact@example.com', 'password'))
