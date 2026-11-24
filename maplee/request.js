window.mapleeRequest = async (method, path, json, keepalive, callback) => {
  try {
    const options = { method, credentials: "same-origin", keepalive };
    if (path.startsWith("/api/world/") && !keepalive && typeof AbortSignal.timeout === "function") {
      options.signal = AbortSignal.timeout(4500);
    }
    if (json !== "") {
      options.headers = { "Content-Type": "application/json" };
      options.body = json;
    }
    const response = await fetch(path,options);
    callback(response.status,JSON.stringify(await response.json()));
  } catch {
    callback(0,"{}");
  }
};
