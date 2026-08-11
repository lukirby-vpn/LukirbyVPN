const GIST_URL = "https://gist.githubusercontent.com/lukirby-vpn/c091eaa8e1f439828c57d9ec12a1d2b1/raw/subscription.json";

function toBase64UTF8(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";

  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }

  return btoa(binary);
}

export default async (request) => {
  if (request.method !== "GET") {
    return new Response("Method Not Allowed", {
      status: 405
    });
  }

  try {
    const response = await fetch(GIST_URL, {
      headers: {
        "User-Agent": "Lukirby-VPN-Subscription"
      },
      cache: "no-store"
    });

    if (!response.ok) {
      return new Response("Gist fetch error: " + response.status, {
        status: 502
      });
    }

    const body = await response.text();

    JSON.parse(body);

    const announce = "Не работает? Нажмите 🔄\nЛУЧШИЙ ВПН ДЛЯ BRAWL STARS!🔥";

    return new Response(body, {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "profile-title": "Lukirby VPN",
        "profile-update-interval": "1",
        "subscription-userinfo": "upload=0; download=0; total=0; expire=1988150400",
        "support-url": "https://t.me/LukirbyVPN",
        "announce": "base64:" + toBase64UTF8(announce),
        "Cache-Control": "no-store"
      }
    });

  } catch (error) {
    return new Response("Subscription error: " + error.message, {
      status: 500,
      headers: {
        "Content-Type": "text/plain"
      }
    });
  }
};
