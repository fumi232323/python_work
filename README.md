# python_work
For python practice. python練習用。
## weather_collector,weatherscrapy　※つくりかけ  
天気予報サイトからスクレイピングした天気予報を表示する。  

* weather_collector :  Djangoアプリケーション  
* weatherscrapy : Scrapyアプリケーション  

1. weather_collectorで、天気予報を表示したい地域を選択（weatherscrapy呼び出し）
2. weatherscrapyが、天気予報サイトから天気予報をスクレイピングしてCSV出力
3. weather_collectorから、2のCSVファイルを読み込んで天気予報をDBへ保存
4. weather_collectorで、DB保存済みの天気予報を表示

### TODO 
スクレイピングしたい天気予報サイト登録機能をつくる。  
過去天気も表示したい。
