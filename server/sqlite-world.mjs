import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";

export function sqliteWorld(path) {
  const db = new DatabaseSync(path);
  db.exec(readFileSync(new URL("../drizzle/0000_world.sql", import.meta.url), "utf8"));
  return {
    prepare(sql) {
      const statement = db.prepare(sql);
      function bind(...values) {
        return {
          bind,
          async first() { return statement.get(...values) ?? null; },
          async run() { return this.execute(); },
          execute() {
            if (statement.columns().length) return { results: statement.all(...values), meta: { changes: 0 } };
            const { changes } = statement.run(...values);
            return { results: [], meta: { changes } };
          }
        };
      }
      return bind();
    },
    async batch(commands) {
      db.exec("BEGIN IMMEDIATE");
      try {
        const results = commands.map(command => command.execute());
        db.exec("COMMIT");
        return results;
      } catch (error) {
        db.exec("ROLLBACK");
        throw error;
      }
    }
  };
}
