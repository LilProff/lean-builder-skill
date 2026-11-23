// Paystack helpers. Web platform only (crypto.subtle, fetch), so they run on Workers and Node.

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

/** Check the x-paystack-signature header: HMAC SHA-512 of the raw body, hex, keyed with your secret key. */
export async function verifyPaystackSignature(
  rawBody: string,
  signature: string | null,
  secret: string,
): Promise<boolean> {
  if (!signature || !secret) return false;
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-512" },
    false,
    ["sign"],
  );
  const expected = toHex(await crypto.subtle.sign("HMAC", key, encoder.encode(rawBody)));
  return sameText(expected, signature.toLowerCase());
}

export type VerifiedTransaction = { status: string; amountKobo: number; currency: string; reference: string };

/** Ask Paystack for the real state of a payment. Never trust the webhook body alone. */
export async function verifyTransaction(
  reference: string,
  secretKey: string,
  fetchFn: typeof fetch,
): Promise<VerifiedTransaction> {
  const res = await fetchFn(`https://api.paystack.co/transaction/verify/${encodeURIComponent(reference)}`, {
    headers: { Authorization: `Bearer ${secretKey}` },
  });
  if (!res.ok) throw new Error(`Paystack verify failed with HTTP ${res.status}`);
  const json = (await res.json()) as { status: boolean; data?: { status: string; amount: number; currency: string; reference: string } };
  if (!json.status || !json.data) throw new Error("Paystack verify returned no data");
  return {
    status: json.data.status,
    amountKobo: json.data.amount,
    currency: json.data.currency,
    reference: json.data.reference,
  };
}
