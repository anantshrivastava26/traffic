with open('frontend.html', 'r', encoding='utf-8') as f:
    html = f.read()

three_and_css = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
.shiny-text {
  display: inline-block;
  background-image: linear-gradient(120deg, #94a3b8 0%, #94a3b8 35%, #ffffff 50%, #94a3b8 65%, #94a3b8 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shine 3s linear infinite;
}
.shiny-text-accent {
  display: inline-block;
  background-image: linear-gradient(120deg, #38bdf8 0%, #38bdf8 35%, #ffffff 50%, #38bdf8 65%, #38bdf8 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shine 2s linear infinite;
}
@keyframes shine {
  0%   { background-position: 150% center; }
  100% { background-position: -50% center; }
}
.light-pillar-wrap {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}
.light-pillar-wrap canvas {
  width: 100% !important;
  height: 100% !important;
  mix-blend-mode: screen;
  opacity: 0.6;
}
</style>
</head>"""

html = html.replace('</head>', three_and_css, 1)

html = html.replace(
    '<div class="header">',
    '<div class="header" style="position:relative;overflow:hidden"><div id="lightPillarHero" class="light-pillar-wrap"></div>',
    1
)

html = html.replace('>TrafficIQ<', '><span class="shiny-text-accent">TrafficIQ</span><', 1)
html = html.replace('>URBAN CONGESTION INTELLIGENCE<', '><span class="shiny-text">URBAN CONGESTION INTELLIGENCE</span><', 1)

light_pillar_js = """
<script>
(function() {
  var container = document.getElementById('lightPillarHero');
  if(!container || typeof THREE === 'undefined') return;
  var w = window.innerWidth;
  var h = 64;
  var renderer = new THREE.WebGLRenderer({antialias:false, alpha:true});
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);
  var scene  = new THREE.Scene();
  var camera = new THREE.OrthographicCamera(-1,1,1,-1,0,1);
  var vertexShader = "varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position,1.0);}";
  var fragmentShader = [
    "precision mediump float;",
    "uniform float uTime;",
    "uniform vec2 uResolution;",
    "uniform vec3 uTopColor;",
    "uniform vec3 uBottomColor;",
    "uniform float uGlowAmount;",
    "uniform float uPillarWidth;",
    "uniform float uPillarHeight;",
    "varying vec2 vUv;",
    "void main(){",
    "  vec2 uv=(vUv*2.0-1.0)*vec2(uResolution.x/uResolution.y,1.0);",
    "  vec3 ro=vec3(0.0,0.0,-10.0);",
    "  vec3 rd=normalize(vec3(uv,1.0));",
    "  vec3 col=vec3(0.0);",
    "  float t=0.1;",
    "  float rotC=cos(uTime*0.3);",
    "  float rotS=sin(uTime*0.3);",
    "  for(int i=0;i<40;i++){",
    "    vec3 p=ro+rd*t;",
    "    p.xz=vec2(rotC*p.x-rotS*p.z,rotS*p.x+rotC*p.z);",
    "    vec3 q=p;",
    "    q.y=p.y*uPillarHeight+uTime;",
    "    q+=cos(q.zxy*1.0-uTime)*1.0;",
    "    q+=cos(q.zxy*2.0-uTime*2.0)*0.5;",
    "    float d=length(cos(q.xz))-0.2;",
    "    float bound=length(p.xz)-uPillarWidth;",
    "    float k=4.0;",
    "    float h2=max(k-abs(d-bound),0.0);",
    "    d=max(d,bound)+h2*h2*0.0625/k;",
    "    d=abs(d)*0.15+0.01;",
    "    float grad=clamp((15.0-p.y)/30.0,0.0,1.0);",
    "    col+=mix(uBottomColor,uTopColor,grad)/d;",
    "    t+=d*1.2;",
    "    if(t>50.0)break;",
    "  }",
    "  col=tanh(col*uGlowAmount/(uPillarWidth/3.0));",
    "  gl_FragColor=vec4(col*1.2,1.0);",
    "}"
  ].join("\\n");
  function hexToVec3(hex){
    var c=new THREE.Color(hex);
    return new THREE.Vector3(c.r,c.g,c.b);
  }
  var material = new THREE.ShaderMaterial({
    vertexShader: vertexShader,
    fragmentShader: fragmentShader,
    uniforms:{
      uTime:         {value:0},
      uResolution:   {value:new THREE.Vector2(w,h)},
      uTopColor:     {value:hexToVec3('#5227FF')},
      uBottomColor:  {value:hexToVec3('#38bdf8')},
      uGlowAmount:   {value:0.003},
      uPillarWidth:  {value:3.0},
      uPillarHeight: {value:0.4}
    },
    transparent:true, depthWrite:false, depthTest:false
  });
  var mesh = new THREE.Mesh(new THREE.PlaneGeometry(2,2), material);
  scene.add(mesh);
  var clock=0;
  function animate(){
    requestAnimationFrame(animate);
    clock+=0.016*0.3;
    material.uniforms.uTime.value=clock;
    renderer.render(scene,camera);
  }
  animate();
  window.addEventListener('resize',function(){
    var nw=window.innerWidth;
    renderer.setSize(nw,64);
    material.uniforms.uResolution.value.set(nw,64);
  });
})();
</script>
</body>"""

html = html.replace('</body>', light_pillar_js, 1)

with open('frontend.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done!")
print("Shiny text + Light Pillar added!")