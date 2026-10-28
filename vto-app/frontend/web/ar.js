// MediaPipe Pose bridge + WebGL sheer-fabric overlay. Loaded from web/index.html:
// <script type="module" src="ar.js"></script>
import { PoseLandmarker, FilesetResolver } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/+esm";
let landmarker, video, gl, prog, tex, opacity = 0.6, garmentImg = null;
const VS = `attribute vec2 p;varying vec2 uv;void main(){uv=p*.5+.5;uv.y=1.-uv.y;gl_Position=vec4(p,0,1);}`;
const FS = `precision mediump float;varying vec2 uv;uniform sampler2D t;uniform float a;uniform vec4 box;
void main(){vec2 q=(uv-box.xy)/box.zw;if(q.x<0.||q.x>1.||q.y<0.||q.y>1.)discard;
vec4 c=texture2D(t,q);gl_FragColor=vec4(c.rgb,c.a*a);}`;
function sh(t,s){const o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);return o;}
window.vtoAR = {
  async start(videoEl, canvas) {
    video = videoEl;
    const fs = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm");
    landmarker = await PoseLandmarker.createFromOptions(fs, {
      baseOptions: { modelAssetPath: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task", delegate: "GPU" },
      runningMode: "VIDEO" });
    gl = canvas.getContext("webgl", { premultipliedAlpha: false });
    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog); gl.useProgram(prog);
    const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
    const l = gl.getAttribLocation(prog, "p"); gl.enableVertexAttribArray(l); gl.vertexAttribPointer(l, 2, gl.FLOAT, false, 0, 0);
    tex = gl.createTexture();
    const loop = () => { frame(); requestAnimationFrame(loop); }; loop();
  },
  setGarment(url, op) {
    opacity = op; garmentImg = new Image(); garmentImg.crossOrigin = "anonymous"; garmentImg.src = url;
    garmentImg.onload = () => { gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, garmentImg);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); };
  },
};
function frame() {
  if (!landmarker || !video || video.readyState < 2 || !garmentImg?.complete) return;
  const r = landmarker.detectForVideo(video, performance.now());
  const k = r.landmarks?.[0]; if (!k) return;
  // 11/12 shoulders, 23/24 hips (left shoulder = saree pallu anchor)
  const xs = [k[11].x, k[12].x, k[23].x, k[24].x], ys = [k[11].y, k[12].y, k[23].y, k[24].y];
  const w = (Math.max(...xs) - Math.min(...xs)) * 1.5, h = (Math.max(...ys) - Math.min(...ys)) * 1.4;
  const x = (Math.min(...xs) + Math.max(...xs)) / 2 - w / 2, y = Math.min(...ys) - h * 0.12;
  gl.viewport(0, 0, gl.canvas.width, gl.canvas.height); gl.clear(gl.COLOR_BUFFER_BIT);
  gl.uniform1f(gl.getUniformLocation(prog, "a"), opacity);
  gl.uniform4f(gl.getUniformLocation(prog, "box"), x, y, w, h);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}
