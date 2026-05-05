/* ═══════════════════════════════════════════
   AMIS Advanced 3D Avatar + Music + Voice
   ═══════════════════════════════════════════ */

// ── MOOD SONGS DATABASE (royalty-free preview URLs) ──
const MOOD_SONGS = {
  happy: [
    {title:"Walking on Sunshine",artist:"Happy Vibes",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"},
    {title:"Feel Good Inc",artist:"Mood Boost",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"},
    {title:"Happy Together",artist:"Joy FM",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"}
  ],
  sad: [
    {title:"Rainy Days",artist:"Melancholy",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"},
    {title:"Blue Horizon",artist:"Soft Piano",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3"},
    {title:"Gentle Tears",artist:"Healing Waves",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3"}
  ],
  stressed: [
    {title:"Ocean Calm",artist:"Nature Sounds",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3"},
    {title:"Deep Breath",artist:"Meditation",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3"},
    {title:"Peaceful Mind",artist:"Zen Garden",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3"}
  ],
  angry: [
    {title:"Thunder Road",artist:"Power Rock",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3"},
    {title:"Release",artist:"Heavy Beat",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3"},
    {title:"Storm Pass",artist:"Catharsis",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3"}
  ],
  romantic: [
    {title:"Moonlight Serenade",artist:"Love Songs",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3"},
    {title:"Heart Strings",artist:"Romance",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3"},
    {title:"Sweet Dreams",artist:"Lullaby",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-15.mp3"}
  ],
  energetic: [
    {title:"Power Up",artist:"EDM Beats",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-16.mp3"},
    {title:"Adrenaline",artist:"Workout Mix",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"},
    {title:"Unstoppable",artist:"Pump It",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"}
  ],
  chill: [
    {title:"Lofi Dreams",artist:"Chill Hop",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"},
    {title:"Floating",artist:"Ambient",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"},
    {title:"Sunset Drive",artist:"Smooth Jazz",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3"}
  ],
  nostalgic: [
    {title:"Memory Lane",artist:"Classics",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3"},
    {title:"Golden Days",artist:"Retro",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3"},
    {title:"Time Machine",artist:"Throwback",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3"}
  ],
  confident: [
    {title:"Boss Mode",artist:"Victory",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3"},
    {title:"Crown",artist:"Royal Beat",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3"},
    {title:"Unstoppable",artist:"Power",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3"}
  ],
  bored: [
    {title:"Discovery",artist:"New Vibes",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3"},
    {title:"Adventure",artist:"Explorer",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3"},
    {title:"Surprise",artist:"Random Mix",url:"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3"}
  ]
};

// ── MOOD COLORS for 3D ──
const MOOD_3D_COLORS = {
  happy:{r:1,g:0.85,b:0.24},sad:{r:0.42,g:0.48,b:0.88},
  stressed:{r:0.42,g:0.8,b:0.47},angry:{r:1,g:0.42,b:0.42},
  romantic:{r:0.91,g:0.26,b:0.58},energetic:{r:0.99,g:0.47,b:0.66},
  chill:{r:0,g:0.81,b:0.79},nostalgic:{r:0.99,g:0.8,b:0.43},
  confident:{r:0.95,g:0.61,b:0.07},bored:{r:0.64,g:0.55,b:0.82}
};

const MOOD_EXPRESSIONS = {
  happy:"😄✨",sad:"😔💙",stressed:"😮‍💨🍃",angry:"😤🔥",
  romantic:"🥰💕",energetic:"⚡💪",chill:"😌🌊",
  nostalgic:"🥺🕰️",confident:"😎👑",bored:"😑🎯"
};

// ── Global state ──
let scene,camera,renderer,avatarMesh,particles;
let currentAudio=null,currentSongIdx=0,currentMoodSongs=[];
let isSpeakingNow=false;

// ═══ THREE.JS 3D AVATAR ═══
function init3DAvatar(){
  const container=document.getElementById('avatar3d-container');
  if(!container||typeof THREE==='undefined')return;

  scene=new THREE.Scene();
  camera=new THREE.PerspectiveCamera(50,1,0.1,100);
  camera.position.z=3;

  renderer=new THREE.WebGLRenderer({alpha:true,antialias:true});
  renderer.setSize(120,120);
  renderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(renderer.domElement);

  // Ambient light
  scene.add(new THREE.AmbientLight(0x9333ea,0.6));
  const point=new THREE.PointLight(0x00d4ff,1.5,10);
  point.position.set(2,2,3);scene.add(point);

  // Main sphere (head)
  const geo=new THREE.SphereGeometry(0.8,64,64);
  const mat=new THREE.MeshPhongMaterial({
    color:0x9333ea,emissive:0x4a1a8a,shininess:100,
    transparent:true,opacity:0.9
  });
  avatarMesh=new THREE.Mesh(geo,mat);scene.add(avatarMesh);

  // Eyes
  const eyeGeo=new THREE.SphereGeometry(0.1,16,16);
  const eyeMat=new THREE.MeshPhongMaterial({color:0xffffff,emissive:0x00d4ff});
  const leftEye=new THREE.Mesh(eyeGeo,eyeMat);
  leftEye.position.set(-0.25,0.15,0.72);avatarMesh.add(leftEye);
  const rightEye=new THREE.Mesh(eyeGeo,eyeMat);
  rightEye.position.set(0.25,0.15,0.72);avatarMesh.add(rightEye);

  // Pupils
  const pupilGeo=new THREE.SphereGeometry(0.05,12,12);
  const pupilMat=new THREE.MeshPhongMaterial({color:0x000000});
  const lp=new THREE.Mesh(pupilGeo,pupilMat);lp.position.set(0,0,0.06);leftEye.add(lp);
  const rp=new THREE.Mesh(pupilGeo,pupilMat);rp.position.set(0,0,0.06);rightEye.add(rp);

  // Mouth
  const mouthShape=new THREE.Shape();
  mouthShape.absarc(0,0,0.15,0,Math.PI,false);
  const mouthGeo=new THREE.ShapeGeometry(mouthShape);
  const mouthMat=new THREE.MeshBasicMaterial({color:0xff6b9d,side:THREE.DoubleSide});
  const mouth=new THREE.Mesh(mouthGeo,mouthMat);
  mouth.position.set(0,-0.2,0.78);mouth.name='mouth';
  avatarMesh.add(mouth);

  // Particle ring
  const pCount=200;
  const pGeo=new THREE.BufferGeometry();
  const positions=new Float32Array(pCount*3);
  for(let i=0;i<pCount;i++){
    const angle=Math.random()*Math.PI*2;
    const radius=1.2+Math.random()*0.5;
    positions[i*3]=Math.cos(angle)*radius;
    positions[i*3+1]=(Math.random()-0.5)*1.5;
    positions[i*3+2]=Math.sin(angle)*radius;
  }
  pGeo.setAttribute('position',new THREE.BufferAttribute(positions,3));
  const pMat=new THREE.PointsMaterial({color:0x00d4ff,size:0.03,transparent:true,opacity:0.7});
  particles=new THREE.Points(pGeo,pMat);
  scene.add(particles);

  animate3D();
}

function animate3D(){
  requestAnimationFrame(animate3D);
  if(!avatarMesh)return;
  const t=Date.now()*0.001;

  // Gentle idle animation
  avatarMesh.rotation.y=Math.sin(t*0.5)*0.15;
  avatarMesh.rotation.x=Math.sin(t*0.3)*0.05;
  avatarMesh.position.y=Math.sin(t*0.8)*0.05;

  // Speaking animation - mouth scale
  if(isSpeakingNow){
    const mouth=avatarMesh.getObjectByName('mouth');
    if(mouth) mouth.scale.y=1+Math.sin(t*12)*0.5;
  }

  // Particle rotation
  if(particles) particles.rotation.y+=0.003;

  renderer.render(scene,camera);
}

function setAvatarMood(mood){
  if(!avatarMesh)return;
  const c=MOOD_3D_COLORS[mood]||{r:0.58,g:0.2,b:0.92};
  const color=new THREE.Color(c.r,c.g,c.b);
  avatarMesh.material.color.copy(color);
  avatarMesh.material.emissive.copy(color).multiplyScalar(0.4);
  if(particles) particles.material.color.copy(color);

  // Container glow
  const cont=document.getElementById('avatar3d-container');
  if(cont){
    const hex=color.getHexString();
    cont.style.borderColor=`#${hex}88`;
    cont.style.boxShadow=`0 0 30px #${hex}55,0 0 60px #${hex}22`;
  }
}

// ═══ IN-CHAT MUSIC PLAYER ═══
function createMusicPlayer(mood){
  const songs=MOOD_SONGS[mood]||MOOD_SONGS.happy;
  currentMoodSongs=songs;
  currentSongIdx=Math.floor(Math.random()*songs.length);
  const song=songs[currentSongIdx];

  const card=document.createElement('div');
  card.className='music-player-card';
  card.innerHTML=`
    <button class="mp-play-btn" onclick="togglePlay(this)" title="Play">▶</button>
    <div class="mp-info">
      <div class="mp-title">${song.title}</div>
      <div class="mp-artist">${song.artist} • ${mood} vibes</div>
      <div class="mp-progress"><div class="mp-progress-bar"></div></div>
    </div>
    <div class="mp-controls">
      <div class="equalizer paused"><span></span><span></span><span></span><span></span><span></span></div>
      <button class="mp-skip-btn" onclick="skipSong(this)" title="Next">⏭</button>
    </div>
    <span class="mp-time">0:00</span>
  `;
  card.dataset.url=song.url;
  card.dataset.mood=mood;
  return card;
}

function togglePlay(btn){
  const card=btn.closest('.music-player-card');
  const url=card.dataset.url;
  const eq=card.querySelector('.equalizer');
  const bar=card.querySelector('.mp-progress-bar');
  const timeEl=card.querySelector('.mp-time');

  if(currentAudio&&!currentAudio.paused){
    currentAudio.pause();
    btn.textContent='▶';
    eq.classList.add('paused');
    return;
  }

  // Stop any existing audio
  if(currentAudio){currentAudio.pause();currentAudio=null;}
  // Reset all other players
  document.querySelectorAll('.mp-play-btn').forEach(b=>{b.textContent='▶';});
  document.querySelectorAll('.equalizer').forEach(e=>e.classList.add('paused'));

  currentAudio=new Audio(url);
  currentAudio.volume=0.6;
  currentAudio.play().catch(e=>console.log('Audio play error:',e));
  btn.textContent='⏸';
  eq.classList.remove('paused');

  currentAudio.ontimeupdate=()=>{
    if(!currentAudio)return;
    const pct=(currentAudio.currentTime/currentAudio.duration)*100;
    bar.style.width=pct+'%';
    const m=Math.floor(currentAudio.currentTime/60);
    const s=Math.floor(currentAudio.currentTime%60);
    timeEl.textContent=m+':'+(s<10?'0':'')+s;
  };
  currentAudio.onended=()=>{btn.textContent='▶';eq.classList.add('paused');};
}

function skipSong(btn){
  const card=btn.closest('.music-player-card');
  const mood=card.dataset.mood;
  const songs=MOOD_SONGS[mood]||MOOD_SONGS.happy;
  currentSongIdx=(currentSongIdx+1)%songs.length;
  const song=songs[currentSongIdx];

  card.dataset.url=song.url;
  card.querySelector('.mp-title').textContent=song.title;
  card.querySelector('.mp-artist').textContent=song.artist+' • '+mood+' vibes';
  card.querySelector('.mp-progress-bar').style.width='0%';
  card.querySelector('.mp-time').textContent='0:00';

  if(currentAudio){currentAudio.pause();currentAudio=null;}
  const playBtn=card.querySelector('.mp-play-btn');
  playBtn.textContent='▶';
  card.querySelector('.equalizer').classList.add('paused');

  // Auto-play new song
  togglePlay(playBtn);
}

// ═══ ENHANCED HUMAN-LIKE TTS ═══
function speakHuman(text,mood,onDone){
  if(!ttsEnabled||!text||typeof speechSynthesis==='undefined')return;

  // Clean text
  let clean=text.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE00}-\u{FEFF}]/gu,' ')
    .replace(/[—–]/g,', ').replace(/[:;]/g,'.').replace(/\s+/g,' ').trim();

  speechSynthesis.cancel();
  const utter=new SpeechSynthesisUtterance(clean);

  // Mood-based voice tuning for human feel
  const moodVoice={
    happy:{pitch:1.15,rate:0.95},sad:{pitch:0.85,rate:0.8},
    stressed:{pitch:1.0,rate:0.85},angry:{pitch:1.2,rate:1.0},
    romantic:{pitch:1.05,rate:0.82},energetic:{pitch:1.2,rate:1.05},
    chill:{pitch:0.95,rate:0.78},nostalgic:{pitch:0.9,rate:0.82},
    confident:{pitch:1.1,rate:0.92},bored:{pitch:0.9,rate:0.85}
  };
  const tune=moodVoice[mood]||{pitch:1.0,rate:0.9};

  if(selectedVoice)utter.voice=selectedVoice;
  utter.pitch=tune.pitch;
  utter.rate=tune.rate;
  utter.volume=0.95;
  utter.lang=(typeof VOICE_CODES!=='undefined'?VOICE_CODES[currentLang]:null)||'en-US';

  // Visual feedback
  isSpeakingNow=true;
  const cont=document.getElementById('avatar3d-container');
  const wave=document.getElementById('voiceWave');
  if(cont)cont.classList.add('speaking');
  if(wave)wave.classList.remove('hidden');

  utter.onend=()=>{
    isSpeakingNow=false;
    if(cont)cont.classList.remove('speaking');
    if(wave)wave.classList.add('hidden');
    if(onDone)onDone();
  };
  utter.onerror=()=>{
    isSpeakingNow=false;
    if(cont)cont.classList.remove('speaking');
    if(wave)wave.classList.add('hidden');
  };

  speechSynthesis.speak(utter);
}

// ═══ FLOATING EMOJI EFFECT ═══
function spawnFloatingEmojis(mood,targetEl){
  const emojis=(MOOD_EXPRESSIONS[mood]||"✨").split('');
  emojis.forEach((em,i)=>{
    setTimeout(()=>{
      const span=document.createElement('span');
      span.className='emoji-float';
      span.textContent=em;
      span.style.left=(Math.random()*60+20)+'%';
      span.style.top='0';
      if(targetEl)targetEl.appendChild(span);
      setTimeout(()=>span.remove(),2000);
    },i*300);
  });
}

// ═══ EXPRESSION ROW ═══
function createExpressionRow(mood){
  const row=document.createElement('div');
  row.className='expression-row';
  const emoji=document.createElement('span');
  emoji.className='expression-emoji';
  emoji.textContent=MOOD_EXPRESSIONS[mood]||'🎵';
  const label=document.createElement('span');
  label.className='expression-label';
  const feelings={
    happy:'feeling joyful',sad:'feeling emotional',stressed:'taking a breath',
    angry:'channeling energy',romantic:'in love mode',energetic:'pumped up',
    chill:'in zen mode',nostalgic:'remembering',confident:'boss mode on',bored:'exploring'
  };
  label.textContent=`AMIS is ${feelings[mood]||'vibing'}...`;
  row.appendChild(emoji);row.appendChild(label);
  return row;
}

// ═══ INIT ON LOAD ═══
document.addEventListener('DOMContentLoaded',()=>{
  // Load Three.js dynamically
  const script=document.createElement('script');
  script.src='https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
  script.onload=()=>init3DAvatar();
  document.head.appendChild(script);
});
