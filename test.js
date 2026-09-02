const headers = new Headers({
  "Content-Type": "application/json",
  "profile-title": "LukirbyVPN Test",
  "subscription-userinfo":
    "upload=0; download=0; total=0; expire=3383251200",
  "Cache-Control": "no-store"
});

return new Response(JSON.stringify([
  {
  "dns": {
    "servers": [
      "1.1.1.1",
      "1.0.0.1"
    ],
    "queryStrategy": "UseIP"
  },
  "routing": {
    "rules": [
      {
        "type": "field",
        "protocol": [
          "bittorrent"
        ],
        "outboundTag": "direct"
      },
      {
        "domain": [
          "geosite:category-ru"
        ],
        "outboundTag": "direct"
      }
    ],
    "domainMatcher": "hybrid",
    "domainStrategy": "IPIfNonMatch"
  },
  "inbounds": [
    {
      "tag": "socks",
      "port": 10808,
      "listen": "127.0.0.1",
      "protocol": "socks",
      "settings": {
        "udp": true,
        "auth": "noauth"
      },
      "sniffing": {
        "enabled": true,
        "routeOnly": false,
        "destOverride": [
          "http",
          "tls",
          "quic"
        ]
      }
    },
    {
      "tag": "http",
      "port": 10809,
      "listen": "127.0.0.1",
      "protocol": "http",
      "settings": {
        "allowTransparent": false
      },
      "sniffing": {
        "enabled": true,
        "routeOnly": false,
        "destOverride": [
          "http",
          "tls",
          "quic"
        ]
      }
    }
  ],
  "outbounds": [
    {
      "tag": "proxy",
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "mirai.chick-team.ru",
            "port": 53570,
            "users": [
              {
                "id": "de6d0cd9-b46e-4a17-b032-8a186fd6073b",
                "encryption": "none",
                "flow": ""
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "xhttp",
        "xhttpSettings": {
          "mode": "auto",
          "host": "xnl.chick-team.ru",
          "path": "/xhttppath/",
          "extra": {
            "xmux": {
              "cMaxReuseTimes": 0,
              "maxConcurrency": "16-32",
              "maxConnections": 0,
              "hKeepAlivePeriod": 0,
              "hMaxRequestTimes": "600-900",
              "hMaxReusableSecs": "1800-3000"
            },
            "noGRPCHeader": false,
            "xPaddingBytes": "100-1000",
            "scMaxEachPostBytes": 1000000,
            "scMinPostsIntervalMs": 30,
            "scStreamUpServerSecs": "20-80"
          }
        },
        "security": "tls",
        "tlsSettings": {
          "serverName": "xnl.chick-team.ru",
          "enableSessionResumption": false,
          "fingerprint": "firefox",
          "alpn": [
            "h2",
            "http/1.1"
          ]
        }
      }
    },
    {
      "tag": "direct",
      "protocol": "freedom"
    },
    {
      "tag": "block",
      "protocol": "blackhole"
    }
  ],
  "remarks": "🇳🇱 Нидерланды #4"
  }
]), {
  status: 200,
  headers
});
