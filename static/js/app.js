document.addEventListener("DOMContentLoaded", () => {
  const unlocked = sessionStorage.getItem("poketestUnlocked") === "yes";
  const gate = document.getElementById("gate-screen");
  const nav = document.querySelector(".topbar nav");
  if (window.location.pathname !== "/" && !unlocked) { window.location.replace("/"); return; }
  if (gate) {
    if (unlocked) { gate.classList.add("hidden"); document.getElementById("arena-screen").classList.remove("hidden"); }
    const qs = [
      {q:"Which pytest feature provides reusable setup?",a:["Fixture","Mock","Coverage"],c:0,w:"Fixtures provide reusable test data."},
      {q:"What replaces an external API in an isolated test?",a:["A mock","A browser","A CSS file"],c:0,w:"Mocks isolate tests from external services."},
      {q:"What does coverage measure?",a:["Number of bugs","Executed code","Code quality"],c:1,w:"Coverage tracks code execution, not correctness."}
    ];
    let i=0,score=0,choice=-1,checked=false;
    const q=document.getElementById("gate-question"),opts=document.getElementById("gate-options"),fb=document.getElementById("gate-feedback"),next=document.getElementById("gate-next");
    function render(){choice=-1;checked=false;next.disabled=true;next.textContent="Check answer";document.getElementById("gate-step").textContent="QUESTION 0"+(i+1)+" / 03";document.getElementById("gate-score").textContent="BADGES "+score+" / 3";document.getElementById("gate-progress-bar").style.width=(i/3*100)+"%";q.innerHTML="<h2>"+qs[i].q+"</h2>";opts.innerHTML="";qs[i].a.forEach((a,n)=>{const b=document.createElement("button");b.textContent=a;b.onclick=()=>{choice=n;[...opts.children].forEach(x=>x.classList.remove("selected"));b.classList.add("selected");next.disabled=false;};opts.appendChild(b);});fb.textContent="Choose one answer, trainer.";}
    next.onclick=()=>{if(!checked){checked=true;const ok=choice===qs[i].c;if(ok)score++;fb.textContent=(ok?"✦ Correct! ":"Not quite. ")+qs[i].w;fb.className="feedback "+(ok?"good":"bad");document.getElementById("gate-score").textContent="BADGES "+score+" / 3";next.textContent=i===2?"Unlock arena":"Next question";return;}if(i<2){i++;render();}else if(score===3){sessionStorage.setItem("poketestUnlocked","yes");gate.classList.add("hidden");document.getElementById("arena-screen").classList.remove("hidden");if(nav)nav.classList.remove("hidden");}else{i=0;score=0;render();}};
    render();
  }
  const input=document.getElementById("pokemon-input"),search=document.getElementById("search-button");
  if(input&&search){const status=document.getElementById("api-status"),result=document.getElementById("pokemon-result"),tests=document.getElementById("lookup-tests"),list=document.getElementById("lookup-test-list");
    const cases=["test_fetch_pokemon_success","test_fetch_pokemon_accepts_pokedex_number","test_fetch_pokemon_not_found","test_fetch_pokemon_network_error","test_fetch_pokemon_upstream_error","test_pokemon_endpoint_success"];
    const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
    async function find(){let name=input.value.trim().toLowerCase();if(!name){status.textContent="Enter a name or Pokédex number.";return;}if(/^#?\d+$/.test(name))name=String(parseInt(name.replace("#",""),10));status.textContent="⚡ Scanning Pokédex…";result.classList.add("hidden");tests.classList.add("hidden");search.disabled=true;try{const r=await fetch("/api/pokemon/"+encodeURIComponent(name)+"/");const d=await r.json();if(!r.ok||!d.ok)throw new Error(d.error||"Pokémon not found");const p=d.pokemon;result.innerHTML="<div class='pokemon-card'><div class='dex'>#"+String(p.id).padStart(3,"0")+"</div><img src='"+esc(p.image||"")+"' alt='"+esc(p.name)+"'></div><div><span class='eyebrow'>POKÉDEX ENTRY · CAUGHT</span><h2>"+esc(p.name)+"</h2><p>Height "+p.height/10+" m · Weight "+p.weight/10+" kg</p><p>Types: "+p.types.map(esc).join(", ")+"</p><p>Abilities: "+p.abilities.map(esc).join(", ")+"</p><div class='stats'>"+p.stats.map(s=>"<span>"+esc(s.name)+": <b>"+s.value+"</b></span>").join("")+"</div><h3>⚡ LIVE RESPONSE CHECKS</h3><p>PASS · Response received</p><p>PASS · Name and ID present</p><p>PASS · Types and stats returned</p></div>";result.classList.remove("hidden");list.innerHTML=cases.map(x=>"<p>✓ <code>"+x+"</code></p>").join("");tests.classList.remove("hidden");status.textContent="Pokémon #"+String(p.id).padStart(3,"0")+" found!";}catch(e){status.textContent=e.message;}finally{search.disabled=false;}}
    search.onclick=find;input.onkeydown=e=>{if(e.key==="Enter")find();};document.querySelectorAll("[data-pokemon]").forEach(b=>b.onclick=()=>{input.value="#"+String(b.dataset.pokemon).padStart(3,"0");find();});find();
  }
  const arcade=document.getElementById("arcade-options");
  if(arcade){const rounds=[{q:"Which pytest feature provides reusable setup?",a:["Mocks","Fixtures","Coverage"],c:"Fixtures"},{q:"What replaces a real API in an isolated test?",a:["Mock","Migration","Template"],c:"Mock"},{q:"What does pytest-cov report?",a:["Executed code coverage","Site visitors","Page speed"],c:"Executed code coverage"}];let i=0,score=0,done=false;const q=document.getElementById("arcade-question"),fb=document.getElementById("arcade-feedback"),next=document.getElementById("arcade-next");function draw(){done=false;next.disabled=true;q.textContent=rounds[i].q;arcade.innerHTML="";rounds[i].a.forEach(a=>{let b=document.createElement("button");b.textContent=a;b.onclick=()=>{if(done)return;done=true;if(a===rounds[i].c)score++;fb.textContent=a===rounds[i].c?"🏅 Correct!":"Correct answer: "+rounds[i].c;document.getElementById("arcade-score").textContent="BADGES "+score+" / 3";next.disabled=false;};arcade.appendChild(b);});}next.onclick=()=>{if(i<2){i++;draw();}else{fb.textContent="Challenge complete! You earned "+score+" / 3 badges.";next.disabled=true;}};draw();}
  const run=document.getElementById("run-tests-btn");
  if(run){
    let suite="all", pollTimer=null;
    const labels={all:"Complete test suite",unit:"Unit tests",api:"Django API tests",mocks:"Mock and external API tests"};
    const out=document.getElementById("pytest-output"),status=document.getElementById("runner-status");
    const metric=(key,value)=>{document.getElementById("metric-"+key).textContent=value;};
    document.querySelectorAll(".suite").forEach(b=>b.onclick=()=>{
      suite=b.dataset.suite;
      document.querySelectorAll(".suite").forEach(x=>x.classList.toggle("selected",x===b));
      document.getElementById("selected-suite-label").textContent=labels[suite];
    });
    const csrf=()=>document.querySelector("#csrf-form [name=csrfmiddlewaretoken]")?.value||"";
    async function poll(id,n=0){
      if(n>120){out.textContent="Still running after 10 minutes. Check GitHub Actions.";run.disabled=false;run.textContent="▶ RUN TESTS";return;}
      try{
        const r=await fetch("/api/run-tests/status/"+encodeURIComponent(id)+"/"),d=await r.json();
        status.textContent=d.status==="queued"?"● QUEUED":d.status==="in_progress"?"● TESTS RUNNING":d.status==="completed"?(d.passed_run?"● ALL CHECKS PASSED":"● RUN FINISHED · REVIEW OUTPUT"):"● CHECKING";
        document.getElementById("terminal-state").textContent=(d.status||"").toUpperCase();
        if(d.status==="completed"){
          out.textContent=d.output||("Run conclusion: "+d.conclusion+". "+(d.run_url||""));
          metric("passed",d.summary?.passed??"—");
          metric("failed",(d.summary?.failed||0)+(d.summary?.errors||0));
          metric("coverage",d.coverage==null?"N/A":d.coverage+"%");
          metric("duration",d.duration==null?"—":d.duration+"s");
          run.disabled=false;run.textContent="▶ RUN TESTS";return;
        }
        out.textContent="GitHub Actions is "+(d.status||"starting")+". Checking again in 5 seconds…";
        pollTimer=setTimeout(()=>poll(id,n+1),5000);
      }catch(e){out.textContent="Could not retrieve test status: "+e.message;run.disabled=false;run.textContent="▶ RUN TESTS";}
    }
    run.onclick=async()=>{
      if(pollTimer)clearTimeout(pollTimer);
      run.disabled=true;run.textContent="DISPATCHING…";
      status.textContent="● SENDING TO GITHUB ACTIONS";out.textContent="Requesting a remote pytest run…";
      ["passed","failed","coverage","duration"].forEach(k=>metric(k,"…"));
      try{
        const access=document.getElementById("runner-access-code").value;
        const r=await fetch("/api/run-tests/",{method:"POST",headers:{"Content-Type":"application/json","X-CSRFToken":csrf()},body:JSON.stringify({suite:suite,access_code:access})});
        const d=await r.json();
        if(!r.ok||!d.ok)throw new Error(d.error||"Could not start test run.");
        if(d.remote){status.textContent="● QUEUED ON GITHUB ACTIONS";poll(d.request_id);return;}
        out.textContent=d.output||"No output";
        metric("passed",d.summary?.passed??"—");
        metric("failed",(d.summary?.failed||0)+(d.summary?.errors||0));
        metric("coverage",d.coverage==null?"N/A":d.coverage+"%");
        metric("duration",d.duration==null?"—":d.duration+"s");
        status.textContent=d.ok?"● ALL CHECKS PASSED":"● RUN FINISHED · REVIEW OUTPUT";
        document.getElementById("terminal-state").textContent="EXIT CODE "+(d.exit_code??r.status);
        run.disabled=false;run.textContent="▶ RUN TESTS";
      }catch(e){
        status.textContent="● RUN FAILED";out.textContent=e.message;
        document.getElementById("terminal-state").textContent="ERROR";
        run.disabled=false;run.textContent="▶ RUN TESTS";
      }
    };
  }
});
