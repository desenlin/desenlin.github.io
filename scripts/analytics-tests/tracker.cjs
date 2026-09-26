const fs=require('node:fs'),assert=require('node:assert/strict'),{JSDOM}=require('jsdom');
const source=fs.readFileSync(process.argv[2],'utf8');
function setup({url='https://desenlin.com/ame-quarter/',existing=false,frame=false}={}){
 const dom=new JSDOM('<html><head><script defer src="assets/analytics.js" data-ga-id="G-MDGMSFPEH2" data-project="ame-quarter"></script></head><body><main><button id="view" data-analytics-action="view_change" data-analytics-value="plan">Plan</button><input id="rent" data-analytics-action="assumption_change" data-analytics-once="true" value="PRIVATE-ANSWER"><select id="premise" data-analytics-action="premise_select" data-analytics-allowed="cafe,books"><option value="cafe">Cafe</option><option value="secret">Secret</option></select><a id="launch" href="https://desenlin.com/housing-market-lab/?private=secret" data-analytics-event="housing_market_lab_click">Open</a></main></body></html>',{url,runScripts:'outside-only'});
 const w=dom.window,callbacks={},calls=[];
 if(frame)dom.reconfigure({windowTop:{}});
 Object.defineProperty(w.document,'currentScript',{value:w.document.querySelector('script')});
 const add=w.document.addEventListener.bind(w.document);
 w.document.addEventListener=(type,fn,...args)=>{callbacks[type]=fn;return add(type,fn,...args);};
 if(existing)w.gtag=(...args)=>calls.push(args);
 w.eval(source);
 const events=()=>existing?calls:Array.from(w.dataLayer||[],args=>Array.from(args));
 const fire=(id,type='click',trusted=true)=>callbacks[type]?.({target:w.document.getElementById(id),type,isTrusted:trusted});
 return {dom,w,events,fire};
}
let s=setup();assert.equal(s.events().filter(x=>x[0]==='config').length,1);s.w.eval(source);assert.equal(s.events().filter(x=>x[0]==='config').length,1);s.dom.window.close();
s=setup({existing:true});assert.equal(s.events().length,0);s.fire('view','click',false);assert.equal(s.events().length,0);s.fire('view');s.fire('view');assert.equal(s.events().filter(x=>x[1]==='activity_start').length,1);assert.equal(s.events().filter(x=>x[1]==='view_change').length,2);
s.fire('rent','change');s.fire('rent','change');assert.equal(s.events().filter(x=>x[1]==='assumption_change').length,1);assert.ok(!JSON.stringify(s.events()).includes('PRIVATE-ANSWER'));
s.fire('premise','change');assert.equal(s.events().find(x=>x[1]==='premise_select')[2].action_value,'cafe');s.w.document.getElementById('premise').value='secret';s.fire('premise','change');assert.ok(!JSON.stringify(s.events()).includes('secret'));
s.fire('launch');assert.equal(s.events().filter(x=>x[1]==='lab_launch').length,1);assert.equal(s.events().filter(x=>x[1]==='housing_market_lab_click').length,1);assert.ok(!JSON.stringify(s.events()).includes('private='));s.dom.window.close();
for(const options of [{frame:true},{url:'file:///example.html'},{url:'http://localhost/'}]){s=setup(options);assert.equal(s.events().length,0);assert.equal(s.w.document.querySelectorAll('script[src*="googletagmanager"]').length,0);s.dom.window.close();}
console.log('PASS: one initialization, existing-tag compatibility, iframe/offline exclusion, trusted events, one activity start, event labels, and no entered values.');
