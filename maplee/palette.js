(() => {
  const skin = [
    ["93604f","c78d69","e6af83","f6cda2","ffe6c0"],
    ["8f5d46","b7805f","d7a67d","edc495","f4d7ae"],
    ["70503c","9e7354","ba9365","d6b682","e7ca98"],
    ["65392e","8f5440","ac6b4e","cd9268","ecc092"],
    ["482b29","674030","89543c","a86d50","c28d66"],
  ];
  const hair = [
    ["141923","29283a","403a50","5e5266","89788d"],
    ["37232c","59342f","824f3b","a66c4b","cb946e"],
    ["584339","8b6d47","b79758","dcbc73","f5de9f"],
    ["481f2d","733141","a64c49","d36c49","f49862"],
    ["3b435a","626983","8992a9","b8bed0","e3e4e8"],
    ["352646","523864","774e8b","9c6eb0","c79ed8"],
    ["1e364c","255567","327b82","52a8a5","80cebb"],
  ];
  const originalHair = ["342b40","51394d","755265","a57784","cc9aa1"];
  window.mapleePortrait = (image,row,skinIndex,hairIndex,full) => {
    const canvas = document.createElement("canvas");
    canvas.width = full ? 2400 : 80;
    canvas.height = 80;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(image,0,row*80,canvas.width,80,0,0,canvas.width,80);
    const pixels = ctx.getImageData(0,0,canvas.width,80);
    const replacements = new Map();
    const add = (from,to) => from.forEach((color,index) =>
      replacements.set(parseInt(color,16),parseInt(to[index],16)));
    add(skin[0],skin[skinIndex] || skin[0]);
    add(originalHair,hair[hairIndex] || hair[0]);
    for (let i=0; i<pixels.data.length; i+=4) {
      if (!pixels.data[i+3]) continue;
      const color = replacements.get((pixels.data[i]<<16)|(pixels.data[i+1]<<8)|pixels.data[i+2]);
      if (color === undefined) continue;
      pixels.data[i] = color >> 16;
      pixels.data[i+1] = (color >> 8) & 255;
      pixels.data[i+2] = color & 255;
    }
    ctx.putImageData(pixels,0,0);
    return canvas;
  };
})();

window.mapleeRequest = async (method, path, json, keepalive, callback) => {
  try {
    const options = { method, credentials: "same-origin", keepalive };
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
