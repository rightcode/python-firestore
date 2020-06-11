"""
Manege Sitemap
"""
from models import get_articles
from datetime import datetime


DOMAIN = 'https://sample.com'


def update_sitemap(changefreq='monthly', priority=0.7):
    """
    sitemapを全て更新する
    カテゴリページは含めない
    :param changefreq: 記事の更新頻度
    :param priority: 記事の優先度
    :return:
    """
    # 公開済みのものだけ取得
    articles = get_articles(False)

    # URL
    locs = [
        '{}/category/{}/{}'.format(DOMAIN, article['category'], article['slug'])
        for article in articles
    ]

    # 最終更新日
    lastmods = [
        article['last_update'].strftime('%Y-%m-%d')
        for article in articles
    ]

    # 上書きする
    sitemap = open('sitemap.xml', 'w')
    sitemap.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    sitemap.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    sitemap.write('    <url>\n')
    sitemap.write('        <loc>{}/</loc>\n'.format(DOMAIN))
    sitemap.write('        <lastmod>{}</lastmod>\n'.format(datetime.now().strftime('%Y-%m-%d')))
    sitemap.write('        <changefreq>always</changefreq>\n')
    sitemap.write('        <priority>1.0</priority>\n')
    sitemap.write('    </url>\n')

    for loc, lastmod in zip(locs, lastmods):
        sitemap.write('    <url>\n')
        sitemap.write('        <loc>{}/</loc>\n'.format(loc))
        sitemap.write('        <lastmod>{}</lastmod>\n'.format(lastmod))
        sitemap.write('        <changefreq>{}</changefreq>\n'.format(changefreq))
        sitemap.write('        <priority>{}</priority>\n'.format(priority))
        sitemap.write('    </url>\n')

    sitemap.write('</urlset>\n')
    sitemap.close()

