"""
controllers.py
ルーティングと処理を記述

Copyright (c) RightCode Inc. All rights reserved.
"""

import responder

from auth import _login, _sign_up, _get_user, _change_user_info
from models import *
from sitemap_generator import update_sitemap

import markdown
import os
from datetime import datetime, timedelta

api = responder.API()

firebase_error_massages = {
    'EMAIL_NOT_FOUND': 'メールアドレスが正しくありません',
    'INVALID_PASSWORD': 'パスワードが正しくありません',
    'WEAK_PASSWORD': 'パスワードが短すぎます。最低でも6文字以上にしてください。',
    'INVALID_EMAIL': 'メールアドレスが正しくありません。',
}

COOKIE_EXPIRES = 5  # days later


@api.route('/')
def index(req, resp):
    """ ルート """
    articles = get_articles(unreleased=False)  # 公開済みのものだけ

    # new
    art_categories = [
        get_category_name(art['category'])
        for art in articles
    ]

    md = markdown.Markdown(extensions=['tables'])
    thumbnails = [
        md.convert(art['thumbnail']) for art in articles
    ]

    resp.html = api.template('index.html',
                             title='ブログ一覧',
                             thumbnails=thumbnails,
                             art_categories=art_categories,  # new
                             articles=articles,)


@api.route('/category/{category}')
def category(req, resp, *, category):
    """ カテゴリごとの記事一覧 """
    articles = get_articles(unreleased=False)  # 公開済みのものだけ

    # カテゴリ抽出
    articles = [
        art for art in articles
        if art['category'] == category
    ]

    md = markdown.Markdown(extensions=['tables'])
    thumbnails = [
        md.convert(art['thumbnail']) for art in articles
    ]

    # カテゴリ名
    cat_name = get_category_name(category)

    resp.html = api.template('index.html',
                             title=f'「{cat_name}」の記事一覧',
                             art_categories=[cat_name for _ in articles],  # 全て同じ
                             thumbnails=thumbnails,
                             articles=articles)


@api.route('/login')
def login(req, resp):
    """ ログインページ """
    # エラーがあれば取得
    error = req.params.get('error', '')
    if error in firebase_error_massages:
        error = firebase_error_massages[error]

    resp.html = api.template('login.html',
                             title='Login',
                             error=error
                             )


@api.route('/logout')
def logout(req, resp):
    """ ログアウト処理 """
    # クッキーのログイン情報を破棄してリダイレクト
    resp.set_cookie(key='session', value='', expires=0, max_age=0)
    resp.set_cookie(key='username', value='', expires=0, max_age=0)
    resp.set_cookie(key='email', value='', expires=0, max_age=0)

    api.redirect(resp, '/login')


@api.route('/admin')
class Admin:
    """ 管理者ページ """
    async def on_get(self, req, resp):
        # ログインしてなければ
        if req.cookies.get('session') is None:
            api.redirect(resp, '/login')

        # ログイン済み
        else:
            articles = get_articles()  # New
            resp.html = api.template('admin.html',
                                     title='管理者ページ',
                                     token=req.cookies.get('token'),
                                     name=req.cookies.get('username'),
                                     articles=articles)

    async def on_post(self, req, resp):
        # POSTデータを取得
        data = await req.media()
        email = data['email']
        password = data['password']

        # 認証
        res, session = _login(email, password, COOKIE_EXPIRES)

        if 'error' not in res:
            # [new] クッキーにログイン情報をセット
            expires = datetime.now() + timedelta(COOKIE_EXPIRES)
            resp.set_cookie(key='session', value=session, expires=expires)
            resp.set_cookie(key='username', value=res['displayName'], expires=expires)
            resp.set_cookie(key='email', value=email, expires=expires)

            # 認証成功ならば管理者ページへ
            articles = get_articles()
            resp.html = api.template('admin.html',
                                     title='管理者ページ',
                                     name=res['displayName'],
                                     articles=articles)
        else:
            # 認証失敗ならばエラーメッセージをログイン画面に渡してリダイレクト
            api.redirect(resp, '/login?error={}'.format(res['error']['errors'][0]['message']))


@api.route('/admin/new')
def new_article(req, resp):
    """ 新規記事追加 """
    if req.cookies.get('session') is None:
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        categories = get_categories()
        tags = get_tags()
        resp.html = api.template('new.html',
                                 action='add',  # new
                                 slug=None,  # new
                                 name=req.cookies.get('username'),
                                 article=None,  # new
                                 categories=categories,
                                 tags=tags)


@api.route('/admin/edit/{slug}')
def edit(req, resp, *, slug):
    """ 記事の編集 """
    if req.cookies.get('session') is None:
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        article = get_article(slug)
        categories = get_categories()
        tags = get_tags()
        resp.html = api.template('new.html',
                                 action='article/update',
                                 slug=slug,
                                 article=article,
                                 name=req.cookies.get('username'),
                                 categories=categories,
                                 tags=tags
                                 )


@api.route('/admin/article/update')
async def article_update(req, resp):
    """ 記事一覧 """
    if req.cookies.get('session') is None or req.media == 'get':
        api.redirect(resp, '/admin')
        return

    data = await req.media()
    original_slug = data.get('original_slug', None)
    title = data.get('title', '')
    thumbnail = data.get('thumbnail', '')  # 変更
    description = data.get('description', '')
    slug = data.get('slug', '').lower().replace(' ', '-')  # 全て小文字かつ空白は置換
    contents = data.get('contents', '')
    category = data.get('category', '')
    tags = data.get_list('tags')

    # プレビュー の場合
    if data.get('preview', None) is not None:
        # マークダウンからHTMLへ
        # tableはでデフォルトでは変換してくれないのでここで指定する
        md = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite'])
        html = md.convert(contents)

        thumbnail = md.convert(thumbnail)  # 追加 md => html

        whats_new = get_whats_new()
        categories = get_categories()
        resp.html = api.template('preview.html',
                                 title=title,
                                 contents=html,
                                 thumbnail=thumbnail,
                                 category=category,
                                 tags=tags,
                                 whats_new=whats_new,
                                 categories=categories
                                 )
        return

    released = False if data.get('draft', None) is not None else True

    # update
    update_article_by_slug(
        original_slug,
        title,
        thumbnail,
        description,
        slug,
        contents,
        category,
        tags,
        released
    )

    if released:
        update_sitemap()

    api.redirect(resp, '/admin')
    return


@api.route('/admin/article/delete')
def delete_article(req, resp):
    """ 記事削除 """
    if req.cookies.get('session') is None:
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        # GETデータ取得
        art_slug = req.params.get('slug', None)

        if art_slug is None:
            api.redirect(resp, '/admin')
            return

        # delete
        delete_article_by_slug(art_slug)

        update_sitemap()

        api.redirect(resp, '/admin')


@api.route('/admin/add')
class Add:
    """ 新規記事の保存・プレビュー ・公開 """
    async def on_get(self, req, resp):
        # ログインしてなければ
        if req.cookies.get('token') is None:
            api.redirect(resp, '/login')

        # ログイン済み
        else:
            resp.html = api.template('new.html',
                                     name=req.cookies.get('username'))

    async def on_post(self, req, resp):
        data = await req.media()
        title = data.get('title', '')
        thumbnail = data.get('thumbnail', '')  # 変更
        description = data.get('description', '')
        slug = data.get('slug', '').lower().replace(' ', '-')  # 全て小文字かつ空白は置換
        contents = data.get('contents', '')
        category = data.get('category', '')
        tags = data.get_list('tags')

        # プレビュー の場合
        if data.get('preview', None) is not None:
            # マークダウンからHTMLへ
            # tableはでデフォルトでは変換してくれないのでここで指定する
            md = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite'])
            html = md.convert(contents)
            thumbnail = md.convert(thumbnail)  # 追加 md => html

            whats_new = get_whats_new()
            categories = get_categories()
            resp.html = api.template('preview.html',
                                     title=title,
                                     contents=html,
                                     thumbnail=thumbnail,
                                     category=category,
                                     tags=tags,
                                     whats_new=whats_new,
                                     categories=categories
                                     )
            return

        # それ以外
        released = False if data.get('draft', None) is not None else True

        article = Article(
            title=title,
            thumbnail=thumbnail,
            description=description,
            author=req.cookies.get('username'),
            slug=slug,
            contents=contents,
            category=category,
            tags=tags,
            released=released,
        )

        article.add()

        if released:
            update_sitemap()

        api.redirect(resp, '/admin')


@api.route('/category/{category}/{slug}')
def single(req, resp, *, category, slug):
    """ 記事 """
    article = get_article(slug)
    if article is None or not article['released']:
        resp.html = api.template('404.html', title='お探しの記事は見つかりませんでした。')
        return

    categories = get_categories()
    whats_new = get_whats_new()

    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite'])
    article['thumbnail'] = md.convert(article['thumbnail'])
    article['contents'] = md.convert(article['contents'])

    resp.html = api.template('single.html',
                             title=article['title'],
                             cat_name=get_category_name(article['category']),
                             article=article,
                             whats_new=whats_new,
                             categories=categories)


@api.route('/admin/media')
def media(req, resp):
    """ メディアページ """
    if req.cookies.get('session') is None:
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        # 今ある画像パスを全て取得
        imgs = get_images()
        resp.html = api.template('media.html',
                                 name=req.cookies.get('username'),
                                 imgs=imgs)


@api.route('/admin/upload')
async def upload(req, resp):
    """ メディアのアップロード """
    if req.cookies.get('session') is None:
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        # アップロードはバックグラウンドで
        @api.background.task
        def _upload(data, filename):
            file = data['file']
            f = open('static/images/{}'.format(filename), 'wb')
            f.write(file['content'])
            f.close()

        data = await req.media(format='files')

        # 画像の名前を被らない名前にする
        # 今回は日付 + filename
        # この接頭辞を使って最新の画像は一番上にする
        now = datetime.today().strftime('%Y%m%d%H%M%S')

        filename = data['file']['filename']
        filename = f'{now}_{filename}'

        # Upload
        _upload(data, filename)

        # media にリダイレクト
        api.redirect(resp, '/admin/media')


@api.route('/admin/profile')
def profile(req, resp):
    """ 管理者の情報 """
    if req.cookies.get('session') is None:
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        # ユーザ情報取得
        user_data = _get_user(req.cookies.get('email'))
        resp.html = api.template('profile.html',
                                 name=req.cookies.get('username'),
                                 user_data=user_data  # 関係のあるものだけビューに渡す
                                 )


@api.route('/admin/profile/update')
async def profile_update(req, resp):
    """ 管理者情報の更新 """
    if req.cookies.get('session') is None or req.media == 'get':  # GETは受け付けない
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        # ユーザ情報取得
        data = await req.media()
        email = data.get('email', None)
        username = data.get('displayName', None)
        password = data.get('password', None)
        tmp_password = data.get('tmp_password', None)

        if password != tmp_password and password is not None:
            # 本当はエラー処理を入れた方が良いが割愛
            api.redirect(resp, '/admin/profile')
            return

        # アップデート
        user = _get_user(req.cookies.get('email'))
        res = _change_user_info(user['localId'],
                                new_email=email,
                                new_password=password,
                                new_displayName=username)

        # res をもとにエラー処理を入れるのが望ましいがここでは割愛
        if 'error' in res:
            api.redirect(resp, '/admin/profile?error={}'.format(res['error']['message']))
            return

        # ここで、クッキーにも反映させておく
        expires = datetime.now() + timedelta(COOKIE_EXPIRES)
        resp.set_cookie(key='username', value=username, expires=expires)

        api.redirect(resp, '/admin/profile')


@api.route('/admin/category')
def category(req, resp):
    """ カテゴリの追加・更新・削除ページ """
    if req.cookies.get('session') is None:
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        # 今あるカテゴリ取得
        categories = get_categories()
        resp.html = api.template('category.html',
                                 name=req.cookies.get('username'),
                                 categories=categories)


@api.route('/admin/category/add')
async def add_category(req, resp):
    """ カテゴリ追加 """
    if req.cookies.get('session') is None or req.media == 'get':  # GETは受け付けない
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        # ユーザ情報取得
        data = await req.media()
        name = data.get('new_cat_name', None)
        slug = data.get('new_cat_slug', None)

        if name is None or slug is None:
            # 本当はエラー処理を追加すべきだが割愛
            api.redirect(resp, '/admin/category')
            return

        if slug in get_category_slugs():  # 既に同じスラッグが存在します
            # 本当はエラー処理を追加すべきだが割愛 その2
            api.redirect(resp, '/admin/category')
            return

        # カテゴリを追加
        cat = Category(name, slug)
        cat.add()

        api.redirect(resp, '/admin/category')


@api.route('/admin/category/delete')
def delete_category(req, resp):
    """ カテゴリ削除 """
    if req.cookies.get('session') is None:
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        # GETデータ取得
        cat_slug = req.params.get('slug', None)

        if cat_slug is None:
            api.redirect(resp, '/admin/category')
            return

        # delete
        delete_category_by_slug(cat_slug)

        api.redirect(resp, '/admin/category')


@api.route('/admin/category/update')
async def update_category(req, resp):
    """ カテゴリ更新 """
    if req.cookies.get('session') is None or req.media == 'get':  # GETは受け付けない
        api.redirect(resp, '/login')

    # ログイン済み
    else:
        # ユーザ情報取得
        data = await req.media()
        categories = get_category_slugs()

        # 全ての更新情報を取得
        names = [
            data.get(f'cat_name_{cat_slug}', None) for cat_slug in categories
        ]
        slugs = [
            data.get(f'cat_slug_{cat_slug}', None) for cat_slug in categories
        ]

        for slug, new_name, new_slug in zip(categories, names, slugs):
            update_category_by_slug(slug, new_name, new_slug)

        api.redirect(resp, '/admin/category')


@api.route('/sitemap.xml')
def sitemap(req, resp):
    """ サイトマップ """
    resp.text = open('sitemap.xml').read()
    resp.headers['Content-type'] = 'application/xml'


def get_images(image_path='static/images/'):
    """ Get images existing in the directory, [image_path] """
    files = os.listdir(image_path)
    extensions = ['.png', '.jpg', '.bmp', 'gif']  # 画像拡張子
    images = [f'{image_path}{f}'
              for f in files
              if os.path.splitext(f)[-1] in extensions  # 画像拡張子のみ取得
              ]
    # 降順 = 日付が新しい順
    images.sort(reverse=True)

    return images
