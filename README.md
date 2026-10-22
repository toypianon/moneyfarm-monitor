# Money Farm 新着ファームチケット通知（GitHub Actions + Telegram）

iPhoneだけで通知を受け取るための無料構成例です。GitHub Actionsが `https://moneyfarm.jp/projects` を定期取得し、前回見ていないチケットのURLが現れた場合にTelegramへ通知します。

## 仕組み・注意点
- 監視はGitHub Actionsのクラウド上で動くため、PCを起動しておく必要はありません。
- スケジュールは5分間隔を目標にしています。GitHubは実行時刻を保証せず、遅延することがあります。
- 初回実行では既存チケットを記録するだけで通知しません。2回目以降に初めて現れたチケットを通知します。
- 無料で運用する想定ですが、GitHubやTelegramの仕様・利用条件が変わる可能性があります。
- Money Farmのページ構造が変わると動かなくなる場合があります。Actionsの実行ログを確認してください。
- この仕組みはチケット掲載を知らせるだけで、購入・投資判断や申込操作は行いません。

## セットアップ

### 1. Telegramを用意する
1. iPhoneにTelegramをインストールし、アカウントを作成します。
2. Telegram内で `@BotFather` を検索し、公式BotFatherを開きます。
3. `/newbot` を送信し、案内に従ってBot名とユーザー名を設定します。
4. BotFatherから発行されたBot tokenを安全に保管します。ほかの人に公開しないでください。
5. 作成したBotを開き、`Start` を押してメッセージを1通送ります。
6. ブラウザで次のURLを開きます（`YOUR_TOKEN` は自分のtokenに置換）：
   `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
7. 結果の `message` → `chat` → `id` の数字がChat IDです。tokenや結果画面を他人に共有しないでください。

### 2. GitHubリポジトリを作る
1. GitHubにサインインし、新しいリポジトリを作ります。公開（Public）がおすすめです。秘密情報はコードに書かず、必ずSecretsに保存します。
2. このZIP内の `monitor.py`、`known_tickets.json`、`.github/workflows/monitor.yml` をリポジトリにアップロードします。
3. `known_tickets.json` は最初は `{}` にしておいてください。
4. リポジトリの **Settings → Secrets and variables → Actions → New repository secret** で以下を追加します。
   - `TELEGRAM_BOT_TOKEN`：BotFatherのtoken
   - `TELEGRAM_CHAT_ID`：上で確認したChat ID
5. **Settings → Actions → General → Workflow permissions** で、ワークフローにリポジトリへの書き込み権限を許可します（必要な場合）。
6. **Actions** タブでワークフローを有効にします。

### 3. 動作確認
1. Actionsタブで `Monitor Money Farm new tickets` を選択します。
2. `Run workflow` で手動実行します。
3. 初回は既存のチケット一覧を保存し、通知は送られません。
4. 2回目以降、初めて現れたチケットがあればTelegramへ通知します。

## うまく動かない場合
- Actionsの実行ログに `チケットのリンクを取得できませんでした` と出る場合、Money Farm側がJavaScriptで描画しているか、ページ構造が変わった可能性があります。
- `git push` が権限エラーになる場合、Settings → Actions → General のワークフロー権限を確認してください。
- 通知が来ない場合、BotをStart済みか、tokenとChat IDが正しいか、iPhoneのTelegram通知が許可されているかを確認してください。
- GitHubのスケジュール実行は遅延・欠落することがあります。数分以内の通知を保証する仕組みではありません。
