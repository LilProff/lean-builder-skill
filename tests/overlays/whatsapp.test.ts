import { test } from "node:test";
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import {
  extractTextMessages,
  verifyMetaChallenge,
  verifyMetaSignature,
} from "../../shared/overlays/whatsapp-webhook-worker/files/src/whatsapp.ts";

test("challenge echoes when token matches", () => {
  const p = new URLSearchParams({ "hub.mode": "subscribe", "hub.verify_token": "tok", "hub.challenge": "123" });
  assert.equal(verifyMetaChallenge(p, "tok"), "123");
});

test("challenge null on wrong token", () => {
  const p = new URLSearchParams({ "hub.mode": "subscribe", "hub.verify_token": "bad", "hub.challenge": "123" });
  assert.equal(verifyMetaChallenge(p, "tok"), null);
});

const body = JSON.stringify({ object: "whatsapp_business_account" });
const header = "sha256=" + createHmac("sha256", "appsecret").update(body).digest("hex");

test("meta signature valid", async () => {
  assert.equal(await verifyMetaSignature(body, header, "appsecret"), true);
});

test("meta signature invalid", async () => {
  assert.equal(await verifyMetaSignature(body + "x", header, "appsecret"), false);
  assert.equal(await verifyMetaSignature(body, null, "appsecret"), false);
  assert.equal(await verifyMetaSignature(body, header.replace("sha256=", ""), "appsecret"), false);
});

test("extracts text messages, ignores statuses and non-text", () => {
  const payload = {
    entry: [{
      changes: [{
        value: {
          messages: [
            { from: "2348000000000", id: "m1", type: "text", text: { body: "How much?" } },
            { from: "2348000000000", id: "m2", type: "image", image: { id: "x" } },
          ],
          statuses: [{ id: "s1", status: "delivered" }],
        },
      }],
    }],
  };
  assert.deepEqual(extractTextMessages(payload), [{ from: "2348000000000", text: "How much?", id: "m1" }]);
});

test("garbage payload gives no messages", () => {
  assert.deepEqual(extractTextMessages(null), []);
  assert.deepEqual(extractTextMessages({ entry: "x" }), []);
});
