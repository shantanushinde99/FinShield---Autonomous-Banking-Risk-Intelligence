document.addEventListener("DOMContentLoaded", () => {
    checkHealth();
    startVoicePolling();
    
    const form = document.getElementById("investigate-form");
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const customerIdInput = document.getElementById("customer-id").value.trim();
        if (customerIdInput) {
            await runInvestigation(customerIdInput);
        }
    });
});

let voicePollingInterval;
async function startVoicePolling() {
    voicePollingInterval = setInterval(async () => {
        try {
            const res = await fetch("/api/v1/omi/status");
            if (res.ok) {
                const data = await res.json();
                updateVoiceUI(data);
            }
        } catch (e) {
            console.error("Voice polling error", e);
        }
    }, 2000);
}

function updateVoiceUI(data) {
    const stateEl = document.getElementById("voice-state");
    const transcriptEl = document.getElementById("voice-transcript");
    
    if (data.status === "IDLE") {
        stateEl.textContent = "Waiting for voice command...";
    } else {
        stateEl.textContent = `Status: ${data.status.replace('_', ' ')}`;
    }
    
    if (data.transcript) {
        transcriptEl.innerHTML = `<p>"${data.transcript}"</p>`;
    }
    
    if (data.spoken_summary) {
        transcriptEl.innerHTML += `<p class="placeholder-text mt-2">Omi says: "${data.spoken_summary}"</p>`;
    }
    
    // If voice triggered an investigation, auto-run it in the UI if not already running
    if (data.status === "INVESTIGATING" && data.customer_id) {
        const btn = document.getElementById("start-btn");
        if (!btn.disabled && document.getElementById("customer-id").value !== data.customer_id) {
            document.getElementById("customer-id").value = data.customer_id;
            runInvestigation(data.customer_id);
        }
    }
}

async function checkHealth() {
    try {
        const res = await fetch("/health/dependencies");
        const data = await res.json();
        
        const statusEl = document.getElementById("system-status");
        if (data.status === "healthy") {
            statusEl.innerHTML = `<span class="status-dot healthy"></span> System: Healthy`;
        } else if (data.status === "degraded") {
            statusEl.innerHTML = `<span class="status-dot degraded"></span> System: Degraded`;
        } else {
            statusEl.innerHTML = `<span class="status-dot error"></span> System: Error`;
        }
    } catch (e) {
        document.getElementById("system-status").innerHTML = `<span class="status-dot error"></span> System: Disconnected`;
    }
}

function resetUI() {
    document.getElementById("input-error").classList.add("hidden");
    document.getElementById("risk-section").classList.add("hidden");
    document.getElementById("breakdown-section").classList.add("hidden");
    document.getElementById("historical-section").classList.add("hidden");
    
    document.getElementById("trace-list").innerHTML = "";
    document.getElementById("trace-list").style.display = "block";
    document.querySelector(".trace-placeholder").style.display = "none";
    
    // Add pending states
    const traceList = document.getElementById("trace-list");
    const agents = ["Profile", "Credit", "Transactions", "Fraud", "Historical Memory", "Risk Decision"];
    
    agents.forEach(agent => {
        const li = document.createElement("li");
        li.className = "trace-item";
        li.id = `trace-${agent.replace(/\s+/g, '-').toLowerCase()}`;
        li.innerHTML = `
            <span class="trace-agent">${agent}</span>
            <div class="trace-meta">
                <span class="trace-status status-PENDING">PENDING</span>
            </div>
        `;
        traceList.appendChild(li);
    });
}

function renderTrace(trace) {
    if (!trace || !Array.length) return;
    
    // Map tool_names to display names
    const nameMap = {
        "analyze_profile": "profile",
        "analyze_credit": "credit",
        "analyze_transactions": "transactions",
        "analyze_fraud": "fraud",
        "retrieve_historical_cases": "historical-memory",
        "synthesize_risk_decision": "risk-decision"
    };

    trace.forEach(step => {
        const key = nameMap[step.tool_name];
        if (!key) return;
        
        const li = document.getElementById(`trace-${key}`);
        if (li) {
            const durationStr = step.duration_ms ? `${Math.round(step.duration_ms)} ms` : '';
            li.innerHTML = `
                <span class="trace-agent">${li.querySelector('.trace-agent').textContent}</span>
                <div class="trace-meta">
                    <span class="trace-duration">${durationStr}</span>
                    <span class="trace-status status-${step.status}">${step.status}</span>
                </div>
            `;
        }
    });
}

function renderResults(state) {
    if (!state.final_decision) return;
    const decision = state.final_decision;
    
    // Risk Section
    document.getElementById("risk-section").classList.remove("hidden");
    const riskBadge = document.getElementById("risk-level-badge");
    riskBadge.textContent = decision.risk_level.replace('_', ' ');
    riskBadge.className = `risk-badge risk-${decision.risk_level}`;
    
    document.getElementById("risk-score-value").textContent = decision.risk_score || "N/A";
    document.getElementById("confidence-value").textContent = decision.confidence;
    
    // Style the recommendation
    const recEl = document.getElementById("recommendation-value");
    recEl.textContent = decision.recommendation.replace('_', ' ');
    recEl.className = ''; // reset
    if (decision.recommendation === "APPROVE_RECOMMENDATION") recEl.classList.add('rec-approve');
    else if (decision.recommendation === "DECLINE_RECOMMENDATION") recEl.classList.add('rec-decline');
    else recEl.classList.add('rec-manual');
    
    let expText = decision.explanation;
    if (typeof expText === 'object') {
        expText = expText.summary || JSON.stringify(expText);
    }
    
    // Convert the summary paragraph into a bulleted list by splitting sentences
    let sentences = expText.split(/\.\s+/).filter(s => s.trim().length > 0);
    
    let richHtml = `<div class="summary-list"><ul>`;
    sentences.forEach(s => {
        let text = s.trim();
        if (!text.endsWith('.')) text += '.';
        richHtml += `<li>${text}</li>`;
    });
    richHtml += `</ul></div>`;
    
    if (decision.risk_factors && decision.risk_factors.length > 0) {
        richHtml += `<div class="factors-section factors-risk">
            <h4><span class="icon">⚠️</span> Risk Factors</h4>
            <ul>${decision.risk_factors.map(f => `<li>${f}</li>`).join('')}</ul>
        </div>`;
    }
    
    if (decision.positive_factors && decision.positive_factors.length > 0) {
        richHtml += `<div class="factors-section factors-positive">
            <h4><span class="icon">✅</span> Positive Factors</h4>
            <ul>${decision.positive_factors.map(f => `<li>${f}</li>`).join('')}</ul>
        </div>`;
    }
    
    document.getElementById("explanation-text").innerHTML = richHtml;

    // Breakdown Section
    document.getElementById("breakdown-section").classList.remove("hidden");
    const breakdownGrid = document.getElementById("breakdown-grid");
    breakdownGrid.innerHTML = ""; // Clear existing
    
    const categories = [
        { title: "Credit Risk", data: state.credit, levelKey: "risk_level" },
        { title: "Transaction Risk", data: state.transactions, levelKey: "risk_level" },
        { title: "Fraud Risk", data: state.fraud, levelKey: "risk_level" },
    ];
    
        categories.forEach(cat => {
        if (!cat.data) return;
        
        let evidenceHtml = "";
        const evidenceItems = cat.data.positive_factors || cat.data.positive_indicators || cat.data.key_factors || cat.data.suspicious_patterns || [];
        
        if (evidenceItems.length > 0) {
            evidenceItems.slice(0, 3).forEach(item => {
                 evidenceHtml += `<li>${item}</li>`;
            });
        } else {
            evidenceHtml = `<li style="color: rgba(255,255,255,0.4); list-style-type: none; padding-left: 0;">No notable indicators found.</li>`;
        }
        
        const card = document.createElement("div");
        card.className = "breakdown-card";
        const riskClass = cat.data[cat.levelKey] ? `risk-${cat.data[cat.levelKey]}` : '';
        
        card.innerHTML = `
            <h3>${cat.title} <span class="breakdown-level ${riskClass}" style="background:none; border:none; padding:0; font-size:12px;">${cat.data[cat.levelKey]}</span></h3>
            <ul class="evidence-list">
                ${evidenceHtml}
            </ul>
        `;
        breakdownGrid.appendChild(card);
    });
    
    // Historical Section
    if (state.historical && state.historical.similar_cases && state.historical.similar_cases.length > 0) {
        document.getElementById("historical-section").classList.remove("hidden");
        const list = document.getElementById("historical-list");
        list.innerHTML = "";
        
        state.historical.similar_cases.forEach(c => {
            
            // Extract key metrics from the dense Qdrant text
            const text = c.case_summary || "";
            const extract = (regex) => (text.match(regex) || [])[1] || "N/A";
            
            const income = extract(/Annual income:\s*(₹[\d,.]+)/);
            const debt = extract(/Outstanding debt:\s*(₹[\d,.]+)/);
            const txnVolume = extract(/Total transaction volume:\s*(₹[\d,.]+)/);
            const cashOut = extract(/Cash-out transactions:\s*(\d+)/);
            const fraudTx = extract(/Fraud transactions:\s*(\d+)/);
            const completion = extract(/Payment completion:\s*([^ ]+)/);
            
            const div = document.createElement("div");
            div.className = "historical-item";
            div.innerHTML = `
                <div class="historical-item-header">
                    <span>${c.case_id}</span>
                    <span class="sim-score">Similarity: ${(c.similarity_score || 0).toFixed(4)} <span class="risk-badge risk-${c.risk_level}">${c.risk_level}</span></span>
                </div>
                <div class="historical-metrics-grid">
                    <div class="metric-chip"><span class="label">Income</span><span class="val">${income}</span></div>
                    <div class="metric-chip"><span class="label">Debt</span><span class="val">${debt}</span></div>
                    <div class="metric-chip"><span class="label">Txn Vol</span><span class="val">${txnVolume}</span></div>
                    <div class="metric-chip"><span class="label">Cash-outs</span><span class="val">${cashOut}</span></div>
                    <div class="metric-chip"><span class="label">Fraud Tx</span><span class="val">${fraudTx}</span></div>
                    <div class="metric-chip"><span class="label">Pay History</span><span class="val">${completion}</span></div>
                </div>
            `;
            list.appendChild(div);
        });
    }
}

async function runInvestigation(customerId) {
    resetUI();
    const btn = document.getElementById("start-btn");
    const ogText = btn.textContent;
    btn.textContent = "Running Analysis...";
    btn.disabled = true;
    
    // Set UI to running state for trace
    document.querySelectorAll('.trace-status').forEach(el => {
        el.textContent = "RUNNING";
        el.className = "trace-status status-RUNNING";
    });
    
    try {
        const response = await fetch("/api/v1/investigate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ customer_id: customerId })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            const errEl = document.getElementById("input-error");
            errEl.textContent = data.error?.message || "An error occurred during investigation.";
            errEl.classList.remove("hidden");
            
            // Mark trace as failed
            document.querySelectorAll('.trace-status').forEach(el => {
                if (el.textContent === "RUNNING") {
                    el.textContent = "FAILED";
                    el.className = "trace-status status-FAILED";
                }
            });
            return;
        }
        
        // Success
        if (data.trace) renderTrace(data.trace);
        renderResults(data);
        
    } catch (error) {
        console.error(error);
        const errEl = document.getElementById("input-error");
        errEl.textContent = "Failed to connect to the server.";
        errEl.classList.remove("hidden");
    } finally {
        btn.textContent = ogText;
        btn.disabled = false;
    }
}
