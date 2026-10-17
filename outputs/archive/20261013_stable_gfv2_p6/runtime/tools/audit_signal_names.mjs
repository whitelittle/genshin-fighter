import fs from 'node:fs';
import path from 'node:path';
import {decode, msg, num, str, all} from '../../work/node-gia-wire.mjs';

const file = process.argv[2];
if (!file) throw new Error('Usage: audit_signal_names.mjs input.gia');
const bytes = fs.readFileSync(file);
const root = decode(bytes.subarray(20, -4));
const definitions = all(root, 2).map(field => {
  const unit = decode(field.v);
  const signal = msg(msg(msg(msg(unit, 14), 1), 1), 107);
  const names = [101, 102, 108].map(kind => str(msg(signal, kind), 1)).filter(Boolean);
  return {id: num(msg(unit, 1), 4), kind: str(unit, 3), names: [...new Set(names)]};
}).filter(def => def.names.length);
const graph = msg(msg(msg(msg(root, 1), 13), 1), 1);
const counts = new Map();
for (const field of all(graph, 3)) {
  const node = decode(field.v);
  const id = num(msg(node, 2), 5);
  counts.set(id, (counts.get(id) || 0) + 1);
}
const numericStrings = new Map();
function visit(fields) {
  for (const field of fields) {
    if (field.w !== 2) continue;
    const value = field.v.toString('utf8');
    if (/^信号_\d+$/.test(value)) numericStrings.set(value, (numericStrings.get(value) || 0) + 1);
    try { visit(decode(field.v)); } catch {}
  }
}
visit(root);
console.log(JSON.stringify({filename: path.basename(file), signals: [...new Set(definitions.flatMap(def => def.names))], definitions: definitions.map(def => ({...def, referencedNodes: counts.get(def.id) || 0})), numericNameOccurrences: Object.fromEntries(numericStrings)}, null, 2));
