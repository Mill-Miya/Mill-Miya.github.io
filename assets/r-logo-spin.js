/* R mark: transient, CAD-contour 3D spin. WebGL2; no external dependencies. */
(() => {
  "use strict";
  const encoded = [
    "9AAKATB78QGReWcDyHdAePYCPXkqAtZ6NAH2e7gAtn06AOh+DQC2gAUAgYJFAKyDmADPhAoB54WcAfKGTQI3iGcDG8ZLQYmajDIu",
    "llUx+JPoMIKPazAHi2owy4iYMFuEUTEqgtwx631JM+V7JzQLeCw2dnSPOCxxSTsxblI+i2ujQT9pNEVSZ/9IymX8TKtkJFH7Y29V",
    "zmOgV79j2Fn7Y0Beq2SLYspls2aBZrhoPGidbFlqTHDTbL5zpG/rdsdyzXk4dl18C3iDfeV7iH8AgCmBYoM+gb6GfIEQiuOBWI1y",
    "gpSQKIPEkwSE5pYGhfmZLIb8nHeH7Z/kiMyidYqXpSeMTKj5jeyq7I90rf+R5K8wlDmyfpZ0tOqYkrZym5O4Fp51utSgN7yto9i9",
    "n6ZXv6mpu7xhrey56bDutkG0wbNmt2qwV7rqrBO9RamYv3yl5cGTofnDjJ3RxWqZbccvlcvI3ZDqyXmMyMoDiGPLuISqy2eBzMvf",
    "hETKJYhvyDSLUsYJjvLDn5BUwdKR778FlP2875XauY+XirbfmBOz3Zl6r4Waw6vRmvinwpozpFiafaCXmdycgphWmRyX75Vnla+S",
    "Z5OZjx6RtIyQjgWKv4uSh66IYIUOh2GEDoTWgu+CYYLUgLmByn0ygSV2iIACcbl/aW3tfvFp+n2bZuF8aWOle11gR3p4Xch4u1or",
    "dyhYcXX8VcxzJlQ/cm9So3BdTz9tBE55awNMVWh6SkBl2EmsY91IdWCESNNeIEiuWxVI91hPSDtW0Eh7U3lJHlHDSrBN00tMS0ZO",
    "rUYmUUxC603jRNtKn0f3R35KPkV+TbJCnVBUQNpTIz4yVyA8o1pNOiteqTjIYTU3eGXyNTpp4TQLbQI06XBVM9J03DLFeJcyv3yG",
    "Mr6AqjLAhAQzxIiVM8eMXDTHkFs1wpSTNreY/zeanJ05YKBpOwikYz2Sp4k/+6rYQUKuUERnse9GZ7SzSUO3mkz4uaJPhrzLUuq+",
    "EVYlwXRZNMPyXBfFiWDNxjhkU8j8Z6nJ1GvOyr9vwcu6c3/MxXcJzdx7Xc0AgHnNMoRczVyIBc15jHbMiZCwy4mUs8p4mILJU5wc",
    "yBigg8bGo7fEWqe7wtOqj8AurjS+abGsu4O09rh5txW2SboJs/K8068jwHSrbMGqrovC77GAw0C1S8ScuOvEAbxgxW+/v4cJ/cKG",
    "1f0phcv+CYRH/0mCxf8XgfL/SX/6/359uv9TfGf/MHv1/hh6Y/4NebL9yHeY/PYCv4cqAsKGNAEphYYAdYMfALCBAADjfygAFn6Y",
    "AFN8UABg30ZdnODuXZnh5F5L4hhgmOIyYSnj6GhY41hwLOPJd/Pi0Hag4g52kOGAdDbgN3MQ3stxKNt+cAPYjm9D1QlvedLHbs7O",
    "0m7fyHhvi8NecJW7C3KCshx0Mq7SdNupUnWApZ11IaGxdcKcjnVRmDJ1TZSjdAqR/XNfjkxz8YuFclKIB3F2hXdvOYSmbhmC+mw0",
    "gSJstH94apB+32i7fWVnKH0YZpV8PWRYfPFiKXzgYFd8y10Nfc1aRX73V05/R1b/f3NVKoChVed/91bAf/BYzX8+WhuAKlyqgAZe",
    "LoE3XyeC52DwgvVhTIRnY2WFUGSlhiVl/YfYZXCJamYCi95mtYw3Z12Pi2cylLhnXJifZ4OcUmemoNJmC6e3ZTOvAWQewB9gIMUt",
    "XyfKXF7W0ypdUNfhXCDayVw83NZcQ94DXRcAJOTWX0nkp1+E5LRfmPzId3P9vXiB/kt6Df9le3n/inzy/+h+7P9QgZT/F4P1/s+E",
    "Dv5uhvX81ofr2eSqE90horXfOJnR4TGQZeMPh3Hk233z5Jl07ORQa6LkmWU="
  ].join("");
  const depth = 0.21616895;
  const duration = 2800;
  const hold = 120;
  // 2D master: SVG viewBox 0 0 1254 1254, centered at (627,627).
  // The source contour occupies x/y 176.69848..1077.30152 (half-extent 450.30152).
  // The packed mesh normalizes that same contour to [-1,1]; scale accordingly.
  const svgPoseScale = (2 * 450.30152) / 1254;

  function readContours() {
    const bytes = Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
    const view = new DataView(bytes.buffer);
    const contours = [];
    let index = 0;
    while (index < bytes.byteLength) {
      const count = view.getUint16(index, true);
      index += 2;
      const outline = [];
      for (let i = 0; i < count; i++) {
        outline.push([view.getUint16(index, true) / 32767.5 - 1,
          view.getUint16(index + 2, true) / 32767.5 - 1]);
        index += 4;
      }
      contours.push(outline);
    }
    return contours;
  }
  const cross = (a,b,c) => (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]);

  function triangulate(pts) {
    const remaining = pts.map((_,i) => i);
    const triangles = [];
    for (let step = 0; remaining.length > 3; step++) {
      if (step > pts.length * 2) throw Error("Unable to triangulate logo");
      let clipped = false;
      for (let i = 0; i < remaining.length; i++) {
        const a = remaining[(i+remaining.length-1)%remaining.length], b = remaining[i];
        const c = remaining[(i+1)%remaining.length];
        if (cross(pts[a],pts[b],pts[c]) <= 1e-9) continue;
        if (remaining.some(k => k !== a && k !== b && k !== c &&
          cross(pts[a],pts[b],pts[k]) > 1e-9 &&
          cross(pts[b],pts[c],pts[k]) > 1e-9 &&
          cross(pts[c],pts[a],pts[k]) > 1e-9)) continue;
        triangles.push([a,b,c]);
        remaining.splice(i,1);
        clipped = true;
        break;
      }
      if (!clipped) throw Error("Logo contour has no triangulation ear");
    }
    triangles.push(remaining);
    return triangles;
  }

  function makeMesh() {
    const triangles = [];
    // Each triangle carries an exact front/back face tag so its fill never
    // differs from the original black/white SVG. Only the extruded edges are shaded.
    const add = (a,b,c,cap) => {
      for (const vertex of [a,b,c]) triangles.push(...vertex,cap);
    };
    for (const outline of readContours()) {
      const front = outline.map(([x,y]) => [x,y,depth/2]);
      const back = outline.map(([x,y]) => [x,y,-depth/2]);
      for (const [a,b,c] of triangulate(outline)) {
        add(front[a],front[b],front[c],1);
        add(back[c],back[b],back[a],1);
      }
      for (let i=0; i<outline.length; i++) {
        const j=(i+1)%outline.length;
        add(front[i],back[i],front[j],0);
        add(front[j],back[i],back[j],0);
      }
    }
    return new Float32Array(triangles);
  }

  function shader(gl, kind, source) {
    const item=gl.createShader(kind);
    gl.shaderSource(item,source);
    gl.compileShader(item);
    if (!gl.getShaderParameter(item,gl.COMPILE_STATUS)) {
      const error=gl.getShaderInfoLog(item);
      gl.deleteShader(item);
      throw Error(error);
    }
    return item;
  }

  window.createRLogoSpin = (canvas,onFinish) => {
    const gl=canvas.getContext("webgl2",{alpha:true,antialias:true,depth:true});
    if (!gl) return null;
    const vert='#version 300 es\nprecision highp float;\nin vec3 aPosition;\nin float aCap;\nuniform mat3 uRotation;\nuniform float uScale,uAspect;\nout vec3 vPosition;\nflat out float vCap;\nvoid main(){vec3 p=uRotation*aPosition;vPosition=p;vCap=aCap;gl_Position=vec4(p.x*uScale/uAspect,p.y*uScale,-p.z*0.20,1.0);}';
    const frag='#version 300 es\nprecision highp float;\nin vec3 vPosition;\nflat in float vCap;\nuniform float uDark;\nout vec4 outputColor;\nvoid main(){if(vCap>0.5){outputColor=vec4(vec3(1.0-uDark),1.0);return;}vec3 n=normalize(cross(dFdx(vPosition),dFdy(vPosition)));if(!gl_FrontFacing)n=-n;float d=max(dot(n,normalize(vec3(-0.45,0.62,0.73))),0.0);float shade=0.55+0.30*d;vec3 side=mix(vec3(shade),vec3(0.055+0.065*d),uDark);outputColor=vec4(side,1.0);}';
    const program=gl.createProgram(), vs=shader(gl,gl.VERTEX_SHADER,vert), fs=shader(gl,gl.FRAGMENT_SHADER,frag);
    gl.attachShader(program,vs);
    gl.attachShader(program,fs);
    gl.linkProgram(program);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    if(!gl.getProgramParameter(program,gl.LINK_STATUS)) throw Error(gl.getProgramInfoLog(program));
    const vao=gl.createVertexArray();
    gl.bindVertexArray(vao);
    const mesh=makeMesh();
    const buffer=gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    gl.bufferData(gl.ARRAY_BUFFER,mesh,gl.STATIC_DRAW);
    const stride=4*Float32Array.BYTES_PER_ELEMENT;
    const loc=gl.getAttribLocation(program,"aPosition");
    const capLoc=gl.getAttribLocation(program,"aCap");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc,3,gl.FLOAT,false,stride,0);
    gl.enableVertexAttribArray(capLoc);
    gl.vertexAttribPointer(capLoc,1,gl.FLOAT,false,stride,3*Float32Array.BYTES_PER_ELEMENT);
    gl.bindVertexArray(null);
    const uniforms={
      rotation:gl.getUniformLocation(program,"uRotation"),
      scale:gl.getUniformLocation(program,"uScale"),
      aspect:gl.getUniformLocation(program,"uAspect"),
      dark:gl.getUniformLocation(program,"uDark")
    };
    let frame=0,finishTimer=0,start=0,active=false,generation=0;
    function render(progress,dark) {
      const ratio=Math.min(2,window.devicePixelRatio||1);
      const width=Math.max(1,Math.round(canvas.clientWidth*ratio));
      const height=Math.max(1,Math.round(canvas.clientHeight*ratio));
      if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}
      gl.viewport(0,0,width,height);
      // Retain the tap's initial impulse while extending a visibly slow, zero-velocity finish.
      // The initial angular velocity matches the previous 2.15s cubic curve.
      const remaining=1-progress;
      const smooth=1-remaining*remaining*(1-1.9*progress+2*progress*progress);
      const yaw=smooth*Math.PI*8; // four full turns, always finishing face-on
      // Keep the camera level with the XY face: Y-axis spin only, no pitch.
      const cy=Math.cos(yaw),sy=Math.sin(yaw);
      const rotation=new Float32Array([cy,0,-sy, 0,1,0, sy,0,cy]);
      gl.clearColor(0,0,0,0);
      gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      gl.enable(gl.DEPTH_TEST);
      gl.disable(gl.CULL_FACE);
      gl.useProgram(program);
      gl.bindVertexArray(vao);
      gl.uniformMatrix3fv(uniforms.rotation,false,rotation);
      // Use the master SVG's actual viewBox and contour bounds. Both layers now
      // share a centered square viewport regardless of canvas aspect ratio.
      // Do not add hand-tuned translations: they cause jumps on both transitions.
      gl.uniform1f(uniforms.scale,svgPoseScale*Math.min(1,width/height));
      gl.uniform1f(uniforms.aspect,width/height);
      gl.uniform1f(uniforms.dark,dark?1:0);
      gl.drawArrays(gl.TRIANGLES,0,mesh.length/4);
    }
    function stop() {
      active=false;
      generation++;
      cancelAnimationFrame(frame);
      clearTimeout(finishTimer);
      frame=0;finishTimer=0;
    }
    function play(dark, durationMs=duration) {
      stop();active=true;start=performance.now();
      const token=generation;
      render(0,dark);
      function tick(time) {
        if(!active||token!==generation)return;
        const progress=Math.min(1,(time-start)/durationMs);
        render(progress,dark);
        if(progress<1)frame=requestAnimationFrame(tick);
        else {
          frame=0;
          finishTimer=setTimeout(()=>{
            if(token!==generation)return;
            active=false;
            onFinish?.();
          },hold);
        }
      }
      frame=requestAnimationFrame(tick);
    }
    canvas.addEventListener("webglcontextlost",e=>{e.preventDefault();stop();onFinish?.();});
    document.addEventListener("visibilitychange",()=>{if(document.hidden&&active){stop();onFinish?.();}});
    return {play,stop,get active(){return active;},get triangles(){return mesh.length/12;}};
  };
})();