#!/usr/bin/env bash
cd wikiDerby && ./manage.py runserver &
sleep 1

URL=http://127.0.0.1:8000
[[ -x $BROWSER ]] && exec "$BROWSER" "$URL"
path=$(which xdg-open || which gnome-open) && exec "$path" "$URL"
echo "Can't find browser"