import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const data={meta:JSON.parse(fs.readFileSync(path.join(root,'assets/sprites.json'),'utf8')),terrainLip:23};
for(const [key,name]of Object.entries({hero:'hero',monsters:'monsters',background:'background',terrain:'terrain'}))data[key]='data:image/png;base64,'+fs.readFileSync(path.join(root,'assets',name+'.png')).toString('base64');
const packed='const PIXEL_DATA='+JSON.stringify(data)+';';
if(process.argv.includes('--asset-data')){fs.writeFileSync(1,packed);process.exit(0)}
let html=fs.readFileSync(path.join(root,'index.html'),'utf8');
for(const name of ['world','asset-data','pixel-render'])html=html.replace('<script src="src/'+name+'.js"></script>','<script>\n'+(name==='asset-data'?packed:fs.readFileSync(path.join(root,'src',name+'.js'),'utf8'))+'\n</script>');
fs.mkdirSync(path.join(root,'dist'),{recursive:true});
fs.writeFileSync(path.join(root,'dist/maple-local.html'),html);
console.log('Built dist/maple-local.html — offline, no external assets or deployment');
