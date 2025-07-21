#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basit YAML Karşılaştırma Web Arayüzü
FastAPI kullanarak basit YAML karşılaştırma uygulaması
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from simple_yaml_comparator import SimpleYamlComparator, YamlComparison
import json
from datetime import datetime
from dataclasses import asdict

app = FastAPI(
    title="Basit YAML Karşılaştırma Uygulaması",
    description="JSON dosya depolama ve mock AI kullanarak YAML dosyalarını karşılaştırır",
    version="1.0.0"
)

# Pydantic modelleri
class YamlInput(BaseModel):
    yaml_content: str

class ComparisonResult(BaseModel):
    rule_id: str
    rule_name: str
    similarity_score: float
    differences: List[str]
    similarities: List[str]
    ai_analysis: str
    comparison_date: str

# Global comparator instance
comparator = None

@app.on_event("startup")
async def startup_event():
    """Uygulama başlatma eventi"""
    global comparator
    comparator = SimpleYamlComparator()

@app.get("/", response_class=HTMLResponse)
async def get_home():
    """Ana sayfa HTML'i döndürür"""
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Basit YAML Karşılaştırma</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(45deg, #2196F3, #21CBF3);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
            }
            
            .main-content {
                padding: 40px;
            }
            
            .info-section {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                border-left: 4px solid #28a745;
            }
            
            .info-title {
                font-weight: bold;
                margin-bottom: 10px;
                color: #333;
            }
            
            .example-section {
                background: #f1f3f4;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            
            .example-title {
                font-weight: bold;
                margin-bottom: 10px;
                color: #333;
            }
            
            .example-yaml {
                background: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                overflow-x: auto;
            }
            
            .input-section {
                margin-bottom: 30px;
            }
            
            .input-section h2 {
                color: #333;
                margin-bottom: 15px;
                font-size: 1.5em;
            }
            
            .yaml-input {
                width: 100%;
                height: 300px;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                resize: vertical;
                transition: border-color 0.3s;
            }
            
            .yaml-input:focus {
                outline: none;
                border-color: #2196F3;
            }
            
            .button-section {
                text-align: center;
                margin: 30px 0;
            }
            
            .compare-btn {
                background: linear-gradient(45deg, #4CAF50, #45a049);
                color: white;
                border: none;
                padding: 15px 40px;
                font-size: 1.1em;
                border-radius: 25px;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
            }
            
            .compare-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
            }
            
            .compare-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            .loading {
                display: none;
                text-align: center;
                margin: 20px 0;
            }
            
            .loading-spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .results {
                margin-top: 30px;
            }
            
            .result-item {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 25px;
                margin-bottom: 20px;
                border-left: 5px solid #2196F3;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .result-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .result-title {
                font-size: 1.3em;
                font-weight: bold;
                color: #333;
            }
            
            .similarity-score {
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                color: white;
                padding: 8px 15px;
                border-radius: 20px;
                font-weight: bold;
            }
            
            .details-section {
                margin-top: 15px;
            }
            
            .details-title {
                font-weight: bold;
                color: #555;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
            }
            
            .details-title::before {
                content: "📋";
                margin-right: 8px;
            }
            
            .ai-analysis .details-title::before {
                content: "🤖";
            }
            
            .details-list {
                background: white;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 15px;
            }
            
            .details-list div {
                margin-bottom: 5px;
                padding: 5px;
                border-radius: 3px;
            }
            
            .similarity-item {
                background: #d4edda;
                color: #155724;
            }
            
            .difference-item {
                background: #f8d7da;
                color: #721c24;
            }
            
            .ai-analysis {
                background: #e7f3ff;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #007bff;
                white-space: pre-line;
            }
            
            .file-upload {
                margin-bottom: 20px;
            }
            
            .file-input {
                display: none;
            }
            
            .file-label {
                display: inline-block;
                background: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                transition: background 0.3s;
            }
            
            .file-label:hover {
                background: #5a6268;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Basit YAML Karşılaştırma</h1>
                <p>JSON dosya depolama ve mock AI ile güçlendirilmiş YAML analizi</p>
            </div>
            
            <div class="main-content">
                <div class="info-section">
                    <div class="info-title">ℹ️ Uygulama Hakkında</div>
                    <p>Bu uygulama MongoDB veya Ollama AI gerektirmez. Kurallar JSON dosyasında saklanır ve AI analizi mock olarak yapılır. Hızlı test için idealdir!</p>
                </div>
                
                <div class="example-section">
                    <div class="example-title">📝 Örnek YAML (Test için kullanabilirsiniz):</div>
                    <div class="example-yaml">server:
  host: localhost
  port: 9000
  ssl: false
database:
  type: postgresql
  host: db.example.com
  port: 5432</div>
                </div>
                
                <div class="input-section">
                    <h2>📄 YAML İçeriğinizi Girin</h2>
                    <div class="file-upload">
                        <input type="file" id="fileInput" class="file-input" accept=".yml,.yaml" />
                        <label for="fileInput" class="file-label">📁 YAML Dosyası Yükle</label>
                        <span id="fileName" style="margin-left: 10px; color: #666;"></span>
                    </div>
                    <textarea 
                        id="yamlInput" 
                        class="yaml-input" 
                        placeholder="YAML içeriğinizi buraya yapıştırın veya yukarıdan dosya yükleyin..."
                    ></textarea>
                </div>
                
                <div class="button-section">
                    <button id="compareBtn" class="compare-btn" onclick="compareYaml()">
                        🔍 Karşılaştır
                    </button>
                </div>
                
                <div id="loading" class="loading">
                    <div class="loading-spinner"></div>
                    <p>Mock AI analizi yapılıyor, lütfen bekleyin...</p>
                </div>
                
                <div id="results" class="results"></div>
            </div>
        </div>
        
        <script>
            // Dosya yükleme
            document.getElementById('fileInput').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    document.getElementById('fileName').textContent = file.name;
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById('yamlInput').value = e.target.result;
                    };
                    reader.readAsText(file);
                }
            });
            
            async function compareYaml() {
                const yamlContent = document.getElementById('yamlInput').value.trim();
                
                if (!yamlContent) {
                    alert('Lütfen YAML içeriği girin!');
                    return;
                }
                
                const compareBtn = document.getElementById('compareBtn');
                const loading = document.getElementById('loading');
                const results = document.getElementById('results');
                
                // UI durumunu güncelle
                compareBtn.disabled = true;
                loading.style.display = 'block';
                results.innerHTML = '';
                
                try {
                    const response = await fetch('/compare', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            yaml_content: yamlContent
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Karşılaştırma başarısız oldu');
                    }
                    
                    const data = await response.json();
                    displayResults(data);
                    
                } catch (error) {
                    console.error('Hata:', error);
                    results.innerHTML = `<div style="color: red; text-align: center; padding: 20px;">
                        Hata oluştu: ${error.message}
                    </div>`;
                } finally {
                    compareBtn.disabled = false;
                    loading.style.display = 'none';
                }
            }
            
            function displayResults(comparisons) {
                const resultsDiv = document.getElementById('results');
                
                if (!comparisons || comparisons.length === 0) {
                    resultsDiv.innerHTML = '<p style="text-align: center; color: #666;">Sonuç bulunamadı.</p>';
                    return;
                }
                
                let html = '<h2 style="margin-bottom: 20px; color: #333;">🎯 Karşılaştırma Sonuçları</h2>';
                
                comparisons.forEach((comp, index) => {
                    const scorePercent = (comp.similarity_score * 100).toFixed(1);
                    
                    html += `
                        <div class="result-item">
                            <div class="result-header">
                                <div class="result-title">${index + 1}. ${comp.rule_name}</div>
                                <div class="similarity-score">${scorePercent}% Benzer</div>
                            </div>
                            
                            <div class="details-section">
                                <div class="details-title">Benzerlikler (${comp.similarities.length} adet)</div>
                                <div class="details-list">
                                    ${comp.similarities.slice(0, 5).map(sim => 
                                        `<div class="similarity-item">✓ ${sim}</div>`
                                    ).join('')}
                                    ${comp.similarities.length > 5 ? 
                                        `<div style="color: #666; font-style: italic;">... ve ${comp.similarities.length - 5} adet daha</div>` 
                                        : ''}
                                </div>
                            </div>
                            
                            <div class="details-section">
                                <div class="details-title">Farklar (${comp.differences.length} adet)</div>
                                <div class="details-list">
                                    ${comp.differences.slice(0, 5).map(diff => 
                                        `<div class="difference-item">✗ ${diff}</div>`
                                    ).join('')}
                                    ${comp.differences.length > 5 ? 
                                        `<div style="color: #666; font-style: italic;">... ve ${comp.differences.length - 5} adet daha</div>` 
                                        : ''}
                                </div>
                            </div>
                            
                            <div class="details-section">
                                <div class="details-title ai-analysis">Mock AI Analizi</div>
                                <div class="ai-analysis">
                                    ${comp.ai_analysis}
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                resultsDiv.innerHTML = html;
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/compare", response_model=List[ComparisonResult])
async def compare_yaml(yaml_input: YamlInput):
    """YAML karşılaştırma endpoint'i"""
    global comparator
    
    if not comparator:
        raise HTTPException(status_code=500, detail="Comparator başlatılamadı")
    
    try:
        # Karşılaştırma yap
        results = comparator.compare_with_rules(yaml_input.yaml_content)
        
        # Sonuçları API formatına çevir
        api_results = []
        for result in results:
            api_result = ComparisonResult(
                rule_id=result.rule_id,
                rule_name=result.rule_name,
                similarity_score=result.similarity_score,
                differences=result.differences,
                similarities=result.similarities,
                ai_analysis=result.ai_analysis,
                comparison_date=result.comparison_date
            )
            api_results.append(api_result)
        
        return api_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Karşılaştırma hatası: {str(e)}")

@app.post("/upload")
async def upload_yaml_file(file: UploadFile = File(...)):
    """YAML dosya yükleme endpoint'i"""
    if not file.filename.endswith(('.yml', '.yaml')):
        raise HTTPException(status_code=400, detail="Sadece YAML dosyaları kabul edilir")
    
    try:
        content = await file.read()
        yaml_content = content.decode('utf-8')
        
        return {"yaml_content": yaml_content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya okuma hatası: {str(e)}")

@app.get("/rules")
async def get_rules():
    """Kuralları döndürür"""
    global comparator
    
    if not comparator:
        raise HTTPException(status_code=500, detail="Comparator başlatılamadı")
    
    try:
        rules = [{"id": rule["id"], "name": rule["name"], "description": rule["description"], "tags": rule["tags"]} 
                for rule in comparator.rules]
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kurallar alınamadı: {str(e)}")

@app.get("/health")
async def health_check():
    """Sağlık kontrolü"""
    return {"status": "healthy", "message": "Basit YAML karşılaştırıcı çalışıyor"}

if __name__ == "__main__":
    uvicorn.run(
        "simple_web_interface:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )