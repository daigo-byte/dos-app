#!/usr/bin/env bash
# .gitignore を整える前に .env と data/ をコミットしてしまった状態を再現する
set -eu
cp -R "$(dirname "$0")/files/." .
# 本物そっくりのダミーキーをリポジトリに置かないよう、.env と data/ はここで作る
FAKE_KEY_ENV="AIza""SyZz9AnotherFakeKeyForEnvFile987654"
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
mv .gitignore .gitignore.final
printf '.venv/\n__pycache__/\n.gitignore.final\n' > .gitignore
git init -q
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "initial commit"
mv .gitignore.final .gitignore
git -c user.name=eval -c user.email=eval@example.com add .gitignore
git -c user.name=eval -c user.email=eval@example.com commit -qm "add gitignore"
