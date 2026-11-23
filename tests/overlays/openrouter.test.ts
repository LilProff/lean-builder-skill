import { test } from "node:test";
import assert from "node:assert/strict";
import { complete } from "../../shared/overlays/openrouter-client/files/src/openrouter.ts";

const messages = [{ role: "user", content: "hi" }];

function fakeFetch(statusByModel: Record<string, number>, calls: string[]) {
  return (async (_url: string, init?: RequestInit) => {
    const model = JSON.parse(String(init?.body)).model as string;
    calls.push(model);
    const status = statusByModel[model] ?? 200;
    if (status !== 200) return new Response("{}", { status });
    return new Response(JSON.stringify({ choices: [{ message: { content: `from ${model}` } }] }));
  }) as typeof fetch;
}

test("first model answers", async () => {
  const calls: string[] = [];
  const r = await complete(messages, { apiKey: "k", models: ["A", "B"], fetchFn: fakeFetch({}, calls) });
  assert.deepEqual(r, { model: "A", text: "from A", fromCache: false });
  assert.deepEqual(calls, ["A"]);
});

test("falls back after 429", async () => {
  const calls: string[] = [];
  const r = await complete(messages, { apiKey: "k", models: ["A", "B"], fetchFn: fakeFetch({ A: 429 }, calls) });
  assert.equal(r.model, "B");
  assert.deepEqual(calls, ["A", "B"]);
});

test("falls back after 503", async () => {
  const calls: string[] = [];
  const r = await complete(messages, { apiKey: "k", models: ["A", "B"], fetchFn: fakeFetch({ A: 503 }, calls) });
  assert.equal(r.model, "B");
});

test("a 401 stops at once (a bad key will not work on another model)", async () => {
  const calls: string[] = [];
  await assert.rejects(
    () => complete(messages, { apiKey: "k", models: ["A", "B"], fetchFn: fakeFetch({ A: 401 }, calls) }),
    /401/,
  );
  assert.deepEqual(calls, ["A"]);
});

test("cache hit skips fetch", async () => {
  const calls: string[] = [];
  const cache = new Map<string, string>();
  const opts = { apiKey: "k", models: ["A"], fetchFn: fakeFetch({}, calls), cache };
  await complete(messages, opts);
  const second = await complete(messages, opts);
  assert.equal(second.fromCache, true);
  assert.deepEqual(calls, ["A"]);
});

test("all fail throws with statuses", async () => {
  const calls: string[] = [];
  await assert.rejects(
    () => complete(messages, { apiKey: "k", models: ["A", "B"], fetchFn: fakeFetch({ A: 429, B: 500 }, calls) }),
    /all models failed: A 429, B 500/,
  );
});

// v0.1.1 (deferred minor): an empty answer is not cached and the next model is tried.
test("empty answer moves to next model and is not cached", async () => {
  const calls: string[] = [];
  const cache = new Map<string, string>();
  const fetchFn = (async (_url: string, init?: RequestInit) => {
    const model = JSON.parse(String(init?.body)).model as string;
    calls.push(model);
    const content = model === "A" ? "" : "real answer";
    return new Response(JSON.stringify({ choices: [{ message: { content } }] }), { status: 200 });
  }) as typeof fetch;
  const out = await complete(messages, { apiKey: "k", models: ["A", "B"], fetchFn, cache });
  assert.equal(out.model, "B");
  assert.equal(out.text, "real answer");
  assert.deepEqual(calls, ["A", "B"]);
  assert.equal([...cache.values()].some((v) => v.includes('"text":""')), false);
});
