const REPO_RAW_BASE =
  "https://raw.githubusercontent.com/lukirby-vpn/LukirbyVPN/main";

const BACKEND_URL =
  "https://lukirby-backend.onrender.com";


// =========================================================
// BASE64 UTF-8
// =========================================================

function toBase64UTF8(text) {

  const bytes =
    new TextEncoder().encode(text);

  let binary = "";

  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }

  return btoa(binary);
}


// =========================================================
// FETCH JSON
// =========================================================

async function fetchJSON(url) {

  const response =
    await fetch(url, {

      headers: {
        "User-Agent":
          "Lukirby-VPN-Subscription"
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


// =========================================================
// GET DEVICE BY HWID
// =========================================================

async function getHWIDStatus(
  token,
  hwid
) {

  const url =
    `${BACKEND_URL}/api/subscriptions/` +
    `${encodeURIComponent(token)}` +
    `/hwid-status/` +
    `${encodeURIComponent(hwid)}`;

  const response =
    await fetch(url, {

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


// =========================================================
// REGISTER HWID
// =========================================================

async function registerHWID(
  token,
  hwid,
  name
) {

  const response =
    await fetch(
      `${BACKEND_URL}/api/hwid`,
      {

        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          "User-Agent":
            "Lukirby-VPN-Subscription"
        },

        body: JSON.stringify({

          token:
            token,

          hwid:
            hwid,

          name:
            name ||
            "Unknown device"
        }),

        cache: "no-store"
      }
    );

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


// =========================================================
// GET SERVER FILE
// =========================================================

async function getServerFile(
  filename
) {

  return await fetchJSON(
    `${REPO_RAW_BASE}/servers/${filename}`
  );
}


// =========================================================
// RESPONSE HEADERS
// =========================================================

function responseHeaders(
  announce
) {

  const headers = {

    "Content-Type":
      "application/json",

    "profile-title":
      "Ook VPN",

    "profile-update-interval":
      "1",

    "support-url":
      "https://t.me/LukirbyVPN",

    // =====================================================
    // HAPP HWID
    // =====================================================

    "subscription-always-hwid-enable":
      "1",

    "subscription-userinfo":
      "upload=0; download=0; total=0; expire=3383251200",
  
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


// =========================================================
// MAIN
// =========================================================

export default {

  async fetch(request) {

    // -----------------------------------------------------
    // ONLY GET
    // -----------------------------------------------------

    if (
      request.method !==
      "GET"
    ) {

      return new Response(
        "Method Not Allowed",
        {
          status: 405
        }
      );
    }


    try {

      const url =
        new URL(
          request.url
        );


      // ===================================================
      // TOKEN
      // ===================================================

      const token =
        url.searchParams.get(
          "token"
        );


      if (!token) {

        return new Response(

          JSON.stringify({

            ok: false,

            error:
              "Missing token"

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


      // ===================================================
      // HWID
      // ===================================================
      //
      // Happ отправляет HWID в HTTP-заголовке.
      //
      // Используем оба варианта регистра,
      // чтобы не зависеть от конкретного клиента.
      //
      // ===================================================

      const hwid =
        request.headers.get(
          "X-HWID"
        ) ||
        request.headers.get(
          "x-hwid"
        );


      // ===================================================
      // ЕСЛИ HWID НЕ ПРИШЁЛ
      // ===================================================

      if (!hwid) {

        return new Response(

          JSON.stringify({

            ok: false,

            error:
              "Missing HWID"

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


      // ===================================================
      // DEVICE NAME
      // ===================================================
      //
      // Если Happ передаст модель устройства,
      // используем её.
      //
      // Иначе просто Unknown device.
      //
      // ===================================================

      const deviceModel =
        request.headers.get(
          "X-Device-Model"
        ) ||
        request.headers.get(
          "x-device-model"
        ) ||
        "Unknown device";


      // ===================================================
      // РЕГИСТРИРУЕМ HWID
      // ===================================================

      const device =
        await registerHWID(
          token,
          hwid,
          deviceModel
        );


      if (!device.ok) {

        throw new Error(
          "HWID registration failed"
        );
      }


      // ===================================================
      // УСТРОЙСТВО УДАЛЕНО
      // ===================================================

      if (
        device.status ===
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


      // ===================================================
      // ПРЕВЫШЕН ЛИМИТ
      // ===================================================
      //
      // Например:
      //
      // VIP = 5
      //
      // 5/5 → обычные сервера
      //
      // 6/5 → ВСЕ устройства этого владельца
      //        получают serverLimitReached.json
      //
      // Проверяется именно user_id владельца,
      // который backend определяет через token.
      //
      // ===================================================

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


      // ===================================================
      // ОБЫЧНАЯ ПОДПИСКА
      // ===================================================

      const order =
        await fetchJSON(
          `${REPO_RAW_BASE}/order.json`
        );


      if (
        !Array.isArray(
          order
        )
      ) {

        throw new Error(
          "order.json must contain an array"
        );
      }


      // ===================================================
      // ЗАГРУЖАЕМ СЕРВЕРА
      // ===================================================

      const servers =
        await Promise.all(

          order.map(

            async (
              name
            ) => {

              if (

                typeof name !==
                  "string" ||

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


      // ===================================================
      // ANNOUNCE
      // ===================================================

      const announce =
        "Не работает? Нажмите 🔄\n" +
        "🎮 Огромный список серверов, абсолютно бесплатно 🔥";


      // ===================================================
      // RESPONSE
      // ===================================================

      return new Response(

        JSON.stringify(
          servers
        ),

        {

          status: 200,

          headers:
            responseHeaders(
              announce
            )
        }
      );


    } catch (
      error
    ) {

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
