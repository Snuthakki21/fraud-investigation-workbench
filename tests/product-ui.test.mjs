import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import view from '../web/templates/fraud_investigation_workbench.js';
const catalog=JSON.parse(fs.readFileSync(new URL('../dist/catalog.json',import.meta.url)));
const project=catalog.projects.find(p=>p.id==='fraud_investigation_workbench');
const example=project.examples[0];
test('expanded workflow exposes computed domain evidence',()=>{
 const html=view.result(example.report);
 for(const label of ["Behavioral model laboratory", "Chronological evaluation boundaries", "Validation threshold selection", "Explainable entity scores"])assert.ok(html.includes(label),label);
});
test('all new adverse examples render without changing domain output',()=>{
 for(const example of project.examples){
  const report=structuredClone(example.report),before=JSON.stringify(report);
  const html=view.result(report);
  assert.equal(JSON.stringify(report),before);
  assert.doesNotMatch(html,/\b(?:undefined|NaN)\b/);
  assert.ok(html.length>200);
 }
});
test('expanded result retains domain-specific evidence and controlled disclosure',()=>{
 const html=view.result(example.report);
 assert.doesNotMatch(html,/guaranteed|production certified|100% accurate/i);
 assert.match(html,/<table|<dl/);
});
