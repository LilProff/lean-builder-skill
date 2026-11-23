// Cloudflare Worker (Hono) for a Telegram bot. Install: npm install hono
// Env vars (Cloudflare dashboard or `wrangler secret put`, never in the repo):
//   TELEGRAM_BOT_TOKEN, TELEGRAM_SECRET_TOKEN (the secret_token you pass to setWebhook),
//   OPENROUTER_API_KEY, OPENROUTER_MODELS (comma-separated: free models first, one paid model last)
import { Hono } from "hono";
import { complete } from "./openrouter";
import { checkSecretToken, extractTelegramText } from "./telegram";

type Env = {
  TELEGRAM_BOT_TOKEN: string;
  TELEGRAM_SECRET_TOKEN: string;
  OPENROUTER_API_KEY: string;
  OPENROUTER_MODELS: string;
};

const app = new Hono<{ Bindings: Env }>();

app.post("/webhook", async (c) => {
  if (!checkSecretToken(c.req.header("x-telegram-bot-api-secret-token") ?? null, c.env.TELEGRAM_SECRET_TOKEN)) {
    return c.text("Forbidden", 403);
  }
  const incoming = extractTelegramText(await c.req.json());
  if (incoming) c.executionCtx.waitUntil(reply(incoming.chatId, incoming.text, c.env));
  return c.text("OK");
});

async function reply(chatId: number, text: string, env: Env): Promise<void> {
  // AGENT LOGIC GOES HERE: add your system prompt, memory lookup and tools.
  const answer = await complete([{ role: "user", content: text }], {
    apiKey: env.OPENROUTER_API_KEY,
    models: env.OPENROUTER_MODELS.split(",").map((m) => m.trim()).filter(Boolean),
    fetchFn: fetch,
  });
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text: answer.text }),
  });
}

export default app;
