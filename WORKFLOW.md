# iPhone で依頼 → GitHub に反映 → PC で確認する手順

iPhone から Claude に開発を依頼し、成果物を GitHub リポジトリ
(`Okinaga-8/portable-out`)に反映して、PC で確認するまでの一連の流れをまとめたものです。

---

## 全体の流れ(概要)

```
[iPhone] Claude アプリで依頼を書く
   ↓
[Claude] コードを作成・コミットし、GitHub にプッシュ
   ↓
[GitHub] リポジトリに成果物が反映される
   ↓
[PC] ブラウザや git で内容を確認・実行
```

---

## 1. iPhone から依頼を出す

1. iPhone の **Claude アプリ**を開く(またはブラウザで https://claude.ai/code)。
2. **Claude Code(コーディング用のセッション)** を新規作成する。
   - リポジトリを選ぶ画面が出たら `Okinaga-8/portable-out` を選択する。
3. やってほしいことをメッセージで送る。

### 依頼文のコツ

- **何を作るか・どう動いてほしいか**を具体的に書く。
  - 例: 「"Hello Portable" と表示する hello.py を作って」
- **反映先**を一言添える。
  - 「**main に直接コミットして**」 … 確認なしで即反映(一人での実験用に手軽)
  - 「**PR で出して**」 … 変更内容を自分で確認してから Merge ボタンで反映(安全)
- 何も指定しない場合、Claude は作業用ブランチにプッシュして PR を提案することが多い。

### 依頼の例文

> 現在時刻を表示する clock.py を作って、main に直接コミットして

> hello.py のメッセージを「こんにちは」に変えて。今回は PR で出して

---

## 2. Claude が作業して GitHub に反映する

依頼を送ると、Claude がリモート環境で以下を自動で行う。

1. コードの作成・修正
2. `git commit`(変更の記録)
3. `git push`(GitHub への送信)

完了すると、チャットに結果の報告が届く。
**「プッシュしました」「main に反映しました」という報告が出るまでがワンセット**。
報告前にアプリを閉じても作業は続くが、最後に報告を確認すること。

### PR 運用の場合の追加ステップ

「PR で出して」と依頼した場合は、GitHub に Pull Request が作られる。

1. GitHub のリポジトリページ →「**Pull requests**」タブを開く
2. 該当の PR を開き、「**Files changed**」で変更差分(緑=追加、赤=削除)を確認
3. 問題なければ「**Merge pull request**」→「**Confirm merge**」で main に反映
4. マージ後に表示される「**Delete branch**」で作業ブランチを削除しておくときれい

---

## 3. PC から確認する

### 方法 A: ブラウザで見るだけ(いちばん簡単)

1. https://github.com/Okinaga-8/portable-out を開く
2. ファイル一覧に成果物が並んでいる。ファイル名をクリックすると中身が見える
3. 更新履歴を見たいときは「**Commits**」(時計アイコンまたは commit 数の表示)をクリック
   - いつ・何が変わったか、コミット単位で差分を確認できる

### 方法 B: PC に取り込んで実行する

初回だけ、リポジトリを PC にクローン(コピー)する:

```bash
git clone https://github.com/Okinaga-8/portable-out.git
cd portable-out
```

2 回目以降は、最新を取り込むだけでよい:

```bash
cd portable-out
git pull
```

そのうえで実行する(Python の場合):

```bash
python hello.py
# → Hello Portable
```

※ `git` や `python` が PC に入っていない場合は、それぞれ公式サイトからインストールする
(git: https://git-scm.com / Python: https://www.python.org)。

---

## 4. うまくいかないとき

| 症状 | 原因と対処 |
|---|---|
| Claude が「プッシュが 403 で拒否された」と言う | GitHub App の権限切れ・未インストール。https://github.com/settings/installations の「Installed GitHub Apps」に **Claude** があるか確認。なければ https://github.com/apps/claude から Install し、対象リポジトリを選ぶ |
| GitHub に反映されていない | Claude の報告を確認。「コミットした」だけで「プッシュした」と言っていない場合は「プッシュして」と追撃する |
| PC の `git pull` で最新が来ない | ブラウザで GitHub 側に反映されているか先に確認。反映済みなら `git pull origin main` を試す |
| 作業用ブランチ(`claude/...`)が残っている | GitHub の「Branches」ページ(https://github.com/Okinaga-8/portable-out/branches)でゴミ箱アイコンから削除。Claude 側からは削除できないことがある |

---

## 補足: main 直コミットと PR の使い分け

- **main 直コミット**: 速い。一人の実験・練習用リポジトリ向き。
- **PR**: main に入る前に自分の目で差分を確認できる。壊したくないリポジトリや、
  変更内容を把握してから反映したいときに使う。

依頼のたびに好きな方を指定すればよい。迷ったら PR が安全。
