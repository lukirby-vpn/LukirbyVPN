const REPO_RAW_BASE =
  "https://raw.githubusercontent.com/lukirby-vpn/LukirbyVPN/main";

const BACKEND_URL =
  "https://lukirby-backend.onrender.com";

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

async function getDeviceStatus(
  token,
  deviceId
) {
  const url =
    `${BACKEND_URL}/api/subscriptions/` +
    `${encodeURIComponent(token)}` +
    `/device-status/` +
    `${encodeURIComponent(deviceId)}`;

  const response = await fetch(url, {
    headers: {
      "User-Agent":
        "Lukirby-VPN-Subscription"
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(
      `Backend error ${response.status}`
    );
  }

  try {
    return await response.json();
  } catch {
    throw new Error(
      "Invalid backend JSON"
    );
  }
}

async function getServerFile(filename) {
  return await fetchJSON(
    `${REPO_RAW_BASE}/servers/${filename}`
  );
}

function responseHeaders(announce) {
  const headers = {
    "Content-Type":
      "application/json",

    "profile-title":
      "Lukirby VPN",

    "profile-update-interval":
      "1",

    "support-url":
      "https://t.me/LukirbyVPN",

    "subscription-always-hwid-enable":
      "1",

    "Cache-Control":
      "no-store"
  };

  if (announce) {
    headers["announce"] =
      "base64:" +
      toBase64UTF8(announce);
  }

  return headers;
}

export default {
  async fetch(request) {

    if (request.method !== "GET") {
      return new Response(
        "Method Not Allowed",
        {
          status: 405
        }
      );
    }

    try {
      const url =
        new URL(request.url);

      const token =
        url.searchParams.get("token");

      const deviceId =
        url.searchParams.get(
          "device_id"
        );

      if (!token) {
        return new Response(
          JSON.stringify({
            ok: false,
            error: "Missing token"
          }),
          {
            status: 400,
            headers: {
              "Content-Type":
                "application/json",
              "Cache-Control":
                "no-store"
            }
          }
        );
      }

      if (!deviceId) {
        return new Response(
          JSON.stringify({
            ok: false,
            error:
              "Missing device_id"
          }),
          {
            status: 400,
            headers: {
              "Content-Type":
                "application/json",
              "Cache-Control":
                "no-store"
            }
          }
        );
      }

      /*
       * Получаем состояние устройства
       * и состояние подписки его владельца.
       */

      const device =
        await getDeviceStatus(
          token,
          deviceId
        );

      if (!device.ok) {
        throw new Error(
          "Device status unavailable"
        );
      }

      /*
       * =================================================
       * УСТРОЙСТВО УДАЛЕНО
       * =================================================
       */

      if (
        device.device_status ===
        "removed"
      ) {

        const server =
          await getServerFile(
            "serverDeleted.json"
          );

        return new Response(
          JSON.stringify([
            server
          ]),
          {
            status: 200,

            headers:
              responseHeaders()
          }
        );
      }

      /*
       * =================================================
       * ПРЕВЫШЕН ЛИМИТ
       * =================================================
       *
       * Например:
       *
       * 5/5 → обычные сервера
       * 6/5 → ВСЕ устройства владельца
       *       получают serverLimitReached.json
       */

      if (
        device.active_devices >
        device.device_limit
      ) {

        const server =
          await getServerFile(
            "serverLimitReached.json"
          );

        return new Response(
          JSON.stringify([
            server
          ]),
          {
            status: 200,

            headers:
              responseHeaders()
          }
        );
      }

      /*
       * =================================================
       * ОБЫЧНАЯ ПОДПИСКА
       * =================================================
       */

      const order =
        await fetchJSON(
          `${REPO_RAW_BASE}/order.json`
        );

      if (!Array.isArray(order)) {
        throw new Error(
          "order.json must contain an array"
        );
      }

      const servers =
        await Promise.all(
          order.map(
            async (name) => {

              if (
                typeof name !== "string" ||
                !/^[a-zA-Z0-9._-]+$/.test(
                  name
                )
              ) {
                throw new Error(
                  `Invalid server name: ${name}`
                );
              }

              return await fetchJSON(
                `${REPO_RAW_BASE}/servers/${name}.json`
              );
            }
          )
        );

      const announce =
        "Не работает? Нажмите 🔄\n" +
        "ЛУЧШИЙ ВПН ДЛЯ BRAWL STARS!🔥";

      return new Response(
        JSON.stringify(servers),
        {
          status: 200,

          headers:
            responseHeaders(
              announce
            )
        }
      );

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
};
