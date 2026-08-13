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

export default async function handler(req, res) {
  if (req.method !== "GET") {
    return res
      .status(405)
      .send("Method Not Allowed");
  }

  try {
    // Загружаем порядок DEV-серверов
    const order = await fetchJSON(
      `${REPO_RAW_BASE}/dev-order.json`
    );

    if (!Array.isArray(order)) {
      throw new Error(
        "dev-order.json must contain an array"
      );
    }

    // Загружаем серверы в порядке dev-order.json
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

        return await fetchJSON(
          `${REPO_RAW_BASE}/servers/${name}.json`
        );
      })
    );

    const announce =
      "🛠️ LukirbyVPN DEV — экспериментальная подписка";

    return res
      .status(200)

      .setHeader(
        "Content-Type",
        "application/json"
      )

      .setHeader(
        "profile-title",
        "Lukirby VPN DEV"
      )

      .setHeader(
        "profile-update-interval",
        "1"
      )

      .setHeader(
        "support-url",
        "https://t.me/LukirbyVPN"
      )

      .setHeader(
        "announce",
        "base64:" +
          toBase64UTF8(announce)
      )

      .setHeader(
        "Cache-Control",
        "no-store"
      )

      .json(servers);

  } catch (error) {
    return res
      .status(500)

      .setHeader(
        "Content-Type",
        "text/plain"
      )

      .setHeader(
        "Cache-Control",
        "no-store"
      )

      .send(
        "DEV subscription error: " +
        error.message
      );
  }
}
