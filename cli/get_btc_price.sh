#!/bin/bash

CACHE_FILE="/tmp/btc_price_cache"
CACHE_TTL=5

if [ -f "$CACHE_FILE" ]; then
    FILE_TIME=$(stat -f %m "$CACHE_FILE")
    NOW=$(date +%s)
    if [ $((NOW - FILE_TIME)) -lt $CACHE_TTL ]; then
        PRICE=$(cat "$CACHE_FILE")
        LC_NUMERIC=en_US.UTF-8 printf "$%'d" "$PRICE"
        exit 0
    fi
fi

PRICE=$(curl -s "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT" | jq -r ".price | tonumber | round" 2>/dev/null)

if [ -n "$PRICE" ] && [ "$PRICE" != "null" ]; then
    echo "$PRICE" > "$CACHE_FILE"
    LC_NUMERIC=en_US.UTF-8 printf "$%'d" "$PRICE"
else
    if [ -f "$CACHE_FILE" ]; then
        PRICE=$(cat "$CACHE_FILE")
        LC_NUMERIC=en_US.UTF-8 printf "$%'d" "$PRICE"
    else
        echo "--"
    fi
fi
