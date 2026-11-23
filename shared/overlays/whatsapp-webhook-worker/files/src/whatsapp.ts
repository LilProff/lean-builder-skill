// WhatsApp Cloud API webhook helpers. Web platform only, so they run on Workers and Node.

const encoder = new TextEncoder();

function toHex(buffer: ArrayBuffer): string {
  return Array.from(new Uint8Array(buffer), (b) => b.toString(16).padStart(2, "0")).join("");
}

function sameText(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/** GET verification from Meta: return the challenge to echo, or null to refuse. */
export function verifyMetaChallenge(params: URLSearchParams, verifyToken: string): string | null {
  if (!verifyToken) return null;
  if (params.get("hub.mode") === "subscribe" && params.get("hub.verify_token") === verifyToken) {
    return params.get("hub.challenge");
  }
  return null;
}

/** Check X-Hub-Signature-256 ("sha256=<hex>"): HMAC SHA-256 of the raw body with your app secret. */
export async function verifyMetaSignature(rawBody: string, header: string | null, appSecret: string): Promise<boolean> {
  if (!header || !appSecret || !header.startsWith("sha256=")) return false;
  const key = await crypto.subtle.importKey("raw", encoder.encode(appSecret), { name: "HMAC", hash: "SHA-256" }, false, [
    "sign",
  ]);
  const expected = toHex(await crypto.subtle.sign("HMAC", key, encoder.encode(rawBody)));
  return sameText(expected, header.slice("sha256=".length).toLowerCase());
}

export type IncomingText = { from: string; text: string; id: string };

/** Pull the text messages out of a webhook payload. Ignores delivery statuses and media. */
export function extractTextMessages(payload: unknown): IncomingText[] {
  const out: IncomingText[] = [];
  const entries = (payload as { entry?: unknown })?.entry;
  if (!Array.isArray(entries)) return out;
  for (const entry of entries) {
    const changes = (entry as { changes?: unknown })?.changes;
    if (!Array.isArray(changes)) continue;
    for (const change of changes) {
      const messages = (change as { value?: { messages?: unknown } })?.value?.messages;
      if (!Array.isArray(messages)) continue;
      for (const m of messages as Array<Record<string, any>>) {
        if (m?.type === "text" && typeof m.text?.body === "string") {
          out.push({ from: String(m.from), text: m.text.body, id: String(m.id) });
        }
      }
    }
  }
  return out;
}
