import { describe, expect, it } from "vitest";
import { LocalWorkflowStore, MAX_VERSIONS_PER_WORKFLOW, MemoryBackend, STORAGE_KEY } from "../src/lib/storage/store";
import { wf } from "./helpers";

function makeStore() {
  let t = 0;
  const backend = new MemoryBackend();
  const clock = () => new Date(Date.UTC(2026, 10, 19, 0, 0, t++)).toISOString();
  return { store: new LocalWorkflowStore(backend, clock), backend };
}

describe("LocalWorkflowStore", () => {
  it("saves, lists and reopens", async () => {
    const { store } = makeStore();
    const w = wf(["a", "b"], [["a", "b"]]);
    const v = await store.save(w, "first");
    expect(v.number).toBe(1);
    const list = await store.list();
    expect(list).toHaveLength(1);
    expect(list[0]).toMatchObject({ id: "wf_test", nodeCount: 2, edgeCount: 1, versionCount: 1 });
    const back = await store.get("wf_test");
    expect(back?.nodes).toEqual(w.nodes);
    expect(await store.get("missing")).toBeNull();
  });

  it("keeps version history and restores old versions as a new version", async () => {
    const { store } = makeStore();
    const w = wf(["a"], []);
    await store.save(w);
    await store.save({ ...w, name: "Second" });
    const versions = await store.listVersions(w.id);
    expect(versions.map((v) => v.number)).toEqual([2, 1]);
    const restored = await store.restoreVersion(w.id, "v1");
    expect(restored.number).toBe(3);
    expect((await store.get(w.id))?.name).toBe("Test");
    expect(restored.note).toBe("Restored version 1");
  });

  it("renames, duplicates and removes", async () => {
    const { store } = makeStore();
    await store.save(wf(["a"], []));
    await store.rename("wf_test", "  Better name ");
    expect((await store.get("wf_test"))?.name).toBe("Better name");
    await expect(store.rename("wf_test", "  ")).rejects.toThrow();
    const copy = await store.duplicate("wf_test", "wf_copy");
    expect(copy.name).toBe("Better name (copy)");
    expect((await store.list()).map((s) => s.id).sort()).toEqual(["wf_copy", "wf_test"]);
    await expect(store.duplicate("wf_test", "wf_copy")).rejects.toThrow();
    await store.remove("wf_test");
    expect((await store.list()).map((s) => s.id)).toEqual(["wf_copy"]);
  });

  it("lists most recently updated first", async () => {
    const { store } = makeStore();
    await store.save({ ...wf(["a"], []), id: "one" });
    await store.save({ ...wf(["a"], []), id: "two" });
    await store.save({ ...wf(["a"], []), id: "one", name: "updated" });
    expect((await store.list()).map((s) => s.id)).toEqual(["one", "two"]);
  });

  it("caps versions per workflow", async () => {
    const { store } = makeStore();
    const w = wf(["a"], []);
    for (let i = 0; i < MAX_VERSIONS_PER_WORKFLOW + 5; i++) await store.save(w);
    const v = await store.listVersions(w.id);
    expect(v).toHaveLength(MAX_VERSIONS_PER_WORKFLOW);
    expect(v[0].number).toBe(MAX_VERSIONS_PER_WORKFLOW + 5);
  });

  it("survives corrupt storage", async () => {
    const { store, backend } = makeStore();
    backend.setItem(STORAGE_KEY, "{oops");
    expect(await store.list()).toEqual([]);
    await store.save(wf(["a"], []));
    expect(await store.list()).toHaveLength(1);
  });
});
