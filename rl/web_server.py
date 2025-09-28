from flask import Flask, jsonify, render_template_string
import numpy as np
import logging as flask_logging
import json


def create_app(current_state, env):
    """Create and configure Flask application for trading visualization."""
    app = Flask(__name__)
    
    # Configure Flask to suppress access logs for cleaner training logs
    flask_log = flask_logging.getLogger('werkzeug')
    flask_log.setLevel(flask_logging.ERROR)  # Only show errors, not access logs
    
    @app.route('/')
    def index():
        """Serve the main visualization page."""
        return render_template_string(HTML_TEMPLATE)

    @app.route('/styles.css')
    def styles():
        """Serve CSS styles."""
        return CSS_STYLES, 200, {'Content-Type': 'text/css'}

    @app.route('/visualization.js')
    def visualization():
        """Serve JavaScript for visualization."""
        return JS_VISUALIZATION, 200, {'Content-Type': 'application/javascript'}

    @app.route('/state')
    def get_state():
        """Get current environment state."""
        return jsonify(current_state)

    @app.route('/environment')
    def get_environment():
        """Get detailed environment information."""
        if env:
            env_state = env.get_state()
            return jsonify(env_state)
        else:
            return jsonify({'error': 'Environment not available'})
    
    @app.route('/agents')
    def get_agents():
        """Get detailed agent information."""
        if env and env.agents:
            agents_data = []
            for agent in env.agents:
                agent_data = {
                    'id': agent.agent_id,
                    'position': agent.position.tolist(),
                    'inventory': agent.inventory,
                    'desired_item': agent.desired_item,
                    'fitness': agent.get_fitness(),  # Note: market_data not available in web context
                    'successful_trades': agent.successful_trades,
                    'attempted_trades': agent.attempted_trades,
                    'trading_matrix': agent.trading_matrix.tolist()
                }
                agents_data.append(agent_data)
            return jsonify(agents_data)
        else:
            return jsonify([])
    
    @app.route('/trades')
    def get_trades():
        """Get recent trade history."""
        if env:
            return jsonify(env.trade_history[-50:])  # Last 50 trades
        else:
            return jsonify([])
    
    @app.route('/statistics')
    def get_statistics():
        """Get environment statistics."""
        if env:
            try:
                from .utils import (calculate_trade_statistics, calculate_fitness_statistics, 
                                  analyze_trading_matrices, calculate_inventory_diversity)
            except ImportError:
                from utils import (calculate_trade_statistics, calculate_fitness_statistics, 
                                 analyze_trading_matrices, calculate_inventory_diversity)
            
            stats = {
                'trade_stats': calculate_trade_statistics(env.trade_history),
                'fitness_stats': calculate_fitness_statistics(env.agents),
                'matrix_analysis': analyze_trading_matrices(env.agents, env.items_list),
                'inventory_diversity': calculate_inventory_diversity(env.agents, env.items_list),
                'generation_stats': env.generation_stats[-10:] if env.generation_stats else []
            }
            return jsonify(stats)
        else:
            return jsonify({})
    
    return app


# HTML Template for the visualization page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent Trading Visualization</title>
    <link rel="stylesheet" href="/styles.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏪 Multi-Agent Trading Environment</h1>
            <div class="status-bar">
                <div class="status-item">
                    <span class="label">Generation:</span>
                    <span id="generation">0</span>
                </div>
                <div class="status-item">
                    <span class="label">Timestep:</span>
                    <span id="timestep">0</span>
                </div>
                <div class="status-item">
                    <span class="label">Agents:</span>
                    <span id="total-agents">0</span>
                </div>
                <div class="status-item">
                    <span class="label">Recent Trades:</span>
                    <span id="recent-trades">0</span>
                </div>
            </div>
        </header>

        <div class="main-content">
            <div class="left-panel">
                <div class="panel">
                    <h3>🎯 Trading World</h3>
                    <canvas id="world-canvas" width="400" height="400"></canvas>
                </div>
                
                <div class="panel">
                    <h3>📊 Fitness Distribution</h3>
                    <canvas id="fitness-chart" width="400" height="200"></canvas>
                </div>
            </div>

            <div class="right-panel">
                <div class="panel">
                    <h3>📈 Performance Metrics</h3>
                    <div class="metrics">
                        <div class="metric">
                            <span class="metric-label">Best Fitness:</span>
                            <span id="best-fitness" class="metric-value">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg Fitness:</span>
                            <span id="avg-fitness" class="metric-value">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Generation Progress:</span>
                            <div class="progress-bar">
                                <div id="generation-progress" class="progress-fill"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="panel">
                    <h3>🔄 Recent Trades</h3>
                    <div id="trades-list" class="trades-list"></div>
                </div>

                <div class="panel">
                    <h3>🏆 Top Agents</h3>
                    <div id="top-agents" class="agents-list"></div>
                </div>
            </div>
        </div>

        <div class="bottom-panel">
            <div class="panel">
                <h3>📊 Generation History</h3>
                <canvas id="generation-chart" width="800" height="200"></canvas>
            </div>
        </div>
    </div>

    <script src="/visualization.js"></script>
</body>
</html>
"""

# CSS Styles
CSS_STYLES = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #333;
    min-height: 100vh;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 30px;
}

header h1 {
    color: white;
    font-size: 2.5em;
    margin-bottom: 20px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.status-bar {
    display: flex;
    justify-content: center;
    gap: 30px;
    background: rgba(255,255,255,0.1);
    padding: 15px;
    border-radius: 10px;
    backdrop-filter: blur(10px);
}

.status-item {
    text-align: center;
}

.status-item .label {
    display: block;
    color: rgba(255,255,255,0.8);
    font-size: 0.9em;
    margin-bottom: 5px;
}

.status-item span:last-child {
    color: white;
    font-size: 1.2em;
    font-weight: bold;
}

.main-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
}

.left-panel, .right-panel {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.bottom-panel {
    width: 100%;
}

.panel {
    background: rgba(255,255,255,0.95);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    backdrop-filter: blur(10px);
}

.panel h3 {
    margin-bottom: 15px;
    color: #4a5568;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 10px;
}

#world-canvas {
    border: 2px solid #e2e8f0;
    border-radius: 10px;
    background: #f7fafc;
}

.metrics {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    background: #f7fafc;
    border-radius: 8px;
}

.metric-label {
    font-weight: 600;
    color: #4a5568;
}

.metric-value {
    font-weight: bold;
    color: #2d3748;
    font-size: 1.1em;
}

.progress-bar {
    width: 100px;
    height: 10px;
    background: #e2e8f0;
    border-radius: 5px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #48bb78, #38a169);
    transition: width 0.3s ease;
    width: 0%;
}

.trades-list, .agents-list {
    max-height: 200px;
    overflow-y: auto;
}

.trade-item, .agent-item {
    padding: 10px;
    margin-bottom: 8px;
    background: #f7fafc;
    border-radius: 8px;
    border-left: 4px solid #4299e1;
    font-size: 0.9em;
}

.trade-item:last-child, .agent-item:last-child {
    margin-bottom: 0;
}

.agent-item {
    border-left-color: #48bb78;
}

.agent-fitness {
    font-weight: bold;
    color: #2d3748;
}

.agent-desired {
    color: #4a5568;
    font-style: italic;
}

/* Responsive design */
@media (max-width: 768px) {
    .main-content {
        grid-template-columns: 1fr;
    }
    
    .status-bar {
        flex-direction: column;
        gap: 15px;
    }
    
    header h1 {
        font-size: 2em;
    }
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #a1a1a1;
}
"""

# JavaScript for visualization
JS_VISUALIZATION = """
class TradingVisualization {
    constructor() {
        this.worldCanvas = document.getElementById('world-canvas');
        this.worldCtx = this.worldCanvas.getContext('2d');
        this.fitnessChart = null;
        this.generationChart = null;
        this.agents = [];
        this.trades = [];
        this.statistics = {};
        
        this.initCharts();
        this.startUpdating();
    }
    
    initCharts() {
        // Fitness distribution chart
        const fitnessCtx = document.getElementById('fitness-chart').getContext('2d');
        this.fitnessChart = new Chart(fitnessCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Agent Fitness',
                    data: [],
                    backgroundColor: 'rgba(66, 153, 225, 0.6)',
                    borderColor: 'rgba(66, 153, 225, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        // Generation history chart
        const generationCtx = document.getElementById('generation-chart').getContext('2d');
        this.generationChart = new Chart(generationCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Best Fitness',
                    data: [],
                    borderColor: 'rgba(72, 187, 120, 1)',
                    backgroundColor: 'rgba(72, 187, 120, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Average Fitness',
                    data: [],
                    borderColor: 'rgba(66, 153, 225, 1)',
                    backgroundColor: 'rgba(66, 153, 225, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    async fetchData() {
        try {
            const [stateResponse, agentsResponse, tradesResponse, statsResponse] = await Promise.all([
                fetch('/state'),
                fetch('/agents'),
                fetch('/trades'),
                fetch('/statistics')
            ]);
            
            const state = await stateResponse.json();
            this.agents = await agentsResponse.json();
            this.trades = await tradesResponse.json();
            this.statistics = await statsResponse.json();
            
            this.updateUI(state);
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }
    
    updateUI(state) {
        // Update status bar
        document.getElementById('generation').textContent = state.generation || 0;
        document.getElementById('timestep').textContent = state.timestep || 0;
        document.getElementById('total-agents').textContent = state.total_agents || 0;
        document.getElementById('recent-trades').textContent = state.recent_trades || 0;
        
        // Update metrics
        document.getElementById('best-fitness').textContent = (state.best_fitness || 0).toFixed(2);
        document.getElementById('avg-fitness').textContent = (state.avg_fitness || 0).toFixed(2);
        
        // Update progress bar
        const progress = (state.generation_progress || 0) * 100;
        document.getElementById('generation-progress').style.width = progress + '%';
        
        // Update visualizations
        this.drawWorld();
        this.updateFitnessChart();
        this.updateTradesList();
        this.updateTopAgents();
        this.updateGenerationChart();
    }
    
    drawWorld() {
        const canvas = this.worldCanvas;
        const ctx = this.worldCtx;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw background grid
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        for (let i = 0; i <= canvas.width; i += 40) {
            ctx.beginPath();
            ctx.moveTo(i, 0);
            ctx.lineTo(i, canvas.height);
            ctx.stroke();
        }
        for (let i = 0; i <= canvas.height; i += 40) {
            ctx.beginPath();
            ctx.moveTo(0, i);
            ctx.lineTo(canvas.width, i);
            ctx.stroke();
        }
        
        if (!this.agents || this.agents.length === 0) return;
        
        // Find world bounds
        const worldSize = 100; // From config
        const scaleX = canvas.width / worldSize;
        const scaleY = canvas.height / worldSize;
        
        // Draw agents
        this.agents.forEach((agent, index) => {
            const x = agent.position[0] * scaleX;
            const y = agent.position[1] * scaleY;
            
            // Agent color based on fitness (green = high, red = low)
            const fitness = agent.fitness || 0;
            const maxFitness = Math.max(...this.agents.map(a => a.fitness || 0));
            const normalizedFitness = maxFitness > 0 ? fitness / maxFitness : 0;
            
            const red = Math.floor(255 * (1 - normalizedFitness));
            const green = Math.floor(255 * normalizedFitness);
            
            // Draw agent circle
            ctx.beginPath();
            ctx.arc(x, y, 6, 0, 2 * Math.PI);
            ctx.fillStyle = `rgb(${red}, ${green}, 0)`;
            ctx.fill();
            ctx.strokeStyle = '#2d3748';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Draw desired item indicator
            ctx.fillStyle = '#2d3748';
            ctx.font = '10px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(agent.desired_item ? agent.desired_item[0].toUpperCase() : '?', x, y + 3);
        });
        
        // Draw recent trades as lines
        if (this.trades && this.trades.length > 0) {
            ctx.strokeStyle = 'rgba(66, 153, 225, 0.5)';
            ctx.lineWidth = 2;
            
            this.trades.slice(-10).forEach(trade => {
                const requester = this.agents.find(a => a.id === trade.requester_id);
                const target = this.agents.find(a => a.id === trade.target_id);
                
                if (requester && target) {
                    const x1 = requester.position[0] * scaleX;
                    const y1 = requester.position[1] * scaleY;
                    const x2 = target.position[0] * scaleX;
                    const y2 = target.position[1] * scaleY;
                    
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();
                }
            });
        }
    }
    
    updateFitnessChart() {
        if (!this.agents || this.agents.length === 0) return;
        
        // Sort agents by fitness and take top 10
        const sortedAgents = this.agents
            .sort((a, b) => (b.fitness || 0) - (a.fitness || 0))
            .slice(0, 10);
        
        const labels = sortedAgents.map(agent => agent.id.split('_').pop());
        const data = sortedAgents.map(agent => agent.fitness || 0);
        
        this.fitnessChart.data.labels = labels;
        this.fitnessChart.data.datasets[0].data = data;
        this.fitnessChart.update('none');
    }
    
    updateTradesList() {
        const tradesList = document.getElementById('trades-list');
        
        if (!this.trades || this.trades.length === 0) {
            tradesList.innerHTML = '<div class="trade-item">No recent trades</div>';
            return;
        }
        
        const recentTrades = this.trades.slice(-5).reverse();
        tradesList.innerHTML = recentTrades.map(trade => {
            const gave = trade.requester_gave;
            const received = trade.requester_received;
            return `
                <div class="trade-item">
                    <strong>${trade.requester_id}</strong> ↔ <strong>${trade.target_id}</strong><br>
                    ${gave[1].toFixed(1)} ${gave[0]} → ${received[1].toFixed(1)} ${received[0]}
                </div>
            `;
        }).join('');
    }
    
    updateTopAgents() {
        const topAgents = document.getElementById('top-agents');
        
        if (!this.agents || this.agents.length === 0) {
            topAgents.innerHTML = '<div class="agent-item">No agents available</div>';
            return;
        }
        
        const sortedAgents = this.agents
            .sort((a, b) => (b.fitness || 0) - (a.fitness || 0))
            .slice(0, 5);
        
        topAgents.innerHTML = sortedAgents.map((agent, index) => `
            <div class="agent-item">
                <div><strong>#${index + 1} ${agent.id}</strong></div>
                <div class="agent-fitness">Fitness: ${(agent.fitness || 0).toFixed(2)}</div>
                <div class="agent-desired">Wants: ${agent.desired_item}</div>
                <div>Trades: ${agent.successful_trades}/${agent.attempted_trades}</div>
            </div>
        `).join('');
    }
    
    updateGenerationChart() {
        if (!this.statistics.generation_stats || this.statistics.generation_stats.length === 0) return;
        
        const stats = this.statistics.generation_stats;
        const labels = stats.map(s => `Gen ${s.generation}`);
        const bestFitness = stats.map(s => s.best_fitness);
        const avgFitness = stats.map(s => s.avg_fitness);
        
        this.generationChart.data.labels = labels;
        this.generationChart.data.datasets[0].data = bestFitness;
        this.generationChart.data.datasets[1].data = avgFitness;
        this.generationChart.update('none');
    }
    
    startUpdating() {
        this.fetchData();
        setInterval(() => this.fetchData(), 1000); // Update every second
    }
}

// Initialize visualization when page loads
document.addEventListener('DOMContentLoaded', () => {
    new TradingVisualization();
});
"""
