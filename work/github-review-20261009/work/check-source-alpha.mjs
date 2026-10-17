import {createRequire} from 'node:module';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');
const {createCanvas,loadImage}=require('@napi-rs/canvas');
const img=await loadImage('assets/fighters/diluc/source/diluc-half-side-v2-candidate.png');const canvas=createCanvas(img.width,img.height),ctx=canvas.getContext('2d');ctx.drawImage(img,0,0);const rgba=ctx.getImageData(0,0,img.width,img.height).data;let transparent=0,partial=0;for(let i=3;i<rgba.length;i+=4){if(rgba[i]===0)transparent++;else if(rgba[i]<255)partial++;}console.log(JSON.stringify({width:img.width,height:img.height,transparentPixels:transparent,partialAlphaPixels:partial,totalPixels:rgba.length/4}));
