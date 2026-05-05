/* ═══════════════════════════════════════════════════
   HYPERSPEED — Vanilla JS port of @react-bits/Hyperspeed
   Uses Three.js (loaded via importmap or global)
   Preset: "one" (Cyberpunk / turbulentDistortion)
   ═══════════════════════════════════════════════════ */

const HYPER_PRESET = {
  distortion:'turbulentDistortion',length:400,roadWidth:10,islandWidth:2,
  lanesPerRoad:3,fov:90,fovSpeedUp:150,speedUp:2,carLightsFade:0.4,
  totalSideLightSticks:20,lightPairsPerRoadWay:40,
  shoulderLinesWidthPercentage:0.05,brokenLinesWidthPercentage:0.1,
  brokenLinesLengthPercentage:0.5,lightStickWidth:[0.12,0.5],
  lightStickHeight:[1.3,1.7],movingAwaySpeed:[60,80],
  movingCloserSpeed:[-120,-160],carLightsLength:[400*0.03,400*0.2],
  carLightsRadius:[0.05,0.14],carWidthPercentage:[0.3,0.5],
  carShiftX:[-0.8,0.8],carFloorSeparation:[0,5],
  colors:{roadColor:0x080808,islandColor:0x0a0a0a,background:0x000000,
    shoulderLines:0x131318,brokenLines:0x131318,
    leftCars:[0xd856bf,0x6750a2,0xc247ac],
    rightCars:[0x03b3c3,0x0e5ea5,0x324555],sticks:0x03b3c3}
};

function initHyperspeedLogin(container){
  if(!container||!window.THREE) return null;
  const T=THREE;
  const opts={...HYPER_PRESET};

  // Distortion uniforms & shaders
  const turbU={uFreq:{value:new T.Vector4(4,8,8,1)},uAmp:{value:new T.Vector4(25,5,10,10)}};
  const nsin=v=>Math.sin(v)*0.5+0.5;
  const distortion={
    uniforms:turbU,
    getDistortion:`
      uniform vec4 uFreq;uniform vec4 uAmp;
      float nsin(float val){return sin(val)*0.5+0.5;}
      #define PI 3.14159265358979
      float getDistortionX(float progress){
        return(cos(PI*progress*uFreq.r+uTime)*uAmp.r+pow(cos(PI*progress*uFreq.g+uTime*(uFreq.g/uFreq.r)),2.)*uAmp.g);
      }
      float getDistortionY(float progress){
        return(-nsin(PI*progress*uFreq.b+uTime)*uAmp.b+-pow(nsin(PI*progress*uFreq.a+uTime/(uFreq.b/uFreq.a)),5.)*uAmp.a);
      }
      vec3 getDistortion(float progress){
        return vec3(getDistortionX(progress)-getDistortionX(0.0125),getDistortionY(progress)-getDistortionY(0.0125),0.);
      }`,
    getJS:(progress,time)=>{
      const uF=turbU.uFreq.value,uA=turbU.uAmp.value;
      const gX=p=>Math.cos(Math.PI*p*uF.x+time)*uA.x+Math.pow(Math.cos(Math.PI*p*uF.y+time*(uF.y/uF.x)),2)*uA.y;
      const gY=p=>-nsin(Math.PI*p*uF.z+time)*uA.z-Math.pow(nsin(Math.PI*p*uF.w+time/(uF.z/uF.w)),5)*uA.w;
      let d=new T.Vector3(gX(progress)-gX(progress+0.007),gY(progress)-gY(progress+0.007),0);
      return d.multiply(new T.Vector3(-2,-5,0)).add(new T.Vector3(0,0,-10));
    }
  };
  opts.distortion=distortion;

  // Helpers
  const random=b=>Array.isArray(b)?Math.random()*(b[1]-b[0])+b[0]:Math.random()*b;
  const pickRandom=a=>Array.isArray(a)?a[Math.floor(Math.random()*a.length)]:a;
  function lerp(c,t,s=0.1,l=0.001){let ch=(t-c)*s;if(Math.abs(ch)<l)ch=t-c;return ch;}

  // Setup renderer
  const W=Math.max(1,container.offsetWidth),H=Math.max(1,container.offsetHeight);
  const renderer=new T.WebGLRenderer({antialias:false,alpha:true});
  renderer.setSize(W,H,false);renderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(renderer.domElement);

  const camera=new T.PerspectiveCamera(opts.fov,W/H,0.1,10000);
  camera.position.set(0,8,-5);
  const scene=new T.Scene();
  scene.background=new T.Color(opts.colors.background);
  const fog=new T.Fog(opts.colors.background,opts.length*0.2,opts.length*500);
  scene.fog=fog;
  const fogU={fogColor:{value:fog.color},fogNear:{value:fog.near},fogFar:{value:fog.far}};
  const clock=new T.Clock();

  // ── Car Lights ──
  const carLightsFragment=`
    #define USE_FOG;
    ${T.ShaderChunk['fog_pars_fragment']}
    varying vec3 vColor;varying vec2 vUv;uniform vec2 uFade;
    void main(){vec3 color=vec3(vColor);float alpha=smoothstep(uFade.x,uFade.y,vUv.x);
    gl_FragColor=vec4(color,alpha);if(gl_FragColor.a<0.0001)discard;${T.ShaderChunk['fog_fragment']}}`;

  const carLightsVertex=`
    #define USE_FOG;
    ${T.ShaderChunk['fog_pars_vertex']}
    attribute vec3 aOffset;attribute vec3 aMetrics;attribute vec3 aColor;
    uniform float uTravelLength;uniform float uTime;varying vec2 vUv;varying vec3 vColor;
    #include <getDistortion_vertex>
    void main(){vec3 transformed=position.xyz;float radius=aMetrics.r;float myLength=aMetrics.g;float speed=aMetrics.b;
    transformed.xy*=radius;transformed.z*=myLength;
    transformed.z+=myLength-mod(uTime*speed+aOffset.z,uTravelLength);transformed.xy+=aOffset.xy;
    float progress=abs(transformed.z/uTravelLength);transformed.xyz+=getDistortion(progress);
    vec4 mvPosition=modelViewMatrix*vec4(transformed,1.);gl_Position=projectionMatrix*mvPosition;
    vUv=uv;vColor=aColor;${T.ShaderChunk['fog_vertex']}}`;

  function createCarLights(colors,speed,fade){
    let curve=new T.LineCurve3(new T.Vector3(0,0,0),new T.Vector3(0,0,-1));
    let geo=new T.TubeGeometry(curve,40,1,8,false);
    let inst=new T.InstancedBufferGeometry().copy(geo);
    inst.instanceCount=opts.lightPairsPerRoadWay*2;
    let lW=opts.roadWidth/opts.lanesPerRoad;
    let aO=[],aM=[],aC=[];
    let cols=Array.isArray(colors)?colors.map(c=>new T.Color(c)):new T.Color(colors);
    for(let i=0;i<opts.lightPairsPerRoadWay;i++){
      let r=random(opts.carLightsRadius),l=random(opts.carLightsLength),s=random(speed);
      let lane=i%opts.lanesPerRoad,lX=lane*lW-opts.roadWidth/2+lW/2;
      let cW=random(opts.carWidthPercentage)*lW,cS=random(opts.carShiftX)*lW;lX+=cS;
      let oY=random(opts.carFloorSeparation)+r*1.3,oZ=-random(opts.length);
      aO.push(lX-cW/2,oY,oZ,lX+cW/2,oY,oZ);
      aM.push(r,l,s,r,l,s);
      let c=pickRandom(cols);aC.push(c.r,c.g,c.b,c.r,c.g,c.b);
    }
    inst.setAttribute('aOffset',new T.InstancedBufferAttribute(new Float32Array(aO),3,false));
    inst.setAttribute('aMetrics',new T.InstancedBufferAttribute(new Float32Array(aM),3,false));
    inst.setAttribute('aColor',new T.InstancedBufferAttribute(new Float32Array(aC),3,false));
    let mat=new T.ShaderMaterial({fragmentShader:carLightsFragment,vertexShader:carLightsVertex,transparent:true,
      uniforms:Object.assign({uTime:{value:0},uTravelLength:{value:opts.length},uFade:{value:fade}},fogU,distortion.uniforms)});
    mat.onBeforeCompile=sh=>{sh.vertexShader=sh.vertexShader.replace('#include <getDistortion_vertex>',distortion.getDistortion);};
    let mesh=new T.Mesh(inst,mat);mesh.frustumCulled=false;scene.add(mesh);
    return mesh;
  }

  const leftCars=createCarLights(opts.colors.leftCars,opts.movingAwaySpeed,new T.Vector2(0,1-opts.carLightsFade));
  leftCars.position.setX(-opts.roadWidth/2-opts.islandWidth/2);
  const rightCars=createCarLights(opts.colors.rightCars,opts.movingCloserSpeed,new T.Vector2(1,0+opts.carLightsFade));
  rightCars.position.setX(opts.roadWidth/2+opts.islandWidth/2);

  // ── Side Light Sticks ──
  const ssV=`#define USE_FOG;${T.ShaderChunk['fog_pars_vertex']}
    attribute float aOffset;attribute vec3 aColor;attribute vec2 aMetrics;
    uniform float uTravelLength;uniform float uTime;varying vec3 vColor;
    mat4 rotationY(in float angle){return mat4(cos(angle),0,sin(angle),0,0,1.0,0,0,-sin(angle),0,cos(angle),0,0,0,0,1);}
    #include <getDistortion_vertex>
    void main(){vec3 transformed=position.xyz;float width=aMetrics.x;float height=aMetrics.y;
    transformed.xy*=vec2(width,height);float time=mod(uTime*60.*2.+aOffset,uTravelLength);
    transformed=(rotationY(3.14/2.)*vec4(transformed,1.)).xyz;transformed.z+=-uTravelLength+time;
    float progress=abs(transformed.z/uTravelLength);transformed.xyz+=getDistortion(progress);
    transformed.y+=height/2.;transformed.x+=-width/2.;
    vec4 mvPosition=modelViewMatrix*vec4(transformed,1.);gl_Position=projectionMatrix*mvPosition;
    vColor=aColor;${T.ShaderChunk['fog_vertex']}}`;
  const ssF=`#define USE_FOG;${T.ShaderChunk['fog_pars_fragment']}varying vec3 vColor;
    void main(){gl_FragColor=vec4(vColor,1.);${T.ShaderChunk['fog_fragment']}}`;

  (function createSticks(){
    let geo=new T.PlaneGeometry(1,1);let inst=new T.InstancedBufferGeometry().copy(geo);
    let total=opts.totalSideLightSticks;inst.instanceCount=total;
    let sOff=opts.length/(total-1);let aO=[],aC=[],aM=[];
    let cols=Array.isArray(opts.colors.sticks)?opts.colors.sticks.map(c=>new T.Color(c)):new T.Color(opts.colors.sticks);
    for(let i=0;i<total;i++){
      aO.push((i-1)*sOff*2+sOff*Math.random());
      let c=pickRandom(cols);aC.push(c.r,c.g,c.b);
      aM.push(random(opts.lightStickWidth),random(opts.lightStickHeight));
    }
    inst.setAttribute('aOffset',new T.InstancedBufferAttribute(new Float32Array(aO),1,false));
    inst.setAttribute('aColor',new T.InstancedBufferAttribute(new Float32Array(aC),3,false));
    inst.setAttribute('aMetrics',new T.InstancedBufferAttribute(new Float32Array(aM),2,false));
    let mat=new T.ShaderMaterial({fragmentShader:ssF,vertexShader:ssV,side:T.DoubleSide,
      uniforms:Object.assign({uTravelLength:{value:opts.length},uTime:{value:0}},fogU,distortion.uniforms)});
    mat.onBeforeCompile=sh=>{sh.vertexShader=sh.vertexShader.replace('#include <getDistortion_vertex>',distortion.getDistortion);};
    let mesh=new T.Mesh(inst,mat);mesh.frustumCulled=false;
    mesh.position.setX(-(opts.roadWidth+opts.islandWidth/2));
    scene.add(mesh);window._sticksMesh=mesh;
  })();

  // ── Road ──
  const roadMarkingsVars=`uniform float uLanes;uniform vec3 uBrokenLinesColor;uniform vec3 uShoulderLinesColor;
    uniform float uShoulderLinesWidthPercentage;uniform float uBrokenLinesWidthPercentage;uniform float uBrokenLinesLengthPercentage;`;
  const roadMarkingsFrag=`uv.y=mod(uv.y+uTime*0.05,1.);float laneWidth=1.0/uLanes;
    float brokenLineWidth=laneWidth*uBrokenLinesWidthPercentage;float laneEmptySpace=1.-uBrokenLinesLengthPercentage;
    float brokenLines=step(1.0-brokenLineWidth,fract(uv.x*2.0))*step(laneEmptySpace,fract(uv.y*10.0));
    float sideLines=step(1.0-brokenLineWidth,fract((uv.x-laneWidth*(uLanes-1.0))*2.0))+step(brokenLineWidth,uv.x);
    brokenLines=mix(brokenLines,sideLines,uv.x);`;
  const roadBaseF=`#define USE_FOG;varying vec2 vUv;uniform vec3 uColor;uniform float uTime;
    #include <roadMarkings_vars>${T.ShaderChunk['fog_pars_fragment']}
    void main(){vec2 uv=vUv;vec3 color=vec3(uColor);#include <roadMarkings_fragment>
    gl_FragColor=vec4(color,1.);${T.ShaderChunk['fog_fragment']}}`;
  const islandF=roadBaseF.replace('#include <roadMarkings_fragment>','').replace('#include <roadMarkings_vars>','');
  const roadF=roadBaseF.replace('#include <roadMarkings_fragment>',roadMarkingsFrag).replace('#include <roadMarkings_vars>',roadMarkingsVars);
  const roadV=`#define USE_FOG;uniform float uTime;${T.ShaderChunk['fog_pars_vertex']}
    uniform float uTravelLength;varying vec2 vUv;#include <getDistortion_vertex>
    void main(){vec3 transformed=position.xyz;
    vec3 dist=getDistortion((transformed.y+uTravelLength/2.)/uTravelLength);
    transformed.x+=dist.x;transformed.z+=dist.y;transformed.y+=-1.*dist.z;
    vec4 mvPosition=modelViewMatrix*vec4(transformed,1.);gl_Position=projectionMatrix*mvPosition;
    vUv=uv;${T.ShaderChunk['fog_vertex']}}`;

  const roadTime={value:0};
  function createPlane(side,isRoad){
    let geo=new T.PlaneGeometry(isRoad?opts.roadWidth:opts.islandWidth,opts.length,20,100);
    let u={uTravelLength:{value:opts.length},uColor:{value:new T.Color(isRoad?opts.colors.roadColor:opts.colors.islandColor)},uTime:roadTime};
    if(isRoad)Object.assign(u,{uLanes:{value:opts.lanesPerRoad},uBrokenLinesColor:{value:new T.Color(opts.colors.brokenLines)},
      uShoulderLinesColor:{value:new T.Color(opts.colors.shoulderLines)},uShoulderLinesWidthPercentage:{value:opts.shoulderLinesWidthPercentage},
      uBrokenLinesLengthPercentage:{value:opts.brokenLinesLengthPercentage},uBrokenLinesWidthPercentage:{value:opts.brokenLinesWidthPercentage}});
    let mat=new T.ShaderMaterial({fragmentShader:isRoad?roadF:islandF,vertexShader:roadV,side:T.DoubleSide,
      uniforms:Object.assign(u,fogU,distortion.uniforms)});
    mat.onBeforeCompile=sh=>{sh.vertexShader=sh.vertexShader.replace('#include <getDistortion_vertex>',distortion.getDistortion);};
    let mesh=new T.Mesh(geo,mat);mesh.rotation.x=-Math.PI/2;mesh.position.z=-opts.length/2;
    mesh.position.x+=(opts.islandWidth/2+opts.roadWidth/2)*side;scene.add(mesh);return mesh;
  }
  createPlane(-1,true);createPlane(1,true);createPlane(0,false);

  // ── Animation ──
  let fovTarget=opts.fov,speedUpTarget=0,speedUp=0,timeOffset=0,disposed=false;

  const onDown=()=>{fovTarget=opts.fovSpeedUp;speedUpTarget=opts.speedUp;};
  const onUp=()=>{fovTarget=opts.fov;speedUpTarget=0;};
  container.addEventListener('mousedown',onDown);
  container.addEventListener('mouseup',onUp);
  container.addEventListener('mouseout',onUp);
  container.addEventListener('touchstart',onDown,{passive:true});
  container.addEventListener('touchend',onUp,{passive:true});
  container.addEventListener('contextmenu',e=>e.preventDefault());

  function onResize(){
    const w=container.offsetWidth,h=container.offsetHeight;
    if(w<=0||h<=0)return;
    renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();
  }
  window.addEventListener('resize',onResize);

  function tick(){
    if(disposed)return;
    const delta=clock.getDelta();
    let lp=Math.exp(-(-60*Math.log2(1-0.1))*delta);
    speedUp+=lerp(speedUp,speedUpTarget,lp,0.00001);
    timeOffset+=speedUp*delta;
    let time=clock.elapsedTime+timeOffset;

    leftCars.material.uniforms.uTime.value=time;
    rightCars.material.uniforms.uTime.value=time;
    if(window._sticksMesh)window._sticksMesh.material.uniforms.uTime.value=time;
    roadTime.value=time;

    let fovChange=lerp(camera.fov,fovTarget,lp);
    if(fovChange!==0){camera.fov+=fovChange*delta*6;camera.updateProjectionMatrix();}
    if(distortion.getJS){
      const d=distortion.getJS(0.025,time);
      camera.lookAt(new T.Vector3(camera.position.x+d.x,camera.position.y+d.y,camera.position.z+d.z));
    }
    renderer.render(scene,camera);
    requestAnimationFrame(tick);
  }
  tick();

  return {
    dispose(){
      disposed=true;
      window.removeEventListener('resize',onResize);
      container.removeEventListener('mousedown',onDown);
      container.removeEventListener('mouseup',onUp);
      container.removeEventListener('mouseout',onUp);
      renderer.dispose();renderer.forceContextLoss();
      if(renderer.domElement&&renderer.domElement.parentNode)renderer.domElement.parentNode.removeChild(renderer.domElement);
      scene.traverse(o=>{if(o.isMesh){if(o.geometry)o.geometry.dispose();if(o.material){if(Array.isArray(o.material))o.material.forEach(m=>m.dispose());else o.material.dispose();}}});
      scene.clear();
    }
  };
}
