import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const assetScript = fs.readFileSync(path.join(root, 'src/asset-data.js'), 'utf8');
const packed = assetScript.replace(/"assets\/[\w-]+\.(png|jpg)"/g, (literal, extension) => {
  const image = fs.readFileSync(path.join(root, JSON.parse(literal)));
  return JSON.stringify('data:image/' + (extension === 'jpg' ? 'jpeg' : extension) + ';base64,' + image.toString('base64'));
});
if (process.argv.includes('--asset-data')) {
  fs.writeFileSync(1, packed);
} else {
  const template = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  const stylesheet = fs.readFileSync(path.join(root, 'src/ui.css'), 'utf8');
  const html = template.replace('<link rel="stylesheet" href="src/ui.css">', '<style>\n' + stylesheet + '\n</style>').replace(/<script src="(src\/[\w-]+\.js)"><\/script>/g, (_, source) => {
    const script = source === 'src/asset-data.js' ? packed : fs.readFileSync(path.join(root, source), 'utf8');
    return '<script>\n' + script + '\n</script>';
  });
  fs.mkdirSync(path.join(root, 'dist'), {recursive: true});
  fs.writeFileSync(path.join(root, 'dist/maple-local.html'), html);
  console.log('Built dist/maple-local.html');
}
