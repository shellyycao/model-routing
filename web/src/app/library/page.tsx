"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { downloadText, newId, slugify } from "@/lib/client/session";
import { browserStore, type WorkflowStore, type WorkflowSummary, type WorkflowVersion } from "@/lib/storage/store";
import { exportWorkflowJson } from "@/lib/workflow/io";

const fmtDate = (iso: string) => new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });

export default function LibraryPage() {
  const storeRef = useRef<WorkflowStore | null>(null);
  const [items, setItems] = useState<WorkflowSummary[] | null>(null);
  const [renaming, setRenaming] = useState<string | null>(null);
  const [renameText, setRenameText] = useState("");
  const [openVersions, setOpenVersions] = useState<string | null>(null);
  const [versions, setVersions] = useState<WorkflowVersion[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  // localStorage only exists in the browser, so the store is created lazily.
  const getStore = () => (storeRef.current ??= browserStore());

  const refresh = useCallback(async () => {
    const list = await (storeRef.current ??= browserStore()).list();
    setItems(list);
  }, []);

  useEffect(() => {
    let live = true;
    (storeRef.current ??= browserStore()).list().then((list) => {
      if (live) setItems(list);
    });
    return () => {
      live = false;
    };
  }, []);

  const showVersions = async (id: string) => {
    const store = getStore();
    if (openVersions === id) {
      setOpenVersions(null);
      return;
    }
    setVersions(await store.listVersions(id));
    setOpenVersions(id);
  };

  const act = async (fn: () => Promise<unknown>, msg: string) => {
    try {
      await fn();
      setMessage(msg);
      await refresh();
    } catch (e) {
      setMessage((e as Error).message);
    }
  };

  const empty = useMemo(() => items !== null && items.length === 0, [items]);

  return (
    <main className="min-h-[calc(100vh-4rem)] bg-[radial-gradient(ellipse_at_top_right,#30234753,transparent_60%)] px-5 py-12 sm:px-[max(7vw,24px)]">
      <div className="mx-auto max-w-[1100px]">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <span className="eyebrow">YOUR WORKSPACE</span>
            <h1 className="mb-2 mt-3 text-[clamp(34px,4vw,56px)] font-semibold tracking-tight">My Workflows</h1>
            <p className="text-muted">Continue where you left off. Every save is a version you can restore.</p>
          </div>
          <Link href="/studio?new=1" className="btn-primary">
            + New workflow
          </Link>
        </div>

        <p role="status" aria-live="polite" className="min-h-5 text-sm text-accent">
          {message}
        </p>

        {items === null && <p className="mt-6 text-soft">Loading…</p>}
        {empty && (
          <div className="mt-8 rounded-2xl border border-dashed border-line2 p-10 text-center">
            <p className="text-lg">No saved workflows yet.</p>
            <p className="mt-2 text-sm text-muted">
              Generate one from the <Link className="btn-text" href="/">Home page</Link> or start on an{" "}
              <Link className="btn-text" href="/studio?new=1">
                empty canvas
              </Link>
              .
            </p>
          </div>
        )}

        {items && items.length > 0 && (
          <ul className="mt-6 border-t border-line" aria-label="Saved workflows">
            {items.map((w) => (
              <li key={w.id} className="border-b border-[#343448]">
                <div className="grid grid-cols-1 items-center gap-3 px-1.5 py-5 hover:bg-[#21213160] md:grid-cols-[minmax(160px,1fr)_auto]">
                  <div className="min-w-0">
                    {renaming === w.id ? (
                      <form
                        className="flex gap-2"
                        onSubmit={(e) => {
                          e.preventDefault();
                          act(() => getStore().rename(w.id, renameText), "Renamed.").then(() => setRenaming(null));
                        }}
                      >
                        <label className="sr-only" htmlFor={`rename-${w.id}`}>
                          New name
                        </label>
                        <input id={`rename-${w.id}`} autoFocus className="field-input max-w-sm" value={renameText} onChange={(e) => setRenameText(e.target.value)} />
                        <button className="btn-secondary" type="submit">
                          Save
                        </button>
                        <button className="btn-ghost" type="button" onClick={() => setRenaming(null)}>
                          Cancel
                        </button>
                      </form>
                    ) : (
                      <Link href={`/studio?id=${encodeURIComponent(w.id)}`} className="text-lg font-semibold hover:text-accent">
                        {w.name}
                      </Link>
                    )}
                    <p className="mt-1 text-[13px] text-[#9c9cb0]">
                      {w.nodeCount} stages · {w.edgeCount} connections · {w.versionCount} version{w.versionCount === 1 ? "" : "s"} · updated {fmtDate(w.updatedAt)}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <Link href={`/studio?id=${encodeURIComponent(w.id)}`} className="btn-secondary">
                      Open
                    </Link>
                    <button
                      type="button"
                      className="btn-ghost"
                      onClick={() => {
                        setRenaming(w.id);
                        setRenameText(w.name);
                      }}
                    >
                      Rename
                    </button>
                    <button type="button" className="btn-ghost" onClick={() => act(() => getStore().duplicate(w.id, newId("wf")), `Duplicated “${w.name}”.`)}>
                      Duplicate
                    </button>
                    <button type="button" className="btn-ghost" aria-expanded={openVersions === w.id} onClick={() => showVersions(w.id)}>
                      History
                    </button>
                    <button
                      type="button"
                      className="btn-ghost"
                      onClick={async () => {
                        const full = await getStore().get(w.id);
                        if (full) downloadText(`${slugify(full.name)}.modelflow.json`, exportWorkflowJson(full));
                      }}
                    >
                      Export
                    </button>
                    <button
                      type="button"
                      className="btn-ghost hover:text-danger"
                      onClick={() => {
                        if (window.confirm(`Delete “${w.name}” and all its versions from this browser? This cannot be undone.`)) {
                          act(() => getStore().remove(w.id), `Deleted “${w.name}”.`);
                        }
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {openVersions === w.id && (
                  <ol className="mb-4 ml-2 space-y-1 border-l border-line pl-4" aria-label={`Version history of ${w.name}`}>
                    {versions.map((v, i) => (
                      <li key={v.versionId} className="flex flex-wrap items-center justify-between gap-2 py-1.5 text-sm">
                        <span>
                          <strong>v{v.number}</strong> <span className="text-muted">· {fmtDate(v.savedAt)}</span>
                          {v.note && <span className="text-soft"> · {v.note}</span>}
                          {i === 0 && <span className="pill ml-2">current</span>}
                        </span>
                        {i !== 0 && (
                          <button
                            type="button"
                            className="btn-text text-sm"
                            onClick={() =>
                              act(async () => {
                                await getStore().restoreVersion(w.id, v.versionId);
                                setVersions(await getStore().listVersions(w.id));
                              }, `Restored v${v.number} as a new version.`)
                            }
                          >
                            Restore
                          </button>
                        )}
                      </li>
                    ))}
                  </ol>
                )}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-7 text-xs text-muted">
          Saved in this browser only (localStorage). Export JSON for a portable copy. No account, no cloud sync, and no credentials are stored.
        </p>
      </div>
    </main>
  );
}
