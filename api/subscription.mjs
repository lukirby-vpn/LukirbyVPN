const REPO_RAW_BASE =
  "https://github.com/lukirby-vpn/LukirbyVPN/tree/main";

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

  return await response.json();
}

export default async function handler(request) {

  if (request.method !== "GET") {
    return new Response("Method Not Allowed", {
      status: 405
    });
  }

  try {

    const order = await fetchJSON(
      `${REPO_RAW_BASE}/order.json`
    );

    if (!Array.isArray(order)) {
      throw new Error(
        "order.json must contain an array"
      );
    }

    const servers = [];

    for (const name of order) {

      if (
        typeof name !== "string" ||
        !/^[a-zA-Z0-9._-]+$/.test(name)
      ) {
        throw new Error(
          `Invalid server name: ${name}`
        );
      }

      const server = await fetchJSON(
        `${REPO_RAW_BASE}/servers/${name}.json`
      );

      servers.push(server);
    }

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

        "subscription-userinfo":
          "upload=0; download=0; total=0; expire=1988150400",

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
