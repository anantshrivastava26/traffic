with open('frontend.html', 'r', encoding='utf-8') as f:
    html = f.read()

splash_js = """
<script>
(function() {
  var canvas = document.createElement('canvas');
  canvas.id = 'fluid';
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:999;';
  document.body.appendChild(canvas);

  var config = {
    SIM_RESOLUTION: 128,
    DYE_RESOLUTION: 1440,
    DENSITY_DISSIPATION: 3.5,
    VELOCITY_DISSIPATION: 2,
    PRESSURE: 0.1,
    PRESSURE_ITERATIONS: 20,
    CURL: 3,
    SPLAT_RADIUS: 0.2,
    SPLAT_FORCE: 6000,
    SHADING: true,
    COLOR_UPDATE_SPEED: 10,
    TRANSPARENT: true
  };

  var pointers = [];
  function PointerPrototype() {
    this.id = -1;
    this.texcoordX = 0;
    this.texcoordY = 0;
    this.prevTexcoordX = 0;
    this.prevTexcoordY = 0;
    this.deltaX = 0;
    this.deltaY = 0;
    this.down = false;
    this.moved = false;
    this.color = [0,0,0];
  }
  pointers.push(new PointerPrototype());

  var params = {alpha:true,depth:false,stencil:false,antialias:false,preserveDrawingBuffer:false};
  var gl = canvas.getContext('webgl2',params);
  var isWebGL2 = !!gl;
  if(!isWebGL2) gl = canvas.getContext('webgl',params)||canvas.getContext('experimental-webgl',params);

  var halfFloat, supportLinearFiltering;
  if(isWebGL2){
    gl.getExtension('EXT_color_buffer_float');
    supportLinearFiltering = gl.getExtension('OES_texture_float_linear');
  } else {
    halfFloat = gl.getExtension('OES_texture_half_float');
    supportLinearFiltering = gl.getExtension('OES_texture_half_float_linear');
  }
  gl.clearColor(0,0,0,1);
  var halfFloatTexType = isWebGL2 ? gl.HALF_FLOAT : (halfFloat && halfFloat.HALF_FLOAT_OES);

  function getSupportedFormat(gl,internalFormat,format,type){
    if(!supportRenderTextureFormat(gl,internalFormat,format,type)){
      if(internalFormat===gl.R16F) return getSupportedFormat(gl,gl.RG16F,gl.RG,type);
      if(internalFormat===gl.RG16F) return getSupportedFormat(gl,gl.RGBA16F,gl.RGBA,type);
      return null;
    }
    return {internalFormat,format};
  }

  function supportRenderTextureFormat(gl,internalFormat,format,type){
    var tex=gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D,tex);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D,0,internalFormat,4,4,0,format,type,null);
    var fbo=gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER,fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,tex,0);
    return gl.checkFramebufferStatus(gl.FRAMEBUFFER)===gl.FRAMEBUFFER_COMPLETE;
  }

  var formatRGBA,formatRG,formatR;
  if(isWebGL2){
    formatRGBA=getSupportedFormat(gl,gl.RGBA16F,gl.RGBA,halfFloatTexType);
    formatRG=getSupportedFormat(gl,gl.RG16F,gl.RG,halfFloatTexType);
    formatR=getSupportedFormat(gl,gl.R16F,gl.RED,halfFloatTexType);
  } else {
    formatRGBA=getSupportedFormat(gl,gl.RGBA,gl.RGBA,halfFloatTexType);
    formatRG=getSupportedFormat(gl,gl.RGBA,gl.RGBA,halfFloatTexType);
    formatR=getSupportedFormat(gl,gl.RGBA,gl.RGBA,halfFloatTexType);
  }

  function compileShader(type,source){
    var s=gl.createShader(type);
    gl.shaderSource(s,source);
    gl.compileShader(s);
    return s;
  }

  function createProgram(vs,fs){
    var p=gl.createProgram();
    gl.attachShader(p,vs);
    gl.attachShader(p,fs);
    gl.linkProgram(p);
    return p;
  }

  function getUniforms(program){
    var u={};
    var n=gl.getProgramParameter(program,gl.ACTIVE_UNIFORMS);
    for(var i=0;i<n;i++){
      var name=gl.getActiveUniform(program,i).name;
      u[name]=gl.getUniformLocation(program,name);
    }
    return u;
  }

  var baseVS = compileShader(gl.VERTEX_SHADER,
    'precision highp float;attribute vec2 aPosition;varying vec2 vUv;varying vec2 vL;varying vec2 vR;varying vec2 vT;varying vec2 vB;uniform vec2 texelSize;void main(){vUv=aPosition*0.5+0.5;vL=vUv-vec2(texelSize.x,0.0);vR=vUv+vec2(texelSize.x,0.0);vT=vUv+vec2(0.0,texelSize.y);vB=vUv-vec2(0.0,texelSize.y);gl_Position=vec4(aPosition,0.0,1.0);}');

  var copyFS   = compileShader(gl.FRAGMENT_SHADER,'precision mediump float;precision mediump sampler2D;varying highp vec2 vUv;uniform sampler2D uTexture;void main(){gl_FragColor=texture2D(uTexture,vUv);}');
  var clearFS  = compileShader(gl.FRAGMENT_SHADER,'precision mediump float;precision mediump sampler2D;varying highp vec2 vUv;uniform sampler2D uTexture;uniform float value;void main(){gl_FragColor=value*texture2D(uTexture,vUv);}');
  var splatFS  = compileShader(gl.FRAGMENT_SHADER,'precision highp float;precision highp sampler2D;varying vec2 vUv;uniform sampler2D uTarget;uniform float aspectRatio;uniform vec3 color;uniform vec2 point;uniform float radius;void main(){vec2 p=vUv-point.xy;p.x*=aspectRatio;vec3 splat=exp(-dot(p,p)/radius)*color;vec3 base=texture2D(uTarget,vUv).xyz;gl_FragColor=vec4(base+splat,1.0);}');
  var advFS    = compileShader(gl.FRAGMENT_SHADER,'precision highp float;precision highp sampler2D;varying vec2 vUv;uniform sampler2D uVelocity;uniform sampler2D uSource;uniform vec2 texelSize;uniform vec2 dyeTexelSize;uniform float dt;uniform float dissipation;void main(){vec2 coord=vUv-dt*texture2D(uVelocity,vUv).xy*texelSize;gl_FragColor=dissipation>0.0?texture2D(uSource,coord)/(1.0+dissipation*dt):texture2D(uSource,coord);}');
  var divFS    = compileShader(gl.FRAGMENT_SHADER,'precision mediump float;precision mediump sampler2D;varying highp vec2 vUv;varying highp vec2 vL;varying highp vec2 vR;varying highp vec2 vT;varying highp vec2 vB;uniform sampler2D uVelocity;void main(){float L=texture2D(uVelocity,vL).x;float R=texture2D(uVelocity,vR).x;float T=texture2D(uVelocity,vT).y;float B=texture2D(uVelocity,vB).y;vec2 C=texture2D(uVelocity,vUv).xy;if(vL.x<0.0){L=-C.x;}if(vR.x>1.0){R=-C.x;}if(vT.y>1.0){T=-C.y;}if(vB.y<0.0){B=-C.y;}gl_FragColor=vec4(0.5*(R-L+T-B),0.0,0.0,1.0);}');
  var curlFS   = compileShader(gl.FRAGMENT_SHADER,'precision mediump float;precision mediump sampler2D;varying highp vec2 vUv;varying highp vec2 vL;varying highp vec2 vR;varying highp vec2 vT;varying highp vec2 vB;uniform sampler2D uVelocity;void main(){float L=texture2D(uVelocity,vL).y;float R=texture2D(uVelocity,vR).y;float T=texture2D(uVelocity,vT).x;float B=texture2D(uVelocity,vB).x;gl_FragColor=vec4(0.5*(R-L-T+B),0.0,0.0,1.0);}');
  var vortFS   = compileShader(gl.FRAGMENT_SHADER,'precision highp float;precision highp sampler2D;varying vec2 vUv;varying vec2 vL;varying vec2 vR;varying vec2 vT;varying vec2 vB;uniform sampler2D uVelocity;uniform sampler2D uCurl;uniform float curl;uniform float dt;void main(){float L=texture2D(uCurl,vL).x;float R=texture2D(uCurl,vR).x;float T=texture2D(uCurl,vT).x;float B=texture2D(uCurl,vB).x;float C=texture2D(uCurl,vUv).x;vec2 force=0.5*vec2(abs(T)-abs(B),abs(R)-abs(L));force/=length(force)+0.0001;force*=curl*C;force.y*=-1.0;vec2 vel=texture2D(uVelocity,vUv).xy+force*dt;vel=min(max(vel,-1000.0),1000.0);gl_FragColor=vec4(vel,0.0,1.0);}');
  var pressFS  = compileShader(gl.FRAGMENT_SHADER,'precision mediump float;precision mediump sampler2D;varying highp vec2 vUv;varying highp vec2 vL;varying highp vec2 vR;varying highp vec2 vT;varying highp vec2 vB;uniform sampler2D uPressure;uniform sampler2D uDivergence;void main(){float L=texture2D(uPressure,vL).x;float R=texture2D(uPressure,vR).x;float T=texture2D(uPressure,vT).x;float B=texture2D(uPressure,vB).x;float div=texture2D(uDivergence,vUv).x;gl_FragColor=vec4((L+R+B+T-div)*0.25,0.0,0.0,1.0);}');
  var gradFS   = compileShader(gl.FRAGMENT_SHADER,'precision mediump float;precision mediump sampler2D;varying highp vec2 vUv;varying highp vec2 vL;varying highp vec2 vR;varying highp vec2 vT;varying highp vec2 vB;uniform sampler2D uPressure;uniform sampler2D uVelocity;void main(){float L=texture2D(uPressure,vL).x;float R=texture2D(uPressure,vR).x;float T=texture2D(uPressure,vT).x;float B=texture2D(uPressure,vB).x;vec2 vel=texture2D(uVelocity,vUv).xy-vec2(R-L,T-B);gl_FragColor=vec4(vel,0.0,1.0);}');
  var displayFS= compileShader(gl.FRAGMENT_SHADER,'precision highp float;precision highp sampler2D;varying vec2 vUv;uniform sampler2D uTexture;void main(){vec3 c=texture2D(uTexture,vUv).rgb;float a=max(c.r,max(c.g,c.b));gl_FragColor=vec4(c,a);}');

  var copyP  = createProgram(baseVS,copyFS);   var copyU  = getUniforms(copyP);
  var clearP = createProgram(baseVS,clearFS);  var clearU = getUniforms(clearP);
  var splatP = createProgram(baseVS,splatFS);  var splatU = getUniforms(splatP);
  var advP   = createProgram(baseVS,advFS);    var advU   = getUniforms(advP);
  var divP   = createProgram(baseVS,divFS);    var divU   = getUniforms(divP);
  var curlP  = createProgram(baseVS,curlFS);   var curlU  = getUniforms(curlP);
  var vortP  = createProgram(baseVS,vortFS);   var vortU  = getUniforms(vortP);
  var pressP = createProgram(baseVS,pressFS);  var pressU = getUniforms(pressP);
  var gradP  = createProgram(baseVS,gradFS);   var gradU  = getUniforms(gradP);
  var dispP  = createProgram(baseVS,displayFS);var dispU  = getUniforms(dispP);

  gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,-1,1,1,1,1,-1]),gl.STATIC_DRAW);
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,gl.createBuffer());
  gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array([0,1,2,0,2,3]),gl.STATIC_DRAW);
  gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
  gl.enableVertexAttribArray(0);

  function blit(target){
    if(!target){
      gl.viewport(0,0,gl.drawingBufferWidth,gl.drawingBufferHeight);
      gl.bindFramebuffer(gl.FRAMEBUFFER,null);
    } else {
      gl.viewport(0,0,target.width,target.height);
      gl.bindFramebuffer(gl.FRAMEBUFFER,target.fbo);
    }
    gl.drawElements(gl.TRIANGLES,6,gl.UNSIGNED_SHORT,0);
  }

  function createFBO(w,h,internalFormat,format,type,param){
    gl.activeTexture(gl.TEXTURE0);
    var tex=gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D,tex);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,param);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,param);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D,0,internalFormat,w,h,0,format,type,null);
    var fbo=gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER,fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,tex,0);
    gl.viewport(0,0,w,h);
    gl.clear(gl.COLOR_BUFFER_BIT);
    return {texture:tex,fbo:fbo,width:w,height:h,
      attach:function(id){gl.activeTexture(gl.TEXTURE0+id);gl.bindTexture(gl.TEXTURE_2D,tex);return id;}};
  }

  function createDoubleFBO(w,h,iF,f,t,p){
    var f1=createFBO(w,h,iF,f,t,p), f2=createFBO(w,h,iF,f,t,p);
    return {width:w,height:h,texelSizeX:1/w,texelSizeY:1/h,
      read:f1,write:f2,
      swap:function(){var tmp=this.read;this.read=this.write;this.write=tmp;}};
  }

  function getRes(r){
    var ar=gl.drawingBufferWidth/gl.drawingBufferHeight;
    if(ar<1)ar=1/ar;
    var min=Math.round(r),max=Math.round(r*ar);
    return gl.drawingBufferWidth>gl.drawingBufferHeight?{width:max,height:min}:{width:min,height:max};
  }

  function scale(n){return Math.floor(n*(window.devicePixelRatio||1));}

  function resize(){
    var w=scale(canvas.clientWidth),h=scale(canvas.clientHeight);
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;return true;}
    return false;
  }

  var simRes=getRes(128),dyeRes=getRes(1440);
  var filtering=supportLinearFiltering?gl.LINEAR:gl.NEAREST;
  var dye      =createDoubleFBO(dyeRes.width,dyeRes.height,formatRGBA.internalFormat,formatRGBA.format,halfFloatTexType,filtering);
  var velocity =createDoubleFBO(simRes.width,simRes.height,formatRG.internalFormat,formatRG.format,halfFloatTexType,filtering);
  var divergence=createFBO(simRes.width,simRes.height,formatR.internalFormat,formatR.format,halfFloatTexType,gl.NEAREST);
  var curlFBO  =createFBO(simRes.width,simRes.height,formatR.internalFormat,formatR.format,halfFloatTexType,gl.NEAREST);
  var pressure =createDoubleFBO(simRes.width,simRes.height,formatR.internalFormat,formatR.format,halfFloatTexType,gl.NEAREST);

  function HSVtoRGB(h,s,v){
    var r,g,b,i=Math.floor(h*6),f=h*6-i,p=v*(1-s),q=v*(1-f*s),t=v*(1-(1-f)*s);
    switch(i%6){case 0:r=v;g=t;b=p;break;case 1:r=q;g=v;b=p;break;case 2:r=p;g=v;b=t;break;case 3:r=p;g=q;b=v;break;case 4:r=t;g=p;b=v;break;case 5:r=v;g=p;b=q;break;}
    return {r:r,g:g,b:b};
  }

  function genColor(){var c=HSVtoRGB(Math.random(),1,1);return {r:c.r*0.15,g:c.g*0.15,b:c.b*0.15};}

  function splat(x,y,dx,dy,color){
    gl.useProgram(splatP);
    gl.uniform1i(splatU.uTarget,velocity.read.attach(0));
    gl.uniform1f(splatU.aspectRatio,canvas.width/canvas.height);
    gl.uniform2f(splatU.point,x,y);
    gl.uniform3f(splatU.color,dx,dy,0);
    gl.uniform1f(splatU.radius,config.SPLAT_RADIUS/100*(canvas.width>canvas.height?canvas.width/canvas.height:1));
    blit(velocity.write);velocity.swap();
    gl.uniform1i(splatU.uTarget,dye.read.attach(0));
    gl.uniform3f(splatU.color,color.r,color.g,color.b);
    blit(dye.write);dye.swap();
  }

  var lastTime=Date.now(),colorTimer=0;

  function frame(){
    var now=Date.now(),dt=Math.min((now-lastTime)/1000,0.016666);
    lastTime=now;
    if(resize()){
      simRes=getRes(128);dyeRes=getRes(1440);
    }
    colorTimer+=dt*10;
    if(colorTimer>=1){colorTimer=0;pointers.forEach(function(p){p.color=genColor();});}
    pointers.forEach(function(p){if(p.moved){p.moved=false;splat(p.texcoordX,p.texcoordY,p.deltaX*config.SPLAT_FORCE,p.deltaY*config.SPLAT_FORCE,p.color);}});

    gl.disable(gl.BLEND);
    gl.useProgram(curlP);gl.uniform2f(curlU.texelSize,velocity.texelSizeX,velocity.texelSizeY);gl.uniform1i(curlU.uVelocity,velocity.read.attach(0));blit(curlFBO);
    gl.useProgram(vortP);gl.uniform2f(vortU.texelSize,velocity.texelSizeX,velocity.texelSizeY);gl.uniform1i(vortU.uVelocity,velocity.read.attach(0));gl.uniform1i(vortU.uCurl,curlFBO.attach(1));gl.uniform1f(vortU.curl,config.CURL);gl.uniform1f(vortU.dt,dt);blit(velocity.write);velocity.swap();
    gl.useProgram(divP);gl.uniform2f(divU.texelSize,velocity.texelSizeX,velocity.texelSizeY);gl.uniform1i(divU.uVelocity,velocity.read.attach(0));blit(divergence);
    gl.useProgram(clearP);gl.uniform1i(clearU.uTexture,pressure.read.attach(0));gl.uniform1f(clearU.value,config.PRESSURE);blit(pressure.write);pressure.swap();
    gl.useProgram(pressP);gl.uniform2f(pressU.texelSize,velocity.texelSizeX,velocity.texelSizeY);gl.uniform1i(pressU.uDivergence,divergence.attach(0));
    for(var i=0;i<20;i++){gl.uniform1i(pressU.uPressure,pressure.read.attach(1));blit(pressure.write);pressure.swap();}
    gl.useProgram(gradP);gl.uniform2f(gradU.texelSize,velocity.texelSizeX,velocity.texelSizeY);gl.uniform1i(gradU.uPressure,pressure.read.attach(0));gl.uniform1i(gradU.uVelocity,velocity.read.attach(1));blit(velocity.write);velocity.swap();
    gl.useProgram(advP);gl.uniform2f(advU.texelSize,velocity.texelSizeX,velocity.texelSizeY);gl.uniform2f(advU.dyeTexelSize,velocity.texelSizeX,velocity.texelSizeY);var vid=velocity.read.attach(0);gl.uniform1i(advU.uVelocity,vid);gl.uniform1i(advU.uSource,vid);gl.uniform1f(advU.dt,dt);gl.uniform1f(advU.dissipation,config.VELOCITY_DISSIPATION);blit(velocity.write);velocity.swap();
    gl.uniform2f(advU.dyeTexelSize,dye.texelSizeX,dye.texelSizeY);gl.uniform1i(advU.uVelocity,velocity.read.attach(0));gl.uniform1i(advU.uSource,dye.read.attach(1));gl.uniform1f(advU.dissipation,config.DENSITY_DISSIPATION);blit(dye.write);dye.swap();

    gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);gl.enable(gl.BLEND);
    gl.useProgram(dispP);gl.uniform1i(dispU.uTexture,dye.read.attach(0));blit(null);

    requestAnimationFrame(frame);
  }

  function updatePointerDown(pointer,id,x,y){
    pointer.id=id;pointer.down=true;pointer.moved=false;
    pointer.texcoordX=x/canvas.width;pointer.texcoordY=1-y/canvas.height;
    pointer.prevTexcoordX=pointer.texcoordX;pointer.prevTexcoordY=pointer.texcoordY;
    pointer.deltaX=0;pointer.deltaY=0;pointer.color=genColor();
  }

  function updatePointerMove(pointer,x,y){
    pointer.prevTexcoordX=pointer.texcoordX;pointer.prevTexcoordY=pointer.texcoordY;
    pointer.texcoordX=x/canvas.width;pointer.texcoordY=1-y/canvas.height;
    var ar=canvas.width/canvas.height;
    pointer.deltaX=(pointer.texcoordX-pointer.prevTexcoordX)*(ar<1?ar:1);
    pointer.deltaY=(pointer.texcoordY-pointer.prevTexcoordY)*(ar>1?1/ar:1);
    pointer.moved=Math.abs(pointer.deltaX)>0||Math.abs(pointer.deltaY)>0;
  }

  window.addEventListener('mousedown',function(e){
    var p=pointers[0];
    updatePointerDown(p,-1,scale(e.clientX),scale(e.clientY));
    var c=genColor();c.r*=10;c.g*=10;c.b*=10;
    splat(p.texcoordX,p.texcoordY,10*(Math.random()-0.5),30*(Math.random()-0.5),c);
  });

  window.addEventListener('mousemove',function(e){
    var p=pointers[0];
    if(p.down) updatePointerMove(p,scale(e.clientX),scale(e.clientY));
    else {p.moved=true;updatePointerMove(p,scale(e.clientX),scale(e.clientY));}
  });

  window.addEventListener('touchstart',function(e){
    var t=e.targetTouches[0];
    updatePointerDown(pointers[0],t.identifier,scale(t.clientX),scale(t.clientY));
  },{passive:true});

  window.addEventListener('touchmove',function(e){
    var t=e.targetTouches[0];
    updatePointerMove(pointers[0],scale(t.clientX),scale(t.clientY));
  },{passive:false});

  frame();
})();
</script>
</body>"""

html = html.replace('</body>', splash_js, 1)

with open('frontend.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done! SplashCursor added!")