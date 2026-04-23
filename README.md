# Animal Manager

CLI / GUI / APIの3つのインターフェースを持つ、動物情報管理アプリケーションです。

## 機能
- 動物の登録・削除・一覧表示
- 種類や年齢によるフィルタリング（予定）

## セットアップ
### 1. 依存関係のインストール
1. リポジトリをクローンします。
2. 仮想環境を作成し、有効化します。
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
3. 依存関係をインストールします。
   ```bash
   pip install -r requirements.txt
   ```

### CLIモード (コマンドライン)
```bash
python run_cli.py
```
起動後、メニューから以下の操作が可能です。

- 動物の管理(追加, 削除, 編集等)
- リストの管理(表示, ソート, データクリア)
- 検索機能

### GUIモード (グラフィカルユーザーインターフェース)
```bash
python run_gui.py
```
起動後、以下のモードを選択することが可能です。

  - **ローカルモード**: ローカルの SQLite データベースを直接使用します。
  - **リモートモード**: API サーバーを経由して操作します。
    - **注意**: リモートモードを使用する場合、事前に別のターミナルで以下のコマンドを実行し、APIサーバー（デフォルト: ポート8080）を起動しておく必要があります。
      ```bash
      python run_api.py
      ```
    - APIを起動すると、ブラウザから `http://127.0.0.1:8080/docs` にアクセスしてAPI仕様を確認・テストできます。

## アーキテクチャ
本アプリは以下のレイヤー構造を採用しています。

- **CLI / GUI / API**: ユーザーインターフェース
- **Controller**: 入力バリデーションと各層の仲介
- **Manager (Service)**: ビジネスロジックの実装
- **Repository**: データの永続化（SQLite / APIクライアント）

```text
[ UI / API ] -> [ Controller ] -> [ Manager ] -> [ Repository ]
```

## 技術スタック
- Python 3.x
- FastAPI（API）
- Tkinter（GUI）
- pytest（テスト）

## テスト
- pytest使用
- メインロジック core / repository / GUI / APIの各レイヤーをテスト
- API/ファイルIO をmock化しテストの責務を分離

## 今後の改善
- より詳細な動物データの拡張(生年月日･親子関係など)
- 詳細情報の表示機能の追加
  - CLI：詳細表示コマンド
  - GUI：詳細ウィンドウの実装
