const assert = require('assert');
const mod = require('../src/gcs/token_monitor.js');

assert.deepStrictEqual(mod.getCompactBucketsToTrigger(10, 45, [20,30,40,50]), [20,30,40]);
assert.deepStrictEqual(mod.getCompactBucketsToTrigger(20, 45, [20,30,40,50]), [30,40]);
assert.deepStrictEqual(mod.getCompactBucketsToTrigger(40, 45, [20,30,40,50]), []);
assert.strictEqual(mod.resolveMaxContext('gemini-2.5-pro'), 2097152);
assert.strictEqual(mod.resolveMaxContext('gemini-2.5-flash'), 1048576);
assert.strictEqual(mod.resolveMaxContext('unknown-model'), 1048576);
console.log('ok');
