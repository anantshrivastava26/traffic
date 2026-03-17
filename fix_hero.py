with open('frontend.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add Three.js + Light Pillar CSS
inject_head = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
#lightPillarBg {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 0;
}
#lightPillarBg canvas {
  width: 100% !important;
  height: 100% !important;
  mix-blend-mode: screen;
  opacity: 0.55;
}
.shiny-text-accent {
  display: inline-block;
  background-image: linear-gradient(120deg, #38bdf8 0%, #38bdf8 30%, #ffffff 50%, #38bdf8 70%, #38bdf8 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shine 2s linear infinite;
}
.shiny-text {
  display: inline-block;
  background-image: linear-gradient(120deg, #94a3b8 0%, #94a3b8 30%, #ffffff 50%, #94a3b8 70%, #94a3b8 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shine 3s linear infinite;
}
@keyframes shine {
  0%   { background-position: 150% center; }
  100% { background-position: -50% center; }
}
</style>
</head>"""

html = html.replace('</head>', inject_head, 1)

# Add light pillar div right after <body>
html = html.replace('<body>', '<body><div id="lightPillarBg"></div>', 1)

# Add Light Pillar JS before </body>
light_js = """
<script>
(function() {
  var container = document.getElementById('lightPillarBg');
  if(!container || typeof THREE === 'undefined') return;

  var w = window.innerWidth;
  var h = window.innerHeight;

  var renderer = new THREE.WebGLRenderer({antialias:false, alpha:true});
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  container.appendChild(renderer.domElement);

  var scene  = new THREE.Scene();
  var camera = new THREE.OrthographicCamera(-1,1,1,-1,0,1);

  var vert = "varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position,1.0);}";

  var frag = [
    "precision highp float;",
    "uniform float uTime;",
    "uniform vec2 uResolution;",
    "uniform vec3 uTopColor;",
    "uniform vec3 uBottomColor;",
    "uniform float uGlowAmount;",
    "uniform float uPillarWidth;",
    "uniform float uPillarHeight;",
    "uniform float uNoiseIntensity;",
    "uniform float uIntensity;",
    "varying vec2 vUv;",
    "void main(){",
    "  vec2 uv=(vUv*2.0-1.0)*vec2(uResolution.x/uResolution.y,1.0);",
    "  float pRotC=cos(0.436);float pRotS=sin(0.436);",
    "  uv=vec2(pRotC*uv.x-pRotS*uv.y,pRotS*uv.x+pRotC*uv.y);",
    "  vec3 ro=vec3(0.0,0.0,-10.0);",
    "  vec3 rd=normalize(vec3(uv,1.0));",
    "  vec3 col=vec3(0.0);",
    "  float t=0.1;",
    "  float rotC=cos(uTime*0.3);",
    "  float rotS=sin(uTime*0.3);",
    "  float wC=cos(0.4);float wS=sin(0.4);",
    "  for(int i=0;i<80;i++){",
    "    vec3 p=ro+rd*t;",
    "    p.xz=vec2(rotC*p.x-rotS*p.z,rotS*p.x+rotC*p.z);",
    "    vec3 q=p;",
    "    q.y=p.y*uPillarHeight+uTime;",
    "    float freq=1.0;float amp=1.0;",
    "    for(int j=0;j<4;j++){",
    "      q.xz=vec2(wC*q.x-wS*q.z,wS*q.x+wC*q.z);",
    "      q+=cos(q.zxy*freq-uTime*float(j)*2.0)*amp;",
    "      freq*=2.0;amp*=0.5;",
    "    }",
    "    float d=length(cos(q.xz))-0.2;",
    "    float bound=length(p.xz)-uPillarWidth;",
    "    float k=4.0;",
    "    float h2=max(k-abs(d-bound),0.0);",
    "    d=max(d,bound)+h2*h2*0.0625/k;",
    "    d=abs(d)*0.15+0.01;",
    "    float grad=clamp((15.0-p.y)/30.0,0.0,1.0);",
    "    col+=mix(uBottomColor,uTopColor,grad)/d;",
    "    t+=d;",
    "    if(t>50.0)break;",
    "  }",
    "  col=tanh(col*uGlowAmount/(uPillarWidth/3.0));",
    "  col-=fract(sin(dot(gl_FragCoord.xy,vec2(12.9898,78.233)))*43758.5453)/15.0*uNoiseIntensity;",
    "  gl_FragColor=vec4(col*uIntensity,1.0);",
    "}"
  ].join("\\n");

  function hex3(hex){
    var c=new THREE.Color(hex);
    return new THREE.Vector3(c.r,c.g,c.b);
  }

  var mat = new THREE.ShaderMaterial({
    vertexShader:vert, fragmentShader:frag,
    uniforms:{
      uTime:        {value:0},
      uResolution:  {value:new THREE.Vector2(w,h)},
      uTopColor:    {value:hex3('#5227FF')},
      uBottomColor: {value:hex3('#FF9FFC')},
      uGlowAmount:  {value:0.002},
      uPillarWidth: {value:3.0},
      uPillarHeight:{value:0.4},
      uNoiseIntensity:{value:0.5},
      uIntensity:   {value:1.4}
    },
    transparent:true, depthWrite:false, depthTest:false
  });

  scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2), mat));

  var clk=0;
  function animate(){
    requestAnimationFrame(animate);
    clk+=0.016*0.6;
    mat.uniforms.uTime.value=clk;
    renderer.render(scene,camera);
  }
  animate();

  window.addEventListener('resize',function(){
    var nw=window.innerWidth, nh=window.innerHeight;
    renderer.setSize(nw,nh);
    mat.uniforms.uResolution.value.set(nw,nh);
  });
})();
</script>
</body>"""

html = html.replace('</body>', light_js, 1)

# Shiny text on TrafficIQ title
html = html.replace('>TrafficIQ<', '><span class="shiny-text-accent">TrafficIQ</span><', 1)

with open('frontend.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done! Purple Light Pillar background added!")