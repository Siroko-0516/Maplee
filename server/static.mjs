function asset(request) {
  if (!["GET","HEAD"].includes(request.method)) return new Response(null,{ status:405 });
  const path = new URL(request.url).pathname;
  const entry = ASSETS[path === "/" ? "/index.html" : path];
  if (!Array.isArray(entry)) return new Response("Not found",{ status:404 });
  const [type, compressed, base64] = entry;
  const headers = { "Content-Type":type, "X-Content-Type-Options":"nosniff", "X-Robots-Tag":"noindex",
    "Cache-Control":path === "/" || path === "/index.html" ? "no-cache" : "public, max-age=600" };
  let data = null;
  if (request.method !== "HEAD") {
    data = Uint8Array.fromBase64 ? Uint8Array.fromBase64(base64) : Uint8Array.from(atob(base64),c=>c.charCodeAt(0));
    if (compressed) data = new Blob([data]).stream().pipeThrough(new DecompressionStream("gzip"));
  }
  return new Response(data,{ headers });
}
