---
name: add-arxiv-paper
description: 新しいarXiv投稿を山本和樹の個人サイト・研究室サイトの論文一覧と日英の活動欄に登録する。「論文のarXiv投稿」「定型更新1」や、新規プレプリントの追加を頼まれたときに使う。掲載誌が決まった論文の更新や、既存記事の文面だけの修正には使わない。
---

# 論文のarXiv投稿

入力はarXivのURLまたはID。例として `論文のarXiv投稿 https://arxiv.org/abs/2611.22029` で指定できる。既定の掲載先は個人・研究室の両サイト。依頼で掲載先が指定されている場合はその指定に従う。

1. リポジトリルートの `AGENTS.md` を読み、作業ツリーを確認して `main` を同期する。両サイトの `paper_regular.yml` と `activity.yml` で同種の既存項目を確認する。活動欄は研究室サイトの `2607.03799` と `2611.22029` が文例。
2. arXivの概要ページで、版番号なしのID、正式タイトル、著者全員と順序、初回投稿年を確認する。論文一覧の `year` は初回投稿年、活動欄の `date` は依頼で指定された掲載日（指定がなければ日本時間の作業日）とする。arXivのIDから年や日付を推測しない。雑誌掲載済みと確認できた場合はこの手順の対象外として扱う。対象論文や掲載先の判断に必要な事実を確認できない場合は、不足情報を尋ねる。
3. 既存の校正や依頼に特別な指定がなければ、確認した情報を次のコマンドに渡す。`--authors` は著者順を保ち、既存項目と同じ連記形式で指定する。`--site personal` または `--site group` で掲載先を絞れる。まず `--dry-run` で差分を確認し、同じ引数から `--dry-run` を外して適用する。PyYAMLが必要。

   ```sh
   python -B site_data/_misc/add_arxiv_paper.py 2611.22029 \
     --title 'Exact Dynamic Scaling of Quantum Jump Statistics in Monitored Many-Body Systems' \
     --authors 'Kazuki Yamamoto, Taiki Ishiyama, Toranosuke Matsubara, Kazuya Fujimoto, Tomohiro Sasamoto, and Ryusuke Hamazaki' \
     --year 2026 --activity-date 2026-11-18 --dry-run
   ```

   `paper_regular.yml` に `journal: null` のプレプリントを登録し、`activity.yml` に `label: publication` の日英記事を入れる。活動欄は `AGENTS.md` の投稿報告の文例どおり、太字の「arXiv」を論文にリンクする。既存の同じ論文や活動記事は保持し、未登録の箇所だけを補う。日英の片方が欠けている記事や、掲載済み論文が見つかった場合は、スクリプトの出力を確認して個別に扱う。依頼による例外は、実際の差分が指定どおりになるよう調整する。

4. 依頼対象の各サイトに論文と日英記事が揃い、日付順、リンク、既存項目が保たれていることを確認する。`git diff --check` と、対象の `activity.yml` に対する `python site_data/_misc/sort_presentation.py --check` を実行する。変更がある場合は `AGENTS.md` の手順で `main` にコミットし、`origin/main` に push して確認する。更新した掲載先と公開への反映状況を報告する。
