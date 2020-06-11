"""
models.py
モデルの定義とモデル操作

$ python models.py
でサンプルデータの挿入が可能

Copyright (c) RightCode Inc. All rights reserved.
"""
from datetime import datetime
from init_db import db
from google.cloud.firestore import Query


class Category(object):
    def __init__(self, name: str, slug: str):
        """
        Create Category
        :param name:  category name
        :param slug:  category slug
        """
        # slugの被りがあるか調査
        try:
            if slug in get_category_slugs():
                raise ValueError('Error: The slug you gave has already been existed.')
        except ValueError as e:
            print(e)
            exit(-1)

        self.name = name
        self.slug = slug

    def to_dict(self):
        data = self.__dict__
        return data

    def add(self):
        """ Add data to Firestore """
        db.collection('categories').add(self.to_dict())


class Tag(object):
    def __init__(self, name, slug):
        """
        Create Tag
        :param name:
        :param slug:
        """
        # slugの被りがあるか調査
        try:
            if slug in get_category_slugs():
                raise ValueError('Error: The slug you gave has already been existed.')
        except ValueError as e:
            print(e)
            exit(-1)

        self.name = name
        self.slug = slug

    def to_dict(self):
        data = self.__dict__
        return data

    def add(self):
        db.collection('tags').add(self.to_dict())


class Article(object):
    def __init__(self,
                 title: str,
                 thumbnail: str,
                 contents: str,
                 description: str,
                 author: str,
                 slug: str,
                 category: str,
                 tags: list,
                 released: bool = False
                 ):
        """
        Create article
        :param title:       タイトル
        :param thumbnail:    サムネイル
        :param contents:    記事内容
        :param description: 詳細・抜粋
        :param author:      著者
        :param slug:        スラッグ
        :param category:    カテゴリ
        :param tags:        タグ
        :param released:    公開設定
        """
        # slugの被りがあるか調査 & idを設定
        # 記事数が増えるとこのやり方は，よくないかもしれない
        try:
            if slug in get_article_slugs():
                raise ValueError('Error: The slug you gave has already been existed.')
        except ValueError as e:
            print(e)
            exit(-1)

        self.title = title
        self.thumbnail = thumbnail
        self.contents = contents
        self.description = description
        self.author = author
        self.slug = slug
        self.category = category
        self.tags = tags
        self.last_update = datetime.now()
        self.released = released

    def to_dict(self):
        data = self.__dict__
        return data

    def add(self):
        db.collection('articles').add(self.to_dict())


def get_articles(unreleased: bool = True):
    """
    Get articles
    :param unreleased: True => all articles   False => released articles
    :return:
    """
    if unreleased:
        articles = [art.to_dict()
                    for art in
                    db.collection('articles').order_by(
                        'last_update',
                        direction=Query.DESCENDING
                    ).stream()
                    ]
    else:
        articles = [art.to_dict()
                    for art in
                    db.collection('articles').order_by(
                        'last_update',
                        direction=Query.DESCENDING
                    ).stream()
                    ]
        articles = [art for art in articles if art['released']]

    return articles


def get_article(slug: str):
    """
    Get an articles with slug
    :param slug:
    :return:
    """
    article = [art.to_dict() for art in db.collection('articles').where('slug', '==', slug).stream()]
    if len(article) == 0:
        return None

    return article[0]


def update_article_by_slug(original_slug,
                           title,
                           thumbnail,
                           description,
                           slug,
                           contents,
                           category,
                           tags,
                           release,
                           ):
    # IDを取得
    art_id = [art.id for art in db.collection('articles').where('slug', '==', original_slug).stream()][0]

    # 更新
    db.collection('articles').document(art_id).update({
        'title': title,
        'thumbnail': thumbnail,
        'description': description,
        'slug': slug,
        'contents': contents,
        'category': category,
        'tags': tags,
        'last_update': datetime.now(),
        'released': release,
    })


def delete_article_by_slug(slug: str):
    # slugからIDを取得
    art_id = [art.id for art in db.collection('articles').where('slug', '==', slug).stream()][0]

    # ドキュメントを削除
    db.collection('articles').document(art_id).delete()


def get_whats_new(num: int = 5):
    """ get What's New  """
    articles = [art.to_dict() for art in db.collection('articles').where('released', '==', True).limit(num).stream()]

    # datetimeでソート
    articles = sorted(articles, key=lambda art: art['last_update'], reverse=True)
    return articles


def get_categories():
    """ Get all categories """
    return [cat.to_dict() for cat in db.collection('categories').stream()]


def delete_category_by_slug(slug: str):
    # slugからIDを取得
    c_id = [cat.id for cat in db.collection('categories').where('slug', '==', slug).stream()][0]

    # ドキュメントを削除
    db.collection('categories').document(c_id).delete()


def update_category_by_slug(slug: str, new_name: str = None, new_slug: str = None):
    # slugからIDを取得
    c_id = [cat.id for cat in db.collection('categories').where('slug', '==', slug).stream()][0]

    data = {}
    if new_name is not None:
        data['name'] = new_name
    if new_slug is not None:
        data['slug'] = new_slug

    db.collection('categories').document(c_id).update(data)


def get_category_slugs():
    return [cat.to_dict()['slug'] for cat in db.collection('categories').stream()]


def get_category_name(slug):
    # slugからIDを取得
    c_id = [cat.id for cat in db.collection('categories').where('slug', '==', slug).stream()][0]

    # IDを用いてデータを取得
    category = db.collection('categories').document(c_id).get().to_dict()

    return category['name']  # nameだけ返す


def get_tag_slugs():
    return [cat.to_dict()['slug'] for cat in db.collection('tags').stream()]


def get_article_slugs():
    return [cat.to_dict()['slug'] for cat in db.collection('articles').stream()]


def get_tags():
    """ Get all tags """
    return [cat.to_dict() for cat in db.collection('tags').stream()]


if __name__ == '__main__':
    # テストコード

    cat1 = Category('お知らせ', 'news')
    cat2 = Category('技術', 'technology')
    cat1.add()
    cat2.add()

    tag1 = Tag('タグ１', 'tag1')
    tag2 = Tag('タグ２', 'tag2')
    tag1.add()
    tag2.add()

    art = Article(
        title='ブログを開設しました！',
        thumbnail='![画像の代替テキスト](画像パス)',
        contents='## マークダウン形式のコンテンツ',
        description='ブログを開設しました。ここは記事の詳細で、抜粋としても使われます。',
        author='rightcode',
        slug='create-blog',
        category='news',
        tags=['tag1', 'tag2'],
    )
    art.add()
