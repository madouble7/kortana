import fs from 'node:fs';
import path from 'node:path';
import { DatabaseSync } from 'node:sqlite';

export interface AuthorizationRecord {
  task_id: string;
  authorized_at: string;
  authorized_by: string;
  reason: string;
  expires_at: string;
  revoked_at: string | null;
  consumed_at: string | null;
  manifest_hash: string | null;
}

/**
 * Manages human-authorized tokens for core architecture modifications using local SQLite.
 */
export class AuthorizationService {
  private static db: DatabaseSync;
  private static dbPath: string;

  static init(dbPath?: string) {
    if (this.db) {
      return; // Already initialized
    }

    // Default to an in-memory db for dev/test or local sqlite file in the quarantine workspace
    this.dbPath = dbPath || path.join(process.cwd(), 'authorization.sqlite');

    // Ensure the directory exists if not in-memory
    if (this.dbPath !== ':memory:') {
      const dir = path.dirname(this.dbPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    }

    this.db = new DatabaseSync(this.dbPath);

    this.db.exec(`
      CREATE TABLE IF NOT EXISTS task_authorizations (
        task_id TEXT PRIMARY KEY,
        authorized_at TEXT NOT NULL,
        authorized_by TEXT NOT NULL,
        reason TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        revoked_at TEXT,
        consumed_at TEXT,
        manifest_hash TEXT
      );
    `);
  }

  // Exposed for testing
  static close() {
    if (this.db) {
      this.db.close();
      (this.db as any) = undefined;
    }
  }

  static authorizeTask(
    taskId: string,
    authorizedBy: string = 'system',
    reason: string = 'Auto-approved',
    expiresInMs: number = 1000 * 60 * 60 * 24 // 24 hours
  ) {
    this.init();

    const now = new Date();
    const expiresAt = new Date(now.getTime() + expiresInMs);

    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO task_authorizations
      (task_id, authorized_at, authorized_by, reason, expires_at)
      VALUES (?, ?, ?, ?, ?)
    `);

    stmt.run(taskId, now.toISOString(), authorizedBy, reason, expiresAt.toISOString());
    console.log(`[AUTHORIZATION] Task ${taskId} has been authorized by ${authorizedBy}.`);
  }

  static isTaskAuthorized(taskId: string): boolean {
    this.init();

    const stmt = this.db.prepare(`
      SELECT * FROM task_authorizations
      WHERE task_id = ?
    `);

    const record = stmt.get(taskId) as AuthorizationRecord | undefined;

    if (!record) return false;

    if (record.revoked_at) return false;
    if (record.consumed_at) return false;

    // Check expiration
    if (new Date(record.expires_at).getTime() < Date.now()) {
      return false;
    }

    return true;
  }

  static revokeTask(taskId: string) {
    this.init();
    const stmt = this.db.prepare(`
      UPDATE task_authorizations
      SET revoked_at = ?
      WHERE task_id = ?
    `);
    stmt.run(new Date().toISOString(), taskId);
  }

  static consumeTask(taskId: string) {
    this.init();
    const stmt = this.db.prepare(`
      UPDATE task_authorizations
      SET consumed_at = ?
      WHERE task_id = ?
    `);
    stmt.run(new Date().toISOString(), taskId);
  }
}
