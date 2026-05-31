#!/bin/bash

CACHE_FILE="/tmp/btc_price_cache"
CACHE_TTL=5
NOW=$(date +%s)

# 獲取價格
if [ -f "$CACHE_FILE" ]; then
    FILE_TIME=$(stat -f %m "$CACHE_FILE")
    if [ $((NOW - FILE_TIME)) -lt $CACHE_TTL ]; then
        PRICE=$(cat "$CACHE_FILE")
    fi
fi

if [ -z "$PRICE" ]; then
    PRICE=$(curl -s "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT" | jq -r ".price | tonumber | round" 2>/dev/null)
    [ -n "$PRICE" ] && [ "$PRICE" != "null" ] && echo "$PRICE" > "$CACHE_FILE"
fi

# 常駐顯示符號與價格
if [ -n "$PRICE" ] && [ "$PRICE" != "null" ]; then
    LC_NUMERIC=en_US.UTF-8 printf "₿: $%'d" "$PRICE"
else
    echo "₿: --"
fi
