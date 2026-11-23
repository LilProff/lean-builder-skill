// Cloudflare Worker (Hono) for the WhatsApp Cloud API. Install: npm install hono
// Env vars (Cloudflare dashboard or `wrangler secret put`, never in the repo):
//   WHATSAPP_VERIFY_TOKEN, WHATSAPP_APP_SECRET, WHATSAPP_TOKEN, WHATSAPP_PHONE_ID,
//   OPENROUTER_API_KEY, OPENROUTER_MODELS (comma-separated: free models first, one paid model last)
import { Hono } from "hono";
import { complete } from "./openrouter";
import { extractTextMessages, verifyMetaChallenge, verifyMetaSignature, type IncomingText } from "./whatsapp";

type Env = {
  WHATSAPP_VERIFY_TOKEN: string;
  WHATSAPP_APP_SECRET: string;
  WHATSAPP_TOKEN: string;
  WHATSAPP_PHONE_ID: string;
  OPENROUTER_API_KEY: string;
  OPENROUTER_MODELS: string;
};

const GRAPH_VERSION = "v21.0"; // check Meta's current Graph API version before deploying

const app = new Hono<{ Bindings: Env }>();

app.get("/webhook", (c) => {
  const challenge = verifyMetaChallenge(new URL(c.req.url).searchParams, c.env.WHATSAPP_VERIFY_TOKEN);
  return challenge ? c.text(challenge) : c.text("Forbidden", 403);
});

app.post("/webhook", async (c) => {
  const raw = await c.req.text();
  const ok = await verifyMetaSignature(raw, c.req.header("x-hub-signature-256") ?? null, c.env.WHATSAPP_APP_SECRET);
  if (!ok) return c.text("Invalid signature", 401);
  const messages = extractTextMessages(JSON.parse(raw));
  c.executionCtx.waitUntil(Promise.all(messages.map((m) => reply(m, c.env))));
  return c.text("OK"); // answer fast; Meta retries slow webhooks
});

async function reply(message: IncomingText, env: Env): Promise<void> {
  // AGENT LOGIC GOES HERE: add your system prompt, memory lookup and tools.
  const answer = await complete([{ role: "user", content: message.text }], {
    apiKey: env.OPENROUTER_API_KEY,
    models: env.OPENROUTER_MODELS.split(",").map((m) => m.trim()).filter(Boolean),
    fetchFn: fetch,
  });
  await fetch(`https://graph.facebook.com/${GRAPH_VERSION}/${env.WHATSAPP_PHONE_ID}/messages`, {
    method: "POST",
    headers: { Authorization: `Bearer ${env.WHATSAPP_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ messaging_product: "whatsapp", to: message.from, type: "text", text: { body: answer.text } }),
  });
}

export default app;
