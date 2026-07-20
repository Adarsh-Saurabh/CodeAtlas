import React, { useRef, useEffect, useState } from 'react';

const CNNCanvas = ({ nodes = [], activeNodeIndex = 0, packetProgress = 0 }) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.clientWidth;
        const containerHeight = containerRef.current.clientHeight || 400;
        const requiredWidth = Math.max(containerWidth, nodes.length * 160 + 200);
        setDimensions({ width: requiredWidth, height: containerHeight });
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [nodes.length]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    canvas.width = dimensions.width * dpr;
    canvas.height = dimensions.height * dpr;
    canvas.style.width = `${dimensions.width}px`;
    canvas.style.height = `${dimensions.height}px`;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, dimensions.width, dimensions.height);
    
    // Background
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, dimensions.width, dimensions.height);

    const centerY = dimensions.height / 2;
    const spacing = 160;
    const startX = 100;

    const drawnNodes = [];

    // Helper functions
    const drawIsometricCube = (ctx, x, y, sizeX, sizeY, depth, colorStr, label, hasGrid = false) => {
      ctx.save();
      ctx.translate(x, y);
      
      const angle = Math.PI / 6; 
      const cosA = Math.cos(angle);
      const sinA = Math.sin(angle);
      
      const color = colorStr || '#3b82f6';
      
      // Top face
      ctx.fillStyle = adjustBrightness(color, 40);
      ctx.beginPath();
      ctx.moveTo(0, -sizeY);
      ctx.lineTo(depth * cosA, -sizeY - depth * sinA);
      ctx.lineTo(sizeX + depth * cosA, -sizeY - depth * sinA + sizeX * sinA);
      ctx.lineTo(sizeX, -sizeY + sizeX * sinA);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Right face
      ctx.fillStyle = adjustBrightness(color, -20);
      ctx.beginPath();
      ctx.moveTo(sizeX, -sizeY + sizeX * sinA);
      ctx.lineTo(sizeX + depth * cosA, -sizeY - depth * sinA + sizeX * sinA);
      ctx.lineTo(sizeX + depth * cosA, depth * sinA + sizeX * sinA);
      ctx.lineTo(sizeX, sizeY + sizeX * sinA);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Front face
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(0, -sizeY);
      ctx.lineTo(sizeX, -sizeY + sizeX * sinA);
      ctx.lineTo(sizeX, sizeY + sizeX * sinA);
      ctx.lineTo(0, sizeY);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      
      if (hasGrid) {
        ctx.strokeStyle = adjustBrightness(color, 20);
        for(let i=1; i<4; i++) {
          ctx.beginPath();
          ctx.moveTo(i*sizeX/4, -sizeY + i*sizeX/4*sinA);
          ctx.lineTo(i*sizeX/4, sizeY + i*sizeX/4*sinA);
          ctx.stroke();
          
          ctx.beginPath();
          ctx.moveTo(0, -sizeY + i*2*sizeY/4);
          ctx.lineTo(sizeX, -sizeY + sizeX*sinA + i*2*sizeY/4);
          ctx.stroke();
        }
      }

      ctx.restore();
      return { cx: x + sizeX / 2, cy: y, w: sizeX + depth, h: sizeY * 2 + depth };
    };

    const adjustBrightness = (hex, percent) => {
      let num = parseInt(hex.replace('#',''), 16),
        amt = Math.round(2.55 * percent),
        R = (num >> 16) + amt,
        B = (num >> 8 & 0x00FF) + amt,
        G = (num & 0x0000FF) + amt;
      return "#" + (0x1000000 + (R<255?R<1?0:R:255)*0x10000 + (B<255?B<1?0:B:255)*0x100 + (G<255?G<1?0:G:255)).toString(16).slice(1);
    };

    // Draw Nodes
    nodes.forEach((node, idx) => {
      const cx = startX + idx * spacing;
      const cy = centerY;
      
      let opacity = 1;
      let filter = 'none';
      if (idx < activeNodeIndex) {
        opacity = 0.7;
        filter = 'hue-rotate(90deg) saturate(150%) brightness(120%)';
      } else if (idx > activeNodeIndex) {
        opacity = 0.35;
        filter = 'grayscale(100%)';
      }
      
      ctx.save();
      ctx.globalAlpha = opacity;
      ctx.filter = filter;
      
      if (idx === activeNodeIndex) {
        ctx.shadowColor = '#ffffff';
        ctx.shadowBlur = 15;
      }
      
      let bounds = { cx, cy, w: 60, h: 60 };
      const cat = node.category || 'generic';
      const color = node.color || '#3b82f6';
      
      let scale = idx === activeNodeIndex ? 1.1 : 1.0;
      ctx.translate(cx, cy);
      ctx.scale(scale, scale);
      ctx.translate(-cx, -cy);

      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1;

      if (cat === 'conv' || cat === 'pool') {
        const stackCount = Math.min(node.shape ? node.shape[0] : (cat === 'conv' ? 5 : 3), 20);
        const sizeX = cat === 'conv' ? 40 : 25;
        const sizeY = cat === 'conv' ? 60 : 35;
        for (let i = stackCount - 1; i >= 0; i--) {
          const offsetX = i * 4 - (stackCount*2);
          const offsetY = -i * 4 + (stackCount*2);
          
          ctx.fillStyle = adjustBrightness(color, i*2);
          ctx.beginPath();
          ctx.moveTo(cx + offsetX, cy + offsetY - sizeY/2);
          ctx.lineTo(cx + offsetX + sizeX, cy + offsetY - sizeY/2 + 20);
          ctx.lineTo(cx + offsetX + sizeX, cy + offsetY + sizeY/2 + 20);
          ctx.lineTo(cx + offsetX, cy + offsetY + sizeY/2);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        }
        bounds = { cx, cy, w: sizeX + stackCount*4, h: sizeY + 20 + stackCount*4 };
      } 
      else if (cat === 'dense') {
        const count = Math.min(node.shape ? node.shape[0] : 6, 8);
        const radius = 8;
        const hSpace = 20;
        ctx.fillStyle = color;
        for(let i=0; i<count; i++) {
          const y = cy - ((count-1)*hSpace)/2 + i*hSpace;
          ctx.beginPath();
          ctx.arc(cx, y, radius, 0, Math.PI*2);
          ctx.fill();
          ctx.stroke();
        }
        if (node.shape && node.shape[0] > 8) {
          ctx.fillStyle = '#fff';
          ctx.font = '16px monospace';
          ctx.fillText('⋮', cx - 4, cy + ((count-1)*hSpace)/2 + 15);
        }
        bounds = { cx, cy, w: radius*2, h: count*hSpace };
      }
      else if (cat === 'input') {
        bounds = drawIsometricCube(ctx, cx - 20, cy, 30, 40, 20, color, null, true);
      }
      else if (cat === 'output') {
        const count = Math.min(node.shape ? node.shape[0] : 4, 10);
        const radius = 12;
        const hSpace = 30;
        ctx.fillStyle = color;
        for(let i=0; i<count; i++) {
          const y = cy - ((count-1)*hSpace)/2 + i*hSpace;
          ctx.beginPath();
          ctx.arc(cx, y, radius, 0, Math.PI*2);
          ctx.fill();
          ctx.stroke();
          ctx.fillStyle = '#fff';
          ctx.font = '10px monospace';
          ctx.fillText(i, cx - 3, y + 3);
          ctx.fillStyle = color;
        }
        bounds = { cx, cy, w: radius*2, h: count*hSpace };
      }
      else if (cat === 'activation') {
        const w = 40, h = 40;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.roundRect(cx - w/2, cy - h/2, w, h, 8);
        ctx.fill();
        ctx.stroke();
        
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx - 10, cy + 10);
        ctx.lineTo(cx, cy + 10);
        ctx.lineTo(cx + 10, cy - 10);
        ctx.stroke();
        ctx.lineWidth = 1;
      }
      else if (cat === 'normalization' || cat === 'regularization') {
        const w = 30, h = 60;
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.5 * opacity;
        ctx.setLineDash([4, 4]);
        ctx.fillRect(cx - w/2, cy - h/2, w, h);
        ctx.strokeRect(cx - w/2, cy - h/2, w, h);
        ctx.setLineDash([]);
        ctx.globalAlpha = opacity;
        bounds = { cx, cy, w, h };
      }
      else if (cat === 'reshape') {
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(cx - 20, cy - 40);
        ctx.lineTo(cx + 20, cy - 10);
        ctx.lineTo(cx + 20, cy + 10);
        ctx.lineTo(cx - 20, cy + 40);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }
      else if (cat === 'server') {
        bounds = drawIsometricCube(ctx, cx - 20, cy - 10, 30, 40, 20, color, null);
        ctx.fillStyle = '#0f0';
        ctx.beginPath();
        ctx.arc(cx + 5, cy, 3, 0, Math.PI*2);
        ctx.fill();
      }
      else if (cat === 'database') {
        const w = 40, h = 60;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.ellipse(cx, cy - h/2, w/2, 10, 0, 0, Math.PI*2);
        ctx.fill();
        ctx.stroke();
        
        ctx.beginPath();
        ctx.moveTo(cx - w/2, cy - h/2);
        ctx.lineTo(cx - w/2, cy + h/2);
        ctx.ellipse(cx, cy + h/2, w/2, 10, 0, Math.PI, 0, true);
        ctx.lineTo(cx + w/2, cy - h/2);
        ctx.fill();
        ctx.stroke();
        bounds = { cx, cy, w, h };
      }
      else if (cat === 'client') {
        const w = 50, h = 35;
        ctx.fillStyle = color;
        ctx.fillRect(cx - w/2, cy - h/2, w, h);
        ctx.strokeRect(cx - w/2, cy - h/2, w, h);
        ctx.fillStyle = '#666';
        ctx.fillRect(cx - 10, cy + h/2, 20, 10);
        ctx.fillRect(cx - 20, cy + h/2 + 10, 40, 5);
        bounds = { cx, cy, w, h: h + 15 };
      }
      else if (cat === 'api' || cat === 'route') {
        const w = 60, h = 30;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.roundRect(cx - w/2, cy - h/2, w, h, 15);
        ctx.fill();
        ctx.stroke();
        bounds = { cx, cy, w, h };
      }
      else if (cat === 'queue') {
        const w = 60, h = 20;
        ctx.fillStyle = '#444';
        ctx.beginPath();
        ctx.roundRect(cx - w/2, cy - h/2, w, h, 10);
        ctx.fill();
        ctx.fillStyle = color;
        ctx.fillRect(cx - 15, cy - h/2 - 10, 10, 10);
        ctx.fillRect(cx + 5, cy - h/2 - 10, 10, 10);
        bounds = { cx, cy, w, h: h + 10 };
      }
      else if (cat === 'cache') {
        const w = 40, h = 40;
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.5 * opacity;
        ctx.fillRect(cx - w/2, cy - h/2, w, h);
        ctx.globalAlpha = opacity;
        ctx.strokeRect(cx - w/2, cy - h/2, w, h);
        ctx.fillStyle = '#eab308';
        ctx.font = '24px Arial';
        ctx.fillText('⚡', cx - 12, cy + 8);
        bounds = { cx, cy, w, h };
      }
      else {
        bounds = drawIsometricCube(ctx, cx - 15, cy, 25, 25, 20, color, null);
      }
      
      // Node Title
      ctx.fillStyle = '#fff';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(node.title || node.id, cx, cy + bounds.h/2 + 25);
      
      drawnNodes.push(bounds);
      ctx.restore();
    });

    // Draw Connections
    drawnNodes.forEach((node, idx) => {
      if (idx === 0) return;
      const prevNode = drawnNodes[idx - 1];
      
      ctx.save();
      const startX = prevNode.cx + prevNode.w/2 + 10;
      const endX = node.cx - node.w/2 - 10;
      
      ctx.beginPath();
      ctx.moveTo(startX, prevNode.cy);
      
      if (idx <= activeNodeIndex) {
        ctx.strokeStyle = '#2ed573';
        ctx.lineWidth = 3;
        if (idx === activeNodeIndex) {
          ctx.shadowColor = '#2ed573';
          ctx.shadowBlur = 10;
        }
      } else {
        ctx.strokeStyle = '#555';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
      }
      
      ctx.bezierCurveTo(
        startX + (endX - startX)/2, prevNode.cy,
        startX + (endX - startX)/2, node.cy,
        endX, node.cy
      );
      ctx.stroke();
      
      // Arrow head
      ctx.beginPath();
      ctx.moveTo(endX, node.cy);
      ctx.lineTo(endX - 8, node.cy - 5);
      ctx.lineTo(endX - 8, node.cy + 5);
      ctx.fillStyle = ctx.strokeStyle;
      ctx.fill();
      ctx.restore();
    });

    // Draw Data Packet
    if (packetProgress > 0 && activeNodeIndex > 0 && activeNodeIndex < nodes.length) {
      const prevNode = drawnNodes[activeNodeIndex - 1];
      const currNode = drawnNodes[activeNodeIndex];
      const startX = prevNode.cx + prevNode.w/2 + 10;
      const endX = currNode.cx - currNode.w/2 - 10;
      
      const px = startX + (endX - startX) * packetProgress;
      const py = prevNode.cy + (currNode.cy - prevNode.cy) * packetProgress; // simplified linear interpolation
      
      ctx.save();
      ctx.beginPath();
      ctx.arc(px, py, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#2ed573';
      ctx.shadowColor = '#2ed573';
      ctx.shadowBlur = 15;
      ctx.fill();
      ctx.restore();
    }

    // Draw Math overlay for active node
    const activeNode = nodes[activeNodeIndex];
    if (activeNode && activeNode.math) {
      const b = drawnNodes[activeNodeIndex];
      ctx.save();
      ctx.font = 'bold 14px monospace';
      const textWidth = ctx.measureText(activeNode.math).width;
      const padding = 10;
      
      const boxX = b.cx - textWidth/2 - padding;
      const boxY = b.cy - b.h/2 - 60;
      const boxW = textWidth + padding * 2;
      const boxH = 30;
      
      ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxW, boxH, 5);
      ctx.fill();
      
      ctx.strokeStyle = '#eab308';
      ctx.lineWidth = 1;
      ctx.stroke();
      
      ctx.fillStyle = '#eab308';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(activeNode.math, b.cx, boxY + boxH/2);
      ctx.restore();
    }

  }, [nodes, activeNodeIndex, packetProgress, dimensions]);

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%', overflowX: 'auto', overflowY: 'hidden', backgroundColor: '#0f172a' }}>
      <canvas ref={canvasRef} style={{ display: 'block' }} />
    </div>
  );
};

export default CNNCanvas;
