const GIST_URL = "https://gist.githubusercontent.com/lukirby-vpn/c091eaa8e1f439828c57d9ec12a1d2b1/raw/6b2f59d0e95001b2dfcdbdf3cdbe4ecf12e89e8c/subscription.json";

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

    return new Response(body, {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "profile-title": "Lukirby VPN",
        "profile-update-interval": "1",
        "subscription-userinfo": "upload=0; download=0; total=107374182400; expire=1790951622",
        "support-url": "https://t.me/LukirbyVPN",
        "announce": "Не работает? Нажмите 🔄 | ЛУЧШИЙ ВПН ДЛЯ BRAWL STARS!🔥",
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
