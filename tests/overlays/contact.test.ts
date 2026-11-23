import { test } from "node:test";
import assert from "node:assert/strict";
import { validateContact } from "../../shared/overlays/contact-form-worker/files/src/lib/contact.ts";

const good = { name: "Ada", email: "ada@example.com", message: "Hello there" };

test("valid contact passes", () => {
  const r = validateContact(good);
  assert.equal(r.ok, true);
  assert.deepEqual(r.data, good);
});

test("honeypot rejects", () => {
  assert.equal(validateContact({ ...good, website: "http://spam" }).ok, false);
});

test("bad email rejects", () => {
  const r = validateContact({ ...good, email: "not-an-email" });
  assert.equal(r.ok, false);
  assert.ok(r.errors.some((e) => e.toLowerCase().includes("email")));
});

test("empty fields reject", () => {
  assert.equal(validateContact({ name: " ", email: "a@b.co", message: "" }).ok, false);
});

test("message over 5000 characters rejects", () => {
  assert.equal(validateContact({ ...good, message: "x".repeat(5001) }).ok, false);
});

test("non-object body rejects", () => {
  assert.equal(validateContact(null).ok, false);
  assert.equal(validateContact("hi").ok, false);
});
