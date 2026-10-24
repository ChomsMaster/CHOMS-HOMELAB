#!/usr/bin/env bash
set -euo pipefail
set +x

remote="chomsmaster@10.10.10.3"
port="2222"
remote_dir="/home/chomsmaster/choms-external-monitor"
ssh_opts=(-F /dev/null -p "$port")

umask 077
temp_dir="$(mktemp -d)"
cleanup() {
  unset bot_token chat_id
  rm -f -- "${temp_dir}/telegram-bot-token" "${temp_dir}/telegram-chat-id"
  rmdir -- "$temp_dir"
}
trap cleanup EXIT HUP INT TERM

IFS= read -r -s -p "Telegram bot token: " bot_token
printf '\n' >&2
[[ "$bot_token" =~ ^[0-9]{6,12}:[A-Za-z0-9_-]{30,64}$ ]] || { echo "ERROR: invalid token format" >&2; exit 1; }
IFS= read -r -s -p "Telegram chat_id: " chat_id
printf '\n' >&2
[[ "$chat_id" =~ ^-?[0-9]+$ && "$chat_id" != "0" ]] || { echo "ERROR: invalid chat_id" >&2; exit 1; }
printf %s "$bot_token" >"${temp_dir}/telegram-bot-token"
printf %s "$chat_id" >"${temp_dir}/telegram-chat-id"
unset bot_token chat_id

ssh "${ssh_opts[@]}" "$remote" "install -d -m 0700 '${remote_dir}/secrets' '${remote_dir}/state'"
scp -F /dev/null -P "$port" "${temp_dir}/telegram-bot-token" "${temp_dir}/telegram-chat-id" "${remote}:${remote_dir}/secrets/"
ssh "${ssh_opts[@]}" "$remote" "chmod 0600 '${remote_dir}/secrets/telegram-bot-token' '${remote_dir}/secrets/telegram-chat-id'; cd '${remote_dir}'; docker compose up -d --build --no-deps monitor; docker compose exec -T monitor python3 /app/monitor.py --test-notifications"

echo "Synthetic FIRING and RESOLVED were sent. Confirm both in Telegram now."
IFS= read -r -p "Type yes after confirming both messages: " confirmed
[[ "$confirmed" == "yes" ]] || { echo "ERROR: notification receipt not confirmed" >&2; exit 1; }
ssh "${ssh_opts[@]}" "$remote" "touch '${remote_dir}/notification-test-confirmed'"
echo "Credentials installed and notification pair confirmed."
