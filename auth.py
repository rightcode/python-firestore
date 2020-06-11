"""
Firebase Authentication

Copyright (c) RightCode Inc. All rights reserved.
"""

import requests
import json
from firebase_admin import auth
from datetime import timedelta
from getpass import getpass


def _sign_up(email, password, displayName):
    # Api key取得
    with open('private/apikey.txt') as f:
        api_key = f.read()

    # 管理者ユーザ追加
    url = 'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={}'.format(api_key)
    headers = {'Content-type': 'application/json'}
    data = json.dumps({'email': email,
                       'password': password,
                       'returnSecureToken': True})

    result = requests.post(url=url,
                           headers=headers,
                           data=data,
                           )

    if 'error' in result.json():
        print('error: {}'.format(result.json()['error']['errors'][0]['message']))
        return result.json()

    # DisplayNameを更新
    url = 'https://identitytoolkit.googleapis.com/v1/accounts:update?key={}'.format(api_key)
    data = json.dumps({
        'idToken': result.json()['idToken'],
        'displayName': displayName
    })

    result = requests.post(url=url,
                           headers=headers,
                           data=data,
                           )

    if 'error' in result.json():
        print('error: {}'.format(result.json()['error']['errors'][0]['message']))
        return result.json()

    return result.json()


def _login(email, password, expires=5):
    with open('private/apikey.txt') as f:
        api_key = f.read()

    url = 'https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={}'.format(api_key)
    headers = {'Content-type': 'application/json'}
    data = json.dumps({'email': email,
                       'password': password,
                       'returnSecureToken': True})

    result = requests.post(url=url,
                           headers=headers,
                           data=data,
                           )

    result = result.json()

    # エラーがある場合
    if 'error' in result:
        return result, None

    # エラーがなければセッションクッキーの作成
    session_cookie = auth.create_session_cookie(result['idToken'], timedelta(expires))

    return result, session_cookie


def _get_user(email):
    return auth.get_user_by_email(email).__dict__['_data']


def _change_user_info(id_token, new_email=None, new_password=None, new_displayName=None):
    return auth.update_user(id_token,
                            email=new_email,
                            password=new_password,
                            display_name=new_displayName).__dict__['_data']


if __name__ == '__main__':
    email = input('email: ')
    password = getpass('password: ')
    display_name = input('Display Name: ')

    res = _sign_up(email, password, display_name)

    if 'error' not in res:
        print('\nSuccess!\n')
    else:
        print('\nOops. Some Error is happened. You should check the result.\n')

    print('Result:')
    print(res)
