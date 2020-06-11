# Responder+Firebaseで作るブログシステム

[![python](https://img.shields.io/badge/Python-3.6%20|%203.7-blueviolet.svg?style=flat)](https://www.python.org/downloads/release/python-368/)
[![firestore](https://img.shields.io/badge/WebAPI-Responder-lightgray.svg?style=flat)](https://firebase.google.com/docs/firestore?hl=ja)
[![responder](https://img.shields.io/badge/Database-Cloud%20Firestore-orange.svg?style=flat)](https://python-responder.org/en/latest/)
[![license](https://img.shields.io/badge/LICENSE-MIT-informational.svg?style=flat)](https://python-responder.org/en/latest/)
 
本プロジェクトは連載「Responder+Firestoreで作るブログシステム」で作成されたものです．

このコードをもとに改変した使用は，MITライセンスに基づき自由です。


## Setting
詳しくは記事を参照してください。
最低限必要なのは，/private ディレクトリに以下のファイルを配置するだけです．

* keys.json
* apikey.txt

これらは，Google Firestoreのコンソールから取得可能です．

また，ドメインを取得済みであれば[sitemap_generator.py](sitemap_generator.py)のDOMAINを変更してください．
```python
DOMAIN = 'https://sample.com'  # 8行目: ここを変更
```

## 管理者ユーザの追加
```bash
$ python auth.py
email: hogehoge@sample.com
password: 
Display Name: rightcode

Success!

Result:
{'kind': ... 

```

## サンプルデータの追加
```bash
$ python models.py
```

## Run Blog system
```bash
$ python run.py
```
 
 ## 開発
[株式会社ライトコード ー WEB・モバイル・ゲーム開発に強い会社](https://rightcode.co.jp)  

## LICENSE
Copyright (c) 2020 RightCode Inc.  
Released under the MIT license  
[LICENSE.txt](LICENSE.txt)