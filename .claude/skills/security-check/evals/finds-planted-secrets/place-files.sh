#!/usr/bin/env bash
# 問題を仕込んだプロジェクトを作る。
# 本物そっくりのダミーキーをリポジトリに置かない（GitHub の push protection に止められる）ため、
# キー・.env・data/ はここで組み立てる。
set -eu
cp -R "$(dirname "$0")/files/." .
FAKE_KEY="AIza""SyDq7FakeKeyForSecurityEval0123456a"
FAKE_KEY_ENV="AIza""SyZz9AnotherFakeKeyForEnvFile987654"
sed -i.bak "s/__FAKE_GEMINI_KEY__/$FAKE_KEY/" ai_writer/llm.py && rm ai_writer/llm.py.bak
printf 'GEMINI_API_KEY=%s\n' "$FAKE_KEY_ENV" > .env
mkdir -p data
cat > data/history.json <<'EOF'
[
  {
    "tool": "mail",
    "title": "メール返信",
    "time": "2026-11-01 09:00",
    "text": "鈴木様\n\nお世話になっております。見積書の件、11月20日までにご送付いたします。\n\n山田太郎\n090-0000-0000"
  }
]
EOF
