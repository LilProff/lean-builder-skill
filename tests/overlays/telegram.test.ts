import { test } from "node:test";
import assert from "node:assert/strict";
import {
  checkSecretToken,
  extractTelegramText,
} from "../../shared/overlays/telegram-webhook-worker/files/src/telegram.ts";

test("secret token match true", () => {
  assert.equal(checkSecretToken("abc123", "abc123"), true);
});

test("secret mismatch or missing false", () => {
  assert.equal(checkSecretToken("abc124", "abc123"), false);
  assert.equal(checkSecretToken(null, "abc123"), false);
  assert.equal(checkSecretToken("abc123", ""), false);
});

test("extracts chat id and text", () => {
  assert.deepEqual(extractTelegramText({ message: { chat: { id: 42 }, text: "sold 2 for 5k" } }),
    { chatId: 42, text: "sold 2 for 5k" });
});

test("non-text update null", () => {
  assert.equal(extractTelegramText({ message: { chat: { id: 42 }, photo: [] } }), null);
  assert.equal(extractTelegramText({ callback_query: {} }), null);
  assert.equal(extractTelegramText(null), null);
});
