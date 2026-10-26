'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=process.argv[2],lock=JSON.parse(fs.readFileSync(path.join(root,'provenance.json')));let checks=0;
function check(name,f){f();checks++;console.log('CHECK_PASS '+name)}
for(const [file,a]of Object.entries(lock.artifacts)){
 const data=fs.readFileSync(path.join(root,file));
 check(file+'_hash',()=>assert.equal(crypto.createHash('sha256').update(data).digest('hex'),a.patched_sha256));
 check(file+'_size',()=>assert.equal(data.length,a.patched_bytes));
 const text=data.toString(),original=text.replace(a.after,a.before);
 check(file+'_only_loader_changed',()=>{assert.equal(text.split(a.after).length,2);assert.equal(crypto.createHash('sha256').update(original).digest('hex'),a.original_sha256)});
 check(file+'_syntax',()=>new vm.Script(text,{filename:file}));
 let ctx={exports:{},require};vm.runInNewContext(original,ctx);let old={exports:null};ctx.exports.modules[a.module_id](old);
 check(file+'_original_fails',()=>assert.throws(()=>Reflect.apply(old.exports,undefined,['wreq-js']),e=>e.code==='MODULE_NOT_FOUND'));
 const mod=require(path.join(root,file)),fresh={exports:null};mod.modules[a.module_id](fresh);
 check(file+'_native_require',()=>assert.equal(typeof fresh.exports,'function'));
 check(file+'_runtime_websocket',()=>assert.equal(typeof Reflect.apply(fresh.exports,undefined,['wreq-js']).websocket,'function'));
 check(file+'_fail_closed_missing_module',()=>assert.throws(()=>fresh.exports('choms-synthetic-module-not-present'),e=>e.code==='MODULE_NOT_FOUND'));
}
console.log('OFFLINE_CHECKS='+checks+' NETWORK=none NO_INFERENCE=true');
