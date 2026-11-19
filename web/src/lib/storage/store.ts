/**
 * Workflow Library persistence.
 *
 * `WorkflowStore` is the async interface the UI depends on. The MVP backend is
 * `LocalWorkflowStore` over a key-value backend (browser localStorage, or an
 * in-memory map for tests). A cloud store can implement the same interface.
 * Credentials are never stored here.
 */
import { parseWorkflow, type Workflow } from "../workflow/schema";

export interface WorkflowSummary {
  id: string;
  name: string;
  updatedAt: string;
  createdAt: string;
  nodeCount: number;
  edgeCount: number;
  versionCount: number;
}

export interface WorkflowVersion {
  versionId: string;
  number: number;
  savedAt: string;
  note: string;
  workflow: Workflow;
}

export interface WorkflowStore {
  list(): Promise<WorkflowSummary[]>;
  get(id: string): Promise<Workflow | null>;
  /** Save the workflow as a new version (creates the entry if new). */
  save(workflow: Workflow, note?: string): Promise<WorkflowVersion>;
  rename(id: string, name: string): Promise<void>;
  duplicate(id: string, newId: string): Promise<Workflow>;
  remove(id: string): Promise<void>;
  listVersions(id: string): Promise<WorkflowVersion[]>;
  /** Restore an older version by saving it as the newest version. */
  restoreVersion(id: string, versionId: string): Promise<WorkflowVersion>;
}

export interface KeyValueBackend {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export class MemoryBackend implements KeyValueBackend {
  private map = new Map<string, string>();
  getItem(k: string) {
    return this.map.has(k) ? this.map.get(k)! : null;
  }
  setItem(k: string, v: string) {
    this.map.set(k, v);
  }
  removeItem(k: string) {
    this.map.delete(k);
  }
}

interface Entry {
  id: string;
  createdAt: string;
  versions: WorkflowVersion[];
}

interface LibraryFile {
  formatVersion: 1;
  entries: Entry[];
}

export const STORAGE_KEY = "modelflow.library.v1";
export const MAX_VERSIONS_PER_WORKFLOW = 50;

export class LocalWorkflowStore implements WorkflowStore {
  constructor(
    private backend: KeyValueBackend,
    private clock: () => string = () => new Date().toISOString(),
    private key = STORAGE_KEY,
  ) {}

  private read(): LibraryFile {
    const raw = this.backend.getItem(this.key);
    if (!raw) return { formatVersion: 1, entries: [] };
    try {
      const data = JSON.parse(raw) as LibraryFile;
      if (data?.formatVersion !== 1 || !Array.isArray(data.entries)) return { formatVersion: 1, entries: [] };
      // Drop any version whose workflow no longer parses.
      data.entries = data.entries
        .map((e) => ({ ...e, versions: e.versions.filter((v) => parseWorkflow(v.workflow).ok) }))
        .filter((e) => e.versions.length > 0);
      return data;
    } catch {
      return { formatVersion: 1, entries: [] };
    }
  }

  private write(file: LibraryFile) {
    this.backend.setItem(this.key, JSON.stringify(file));
  }

  private latest(e: Entry): WorkflowVersion {
    return e.versions[e.versions.length - 1];
  }

  private nextVersionId(e: Entry | undefined): { id: string; number: number } {
    const number = e ? Math.max(...e.versions.map((v) => v.number)) + 1 : 1;
    return { id: `v${number}`, number };
  }

  async list(): Promise<WorkflowSummary[]> {
    return this.read()
      .entries.map((e) => {
        const w = this.latest(e).workflow;
        return {
          id: e.id,
          name: w.name,
          createdAt: e.createdAt,
          updatedAt: this.latest(e).savedAt,
          nodeCount: w.nodes.length,
          edgeCount: w.edges.length,
          versionCount: e.versions.length,
        };
      })
      .sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : a.updatedAt > b.updatedAt ? -1 : 0));
  }

  async get(id: string): Promise<Workflow | null> {
    const e = this.read().entries.find((x) => x.id === id);
    return e ? structuredClone(this.latest(e).workflow) : null;
  }

  async save(workflow: Workflow, note = ""): Promise<WorkflowVersion> {
    const file = this.read();
    const now = this.clock();
    let entry = file.entries.find((x) => x.id === workflow.id);
    const { id, number } = this.nextVersionId(entry);
    const version: WorkflowVersion = {
      versionId: id,
      number,
      savedAt: now,
      note,
      workflow: structuredClone({ ...workflow, meta: { ...workflow.meta, updatedAt: now } }),
    };
    if (!entry) {
      entry = { id: workflow.id, createdAt: now, versions: [] };
      file.entries.push(entry);
    }
    entry.versions.push(version);
    if (entry.versions.length > MAX_VERSIONS_PER_WORKFLOW) entry.versions.splice(0, entry.versions.length - MAX_VERSIONS_PER_WORKFLOW);
    this.write(file);
    return structuredClone(version);
  }

  async rename(id: string, name: string): Promise<void> {
    const w = await this.get(id);
    if (!w) throw new Error(`Workflow ${id} not found`);
    const trimmed = name.trim();
    if (!trimmed) throw new Error("Name cannot be empty");
    await this.save({ ...w, name: trimmed }, `Renamed to "${trimmed}"`);
  }

  async duplicate(id: string, newId: string): Promise<Workflow> {
    const w = await this.get(id);
    if (!w) throw new Error(`Workflow ${id} not found`);
    if (this.read().entries.some((e) => e.id === newId)) throw new Error(`Workflow ${newId} already exists`);
    const now = this.clock();
    const copy: Workflow = { ...w, id: newId, name: `${w.name} (copy)`, meta: { ...w.meta, createdAt: now, updatedAt: now } };
    await this.save(copy, `Duplicated from "${w.name}"`);
    return copy;
  }

  async remove(id: string): Promise<void> {
    const file = this.read();
    file.entries = file.entries.filter((e) => e.id !== id);
    this.write(file);
  }

  async listVersions(id: string): Promise<WorkflowVersion[]> {
    const e = this.read().entries.find((x) => x.id === id);
    return e ? structuredClone([...e.versions].reverse()) : [];
  }

  async restoreVersion(id: string, versionId: string): Promise<WorkflowVersion> {
    const e = this.read().entries.find((x) => x.id === id);
    const v = e?.versions.find((x) => x.versionId === versionId);
    if (!e || !v) throw new Error(`Version ${versionId} of ${id} not found`);
    return this.save(v.workflow, `Restored version ${v.number}`);
  }
}

/** Browser store; falls back to memory when localStorage is unavailable. */
export function browserStore(): WorkflowStore {
  let backend: KeyValueBackend;
  try {
    const ls = window.localStorage;
    const probe = "__modelflow_probe__";
    ls.setItem(probe, "1");
    ls.removeItem(probe);
    backend = ls;
  } catch {
    backend = new MemoryBackend();
  }
  return new LocalWorkflowStore(backend);
}
