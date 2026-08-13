import fs from "node:fs/promises";
import path from "node:path";

function toBase64UTF8(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";

  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }

  return btoa(binary);
}

async function readJSON(filePath) {
  const text = await fs.readFile(filePath, "utf8");

  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`Invalid JSON: ${filePath}`);
  }
}

export default async function handler(request) {
  if (request.method !== "GET") {
    return new Response("Method Not Allowed", {
      status: 405
    });
  }

  try {
    const root = process.cwd();

    const orderPath = path.join(
      root,
      "order.json"
    );

    const serversPath = path.join(
      root,
      "servers"
    );

    const order = await readJSON(orderPath);

    if (!Array.isArray(order)) {
      throw new Error(
        "order.json must contain an array"
      );
    }

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

        const filePath = path.join(
          serversPath,
          `${name}.json`
        );

        return await readJSON(filePath);
      })
    );

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
