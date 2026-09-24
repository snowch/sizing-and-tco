---
title: "Sizing and TCO"
short_title: Cover
html: |
  <style>
    .cover-container {
      position: relative;
      max-width: 600px;
      margin: 0 auto;
      text-align: center;
      padding: 40px 20px;
    }
    
    .draft-watermark {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%) rotate(-45deg);
      font-size: 120px;
      font-weight: bold;
      color: rgba(200, 0, 0, 0.15);
      pointer-events: none;
      z-index: 1;
      white-space: nowrap;
    }
    
    .cover-content {
      position: relative;
      z-index: 2;
    }
    
    .cover-header {
      margin-bottom: 40px;
    }
    
    .cover-images {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 30px;
      margin: 40px 0;
      align-items: center;
    }
    
    .cover-images img, .cover-images svg {
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      background: white;
      padding: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    h1 {
      font-size: 3em;
      margin: 20px 0;
      color: #2c3e50;
    }
    
    .tagline {
      font-size: 1.2em;
      color: #666;
      margin: 20px 0;
      font-style: italic;
    }
    
    .byline {
      font-size: 1em;
      color: #999;
      margin-top: 60px;
    }
  </style>
  
  <div class="draft-watermark">DRAFT</div>
  
  <div class="cover-container">
    <div class="cover-content">
      <div class="cover-header">
        <h1>Sizing and TCO</h1>
        <p class="tagline">How to size a system, cost it, and know how much to trust the answer.</p>
      </div>
      
      <div class="cover-images">
        <img src="/public/cover-hero.svg" alt="Capacity scaling visualization showing growth over time with a ceiling">
        <img src="/public/cover-model.svg" alt="Model graph showing inputs feeding into computation and outputs">
      </div>
      
      <p class="byline">By Chris Snow</p>
    </div>
  </div>
---

(cover)=
