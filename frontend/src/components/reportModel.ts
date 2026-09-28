import type { Bundle, Planet } from '../api/types'
export const GRAHAS = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']
const LORDS = ['Mars','Venus','Mercury','Moon','Sun','Mercury','Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']
export const THEMES: Record<string, [string,string,string]> = {
 Sun:['Surya · सूर्य','Confidence & purpose','Choose one small promise to yourself and honour it this week.'],
 Moon:['Chandra · चन्द्र','Belonging & emotional rhythms','Make space for a restful routine and a conversation with someone you trust.'],
 Mars:['Mangala · मङ्गल','Courage & initiative','Break a demanding task into small steps; pause before responding when emotions rise.'],
 Mercury:['Budha · बुध','Learning & communication','Write your thoughts down, then ask one clarifying question before deciding.'],
 Jupiter:['Guru · गुरु','Wisdom & growth','Learn something meaningful or share a useful skill.'],
 Venus:['Shukra · शुक्र','Relationships & creativity','Make room for creativity and express appreciation without expecting anything back.'],
 Saturn:['Shani · शनि','Work & steady foundations','Choose a manageable routine. Consistency and rest can work together.'],
 Rahu:['Rahu · राहु','Curiosity & new directions','Explore one new idea while keeping clear boundaries around time and spending.'],
 Ketu:['Ketu · केतु','Reflection & simplicity','Take a quiet screen-free moment and let go of one unnecessary obligation.'],
}
export const DOMAINS = ['','Identity','Money & values','Communication','Home','Creativity','Daily routines','Partnership & marriage','Shared resources','Learning','Work & vocation','Community & gains','Rest & reflection']
export type Check = { title: string; result: 'Good'|'Mixed'|'More hard work'; reason: string; rule: string; unavailable?: boolean }
export function dignityResult(value: string): Check['result'] {
 return ['exalted','moolatrikona','own sign','friendly sign'].includes(value) ? 'Good' : ['debilitated','enemy sign'].includes(value) ? 'More hard work' : 'Mixed'
}
export function checksFor(bundle: Bundle, p: Planet): Check[] {
 const known = bundle.chart.time_known
 const node = ['Rahu','Ketu'].includes(p.name)
 const lord = bundle.chart.planets[LORDS[p.sign]]
 const d9 = bundle.vargas?.D9?.planets[p.name]
 const points = bundle.ashtakavarga?.bav[p.name]?.[p.sign]
 const missing = (title: string, reason: string, rule: string): Check => ({title,result:'Mixed',reason,rule,unavailable:true})
 return [
 node ? missing('Sign setting','Schools differ on nodal dignity. No exaltation or debilitation verdict is assigned here.','Nodal dignity is deliberately unscored.') : {title:'Sign setting',result:dignityResult(p.dignity),reason:`${p.sign_name} · ${p.degree_str}. Traditional dignity: ${p.dignity}. A placement describes a practice area, not your potential.`,rule:'BPHS, Graha characteristics. App labels: exalted / moolatrikona / own / friendly = Good; debilitated / enemy = More hard work; otherwise Mixed.'},
 !known || !p.house ? missing('House setting','Add an accurate birth time to assess houses.','Birth time is required.') : {title:'House setting', result:[1,4,5,7,9,10].includes(p.house)?'Good':[6,8,12].includes(p.house)?'More hard work':'Mixed',reason:`House ${p.house} · ${DOMAINS[p.house]}. Patient, practical steps can support this area.`,rule:'App summary of traditional kendra/trikona/dusthana groups: 1,4,5,7,9,10 Good; 6,8,12 effort; others Mixed. Not a complete functional-benefic assessment.'},
 lord ? {title:'Sign-lord support',result:dignityResult(lord.dignity),reason:`${LORDS[p.sign]} hosts this sign and occupies ${lord.sign_name} (${lord.dignity}). Its setting adds context.`,rule:'Traditional sign rulership; app applies the same dignity mapping to the dispositor. Not an independent strength measurement.'} : missing('Sign-lord support','Sign-lord data is unavailable.','No inferred score.'),
 !known || !d9 || node ? missing('Navamsha setting',node?'Nodal dignity in D9 is left unscored because traditions differ.':'An accurate birth time and D9 calculation are needed.','BPHS, Sixteen divisions: Navamsha (D9).') : {title:'Navamsha setting',result:dignityResult(d9.dignity),reason:`D9: ${d9.sign_name} · ${d9.dignity}.${d9.sign===p.sign?' The sign repeats in D1 and D9 (vargottama).':''} One supporting view, not total planetary strength.`,rule:'BPHS, Sixteen divisions. D9 uses the same dignity mapping. Shadbala is not computed.'},
 !known || points === undefined ? missing('Ashtakavarga points',node?'Individual bindu tables are not assigned to Rahu and Ketu.':'The required bindu table is unavailable.','Classical Bhinna Ashtakavarga; no substitute score.') : {title:'Ashtakavarga points',result:points>=5?'Good':points===4?'Mixed':'More hard work',reason:`${points} / 8 bindus in ${p.sign_name} in ${p.name}’s own table. Build steadily with realistic expectations.`,rule:'BPHS, Ashtakavarga. App bands: 5–8 Good; 4 Mixed; 0–3 More hard work. Not a probability of success.'},
 ]
}
export const todayJD = (date = new Date()) => date.getTime()/86400000 + 2440587.5
export const isCurrent = (start: number, end: number, now: number) => start <= now && now < end
export const dateLabel = (value: string) => new Date(value.slice(0,10)+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'})
