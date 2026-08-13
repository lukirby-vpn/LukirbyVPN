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
    throw new Error(`Fetch error ${response.status}: ${url}`);
  }

  try {
    return await response.json();
  } catch {
    throw new Error(`Invalid JSON: ${url}`);
  }
}

async function buildSubscription(orderFile) {
  const order = await fetchJSON(
    `${REPO_RAW_BASE}/${orderFile}`
  );

  if (!Array.isArray(order)) {
    throw new Error(`${orderFile} must contain an array`);
  }

  return await Promise.all(
    order.map(async (name) => {
      if (
        typeof name !== "string" ||
        !/^[a-zA-Z0-9._-]+$/.test(name)
      ) {
        throw new Error(`Invalid server name: ${name}`);
      }

      return await fetchJSON(
        `${REPO_RAW_BASE}/servers/${name}.json`
      );
    })
  );
}

export default async function handler(request) {
  if (request.method !== "GET") {
    return new Response("Method Not Allowed", {
      status: 405
    });
  }

  try {
    const url = new URL(request.url);

    const isDev = url.pathname === "/api/dev";

    const orderFile = isDev
      ? "dev-order.json"
      : "order.json";

    const servers = await buildSubscription(orderFile);

    const announce = isDev
      ? "🛠️ LukirbyVPN DEV — экспериментальная подписка"
      : "Не работает? Нажмите 🔄\nЛУЧШИЙ ВПН ДЛЯ BRAWL STARS!🔥";

    return new Response(
      JSON.stringify(servers),
      {
        status: 200,
        headers: {
          "Content-Type": "application/json",

          "profile-title": isDev
            ? "Lukirby VPN DEV"
            : "Lukirby VPN",

          "profile-update-interval": "1",

          "support-url":
            "https://t.me/LukirbyVPN",

          "announce":
            "base64:" +
            toBase64UTF8(announce),

          "Cache-Control": "no-store"
        }
      }
    );

  } catch (error) {
    return new Response(
      "Subscription error: " + error.message,
      {
        status: 500,
        headers: {
          "Content-Type": "text/plain",
          "Cache-Control": "no-store"
        }
      }
    );
  }
}
