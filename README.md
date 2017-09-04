# python_work
For python practice. python練習用。

## weather_collector,weatherscrapy

### システム概要:
天気予報サイトからスクレイピングした天気予報を表示するWebアプリケーション。

### 機能の説明:
#### 1. weather_collector  
Djangoを使用したWebアプリケーション。  
天気予報の表示・DB登録、スクレイピングアプリケーションの呼び出し、表示したい地域・予報サイトURLの管理を行う。
##### 1-1. weather
* 天気予報を取得・表示したいエリアを選択する
* weatherscrapyを呼び出して、選択されたエリアの天気予報を天気予報サイトからスクレイピングする
* weatherscrapyからCSV出力された天気予報を読み込みDBに登録する
* 週間天気予報(日単位の天気予報)を表示する
* 今日の天気(時間単位の天気予報)を表示する
* DB登録済みの天気予報を表示する
##### 1-2. channel
* 天気予報を表示したいサイトのURLを登録する
* 登録済みの天気予報サイトURLを変更する
* 登録済みの天気予報サイトURLを削除する
* 天気予報を表示したい地域(例:草津町)を登録する
#### 2. weatherscrapy  
Scrapyを使用したスクレイピングアプリケーション。  
天気予報サイトにアクセスし、天気予報情報をスクレイピングする。
* 指定された天気予報サイトから、天気予報をスクレイピングする
* スクレイピング対象の天気予報サイトURLをCSVファイルから読み込む
* スクレイピングした天気予報をCSV出力する

### 練習のポイント:
- Pythonに慣れる(Python==3.6.1を使用)
- Djangoを使ったWebアプリケーション作成に慣れる(Django==1.11.3を使用)
- データの永続化にRDBMSを使う(今回はPostgreSQLを使用)
    * DBに対して、登録・参照・更新・削除操作を行う(いろいろなパターンのQuerySet メソッド使ってみる)
- マイグレーションをやってみる
- 登録・登録確認・更新・削除機能を持つ画面をそれぞれ作成する
- ModelFormとプレーンなフォーム(Form)の両方を使う
- CSV入力・出力してみる(Pythonのcsvモジュールを使う。他システムとのファイル連携を想定。)
- ログ出力(コンソール、ファイル)
- フラッシュメッセージを表示する(Djangoのmessages frameworkを使う)
- 例外を処理する
- 色々なパターンのテストを書いてみる(unittest.TestCase、django.test.TestCase)
    * モックを使う(unittest.mock)
    * 一時ファイルや一時ディレクトリを使う(tempfileモジュール)
- adminサイトを使ってみる(The Django admin site)
- コードスタイルチェックをやってみる(flake8)  
※以下エラーは一旦無視しています  
    * E501 line too long
    * E122 continuation line missing indentation or outdented(テストコードのみ無視)
    * F841 local variable 'channel_daily' is assigned to but never used(テストコードのみ無視)
- Djangoアプリから他システムを呼び出してみる(subprocess.Popen)
- Scrapyをやってみる(スクレイピング用のフレームワーク)

### 次回(次に作るアプリケーション)の練習ポイント:
今回作成したアプリケーションには盛り込めなかったので、次回やってみる。
* Django
    * ユーザー認証システム
    * セッションデータの操作
    * カスタムバリデータ
* JSONを扱う(bpmappers)
* 画像処理(Pillow)
* 暗号化(PyCrypto)
* dateutil
* パッケージ作成(作ったものをパッケージ化してみる)