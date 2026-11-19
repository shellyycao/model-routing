/** Immutable undo/redo history. */

export interface History<T> {
  past: T[];
  present: T;
  future: T[];
}

export const HISTORY_LIMIT = 100;

export function createHistory<T>(present: T): History<T> {
  return { past: [], present, future: [] };
}

/** Record a new state; clears redo. */
export function commit<T>(h: History<T>, next: T, limit = HISTORY_LIMIT): History<T> {
  if (Object.is(next, h.present)) return h;
  const past = [...h.past, h.present];
  if (past.length > limit) past.splice(0, past.length - limit);
  return { past, present: next, future: [] };
}

/** Replace the present without recording (e.g. live drag); pair with commitFrom. */
export function replacePresent<T>(h: History<T>, next: T): History<T> {
  return { ...h, present: next };
}

/** Record `origin` as the undo point for the current present (used at drag end). */
export function commitFrom<T>(h: History<T>, origin: T, limit = HISTORY_LIMIT): History<T> {
  if (Object.is(origin, h.present)) return h;
  const past = [...h.past, origin];
  if (past.length > limit) past.splice(0, past.length - limit);
  return { past, present: h.present, future: [] };
}

export function undo<T>(h: History<T>): History<T> {
  if (!h.past.length) return h;
  const prev = h.past[h.past.length - 1];
  return { past: h.past.slice(0, -1), present: prev, future: [h.present, ...h.future] };
}

export function redo<T>(h: History<T>): History<T> {
  if (!h.future.length) return h;
  const [next, ...rest] = h.future;
  return { past: [...h.past, h.present], present: next, future: rest };
}

export const canUndo = <T,>(h: History<T>) => h.past.length > 0;
export const canRedo = <T,>(h: History<T>) => h.future.length > 0;
