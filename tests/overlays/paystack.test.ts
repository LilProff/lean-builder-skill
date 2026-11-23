import { test } from "node:test";
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import {
  verifyPaystackSignature,
  verifyTransaction,
} from "../../shared/overlays/paystack-webhook/files/src/lib/paystack.ts";

const body = JSON.stringify({ event: "charge.success", data: { reference: "r1" } });
const secret = "test_secret_value";
const sig = createHmac("sha512", secret).update(body).digest("hex");

test("valid signature passes", async () => {
  assert.equal(await verifyPaystackSignature(body, sig, secret), true);
});

test("tampered body fails", async () => {
  assert.equal(await verifyPaystackSignature(body + " ", sig, secret), false);
});

test("missing signature fails", async () => {
  assert.equal(await verifyPaystackSignature(body, null, secret), false);
});

test("wrong secret fails", async () => {
  assert.equal(await verifyPaystackSignature(body, sig, "other"), false);
});

test("verifyTransaction maps the response and sends the key", async () => {
  let seenUrl = "";
  let seenAuth = "";
  const fake = (async (url: string, init?: RequestInit) => {
    seenUrl = url;
    seenAuth = new Headers(init?.headers).get("Authorization") ?? "";
    return new Response(JSON.stringify({ status: true, data: { status: "success", amount: 500000, currency: "NGN", reference: "r1" } }));
  }) as typeof fetch;
  const r = await verifyTransaction("r1", "k", fake);
  assert.deepEqual(r, { status: "success", amountKobo: 500000, currency: "NGN", reference: "r1" });
  assert.equal(seenUrl, "https://api.paystack.co/transaction/verify/r1");
  assert.equal(seenAuth, "Bearer k");
});

test("verifyTransaction throws on a failed API call", async () => {
  const fake = (async () => new Response("{}", { status: 401 })) as typeof fetch;
  await assert.rejects(() => verifyTransaction("r1", "k", fake));
});
