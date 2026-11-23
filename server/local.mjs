import { createServer } from "node:http";
import { Readable } from "node:stream";
import { DatabaseSync } from "node:sqlite";
import { randomUUID } from "node:crypto";
import { mkdirSync } from "node:fs";
import worker from "../dist/server/index.js";

mkdirSync(".maplee-data", { recursive: true });
const db = new DatabaseSync(".maplee-data/accounts.sqlite");
db.exec("PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS objects (key TEXT PRIMARY KEY, value TEXT, etag TEXT)");
const get = db.prepare("SELECT value,etag FROM objects WHERE key=?");
const insert = db.prepare("INSERT OR IGNORE INTO objects VALUES (?,?,?)");
const update = db.prepare("UPDATE objects SET value=?,etag=? WHERE key=? AND etag=?");
const upsert = db.prepare("INSERT INTO objects VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,etag=excluded.etag");
const del = db.prepare("DELETE FROM objects WHERE key=?");

const SAVES = {
  async get(key) {
    const row = get.get(key);
    return row ? { etag: row.etag, json: async () => JSON.parse(row.value) } : null;
  },
  async put(key,value,options) {
    const condition = options?.onlyIf;
    const etag = randomUUID();
    const result = condition?.etagMatches ? update.run(value,etag,key,condition.etagMatches)
      : condition?.etagDoesNotMatch === "*" ? insert.run(key,value,etag) : upsert.run(key,value,etag);
    return result.changes ? { etag } : null;
  },
  async delete(key) { del.run(key); }
};
const host = "127.0.0.1";
const port = Number(process.env.MAPLEE_PORT || "8000");
createServer(async (req,res) => {
  try {
    const hasBody = !["GET","HEAD"].includes(req.method);
    const headers = new Headers(req.headers);
    headers.set("CF-Connecting-IP",req.socket.remoteAddress);
    const result = await worker.fetch(new Request(new URL(req.url,`http://${host}:${port}`),
      { method:req.method,headers, ...(hasBody ? { body:Readable.toWeb(req),duplex:"half" } : {}) }),{ SAVES });
    res.writeHead(result.status,Object.fromEntries(result.headers));
    if (result.body) Readable.fromWeb(result.body).pipe(res);
    else res.end();
  } catch {
    res.writeHead(500).end();
  }
}).listen(port,host,() => console.log(`Maplee http://${host}:${port}`));
