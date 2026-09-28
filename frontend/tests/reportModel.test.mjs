import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import ts from 'typescript'

const code = ts.transpileModule(readFileSync(new URL('../src/components/reportModel.ts', import.meta.url), 'utf8'), {compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2020}}).outputText
const { checksFor, isCurrent, todayJD, GRAHAS } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`)
const makeBundle = () => ({
 chart:{time_known:true,planets:Object.fromEntries(GRAHAS.map(name=>[name,{name,sign:0,sign_name:'Aries',degree_str:'10°',house:1,dignity:'friendly sign'}]))},
 vargas:{D9:{planets:Object.fromEntries(GRAHAS.map(name=>[name,{sign:0,sign_name:'Aries',dignity:'own sign'}]))}},
 ashtakavarga:{bav:Object.fromEntries(GRAHAS.slice(0,7).map(name=>[name,[5]]))},
})
test('every graha has five explained checks; lunar nodes do not get invented dignity or bindus',()=>{
 const b=makeBundle()
 for(const name of GRAHAS){const checks=checksFor(b,b.chart.planets[name]);assert.equal(checks.length,5);assert(checks.every(c=>c.reason&&c.rule))}
 for(const name of ['Rahu','Ketu']){const checks=checksFor(b,b.chart.planets[name]);for(const i of [0,3,4])assert.equal(checks[i].unavailable,true)}
})
test('unknown birth time suppresses house, D9 and points assessments',()=>{
 const b=makeBundle();b.chart.time_known=false
 const checks=checksFor(b,b.chart.planets.Sun)
 for(const i of [1,3,4])assert.equal(checks[i].unavailable,true)
})
test('zero points are an assessed effort result, not missing data',()=>{
 const b=makeBundle();b.ashtakavarga.bav.Sun=[0]
 assert.equal(checksFor(b,b.chart.planets.Sun)[4].result,'More hard work')
 assert.equal(checksFor(b,b.chart.planets.Sun)[4].unavailable,undefined)
 delete b.ashtakavarga.bav.Sun
 assert.equal(checksFor(b,b.chart.planets.Sun)[4].unavailable,true)
})
test('period boundaries are start-inclusive/end-exclusive and UTC Julian conversion is correct',()=>{
 assert.equal(todayJD(new Date('2000-01-01T12:00:00Z')),2451545)
 assert(isCurrent(10,20,10));assert(!isCurrent(10,20,20));assert(!isCurrent(10,20,9))
})
