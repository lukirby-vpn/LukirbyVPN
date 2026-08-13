const REPO_RAW_BASE =
  "https://raw.githubusercontent.com/lukirby-vpn/LukirbyVPN/main";

function toBase64UTF8(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";

  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }

  return btoa(binary);
}

async function fetchJSON(url) {
  const response = await fetch(url, {
    headers: {
      "User-Agent": "Lukirby-VPN-Subscription"
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(
      `Fetch error ${response.status}: ${url}`
    );
  }

  try {
    return await response.json();
  } catch {
    throw new Error(
      `Invalid JSON: ${url}`
    );
  }
}

export default async function handler(request) {
  if (request.method !== "GET") {
    return new Response("Method Not Allowed", {
      status: 405
    });
  }

  try {
    // Получаем порядок серверов
    const order = await fetchJSON(
      `${REPO_RAW_BASE}/order.json`
    );

    if (!Array.isArray(order)) {
      throw new Error(
        "order.json must contain an array"
      );
    }

    // Загружаем серверы в порядке из order.json
    const servers = await Promise.all(
      order.map(async (name) => {
        if (
          typeof name !== "string" ||
          !/^[a-zA-Z0-9._-]+$/.test(name)
        ) {
          throw new Error(
            `Invalid server name: ${name}`
          );
        }

        const serverURL =
          `${REPO_RAW_BASE}/servers/${encodeURIComponent(name)}.json`;

        return await fetchJSON(serverURL);
      })
    );

    // Готовая подписка для Happ
    const body = JSON.stringify(servers);

    const announce =
      "Не работает? Нажмите 🔄\nЛУЧШИЙ ВПН ДЛЯ BRAWL STARS!🔥";

    return new Response(body, {
      status: 200,

      headers: {
        "Content-Type":
          "application/json",

        "profile-title":
          "Lukirby VPN",

        "profile-update-interval":
          "1",

        "support-url":
          "https://t.me/LukirbyVPN",

        "announce":
          "base64:" +
          toBase64UTF8(announce),

        "Cache-Control":
          "no-store"
      }
    });

  } catch (error) {
    return new Response(
      "Subscription error: " +
      error.message,
      {
        status: 500,

        headers: {
          "Content-Type":
            "text/plain",

          "Cache-Control":
            "no-store"
        }
      }
    );
  }
}
