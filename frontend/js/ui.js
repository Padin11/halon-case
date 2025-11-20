
const formatMoney = (valor) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
};

export const ui = {
    
    //CONTROLE DE TELAS
    toggleScreens: (isLogged) => {
        const loginScreen = document.getElementById('loginScreen');
        const appScreen = document.getElementById('appScreen');
        if (isLogged) {
            loginScreen.classList.add('hidden');
            appScreen.classList.remove('hidden');
        } else {
            loginScreen.classList.remove('hidden');
            appScreen.classList.add('hidden');
        }
    },

    showLoginError: (show) => {
        const el = document.getElementById('loginError');
        show ? el.classList.remove('hidden') : el.classList.add('hidden');
    },

    //CARDS E TABELAS
    renderCards: (dados) => {
        const setVal = (id, val, colorir = false) => {
            const el = document.getElementById(id);
            el.innerText = formatMoney(val);
            if (colorir) {
                el.className = `h3 fw-bold mb-0 ${val >= 0 ? 'text-primary' : 'text-danger'}`;
            }
        };
        setVal('valSaldo', dados.saldo_geral, true);
        setVal('valReceber', dados.total_a_receber);
        setVal('valPagar', dados.total_a_pagar);
        setVal('valVencido', dados.total_inadimplente);
    },

    renderTabela: (dados) => {
        const tbody = document.getElementById('tabelaTitulos');
        tbody.innerHTML = ''; 
        dados.forEach(t => {
            const tr = document.createElement('tr');
            const tdData = document.createElement('td');
            tdData.textContent = new Date(t.data_vencimento).toLocaleDateString('pt-BR');
            tr.appendChild(tdData);

            const tdDesc = document.createElement('td');
            tdDesc.textContent = t.descricao; 
            if(t.parcelado) {
                const small = document.createElement('small');
                small.className = "text-muted d-block";
                small.textContent = `Parcela ${t.numero_parcela}/${t.total_parcelas}`;
                tdDesc.appendChild(small);
            }
            tr.appendChild(tdDesc);

            const tdStatus = document.createElement('td');
            let badgeClass = 'bg-secondary';
            if(t.status === 'PAGO') badgeClass = 'bg-success';
            if(t.status === 'VENCIDO') badgeClass = 'bg-danger';
            if(t.status === 'PENDENTE') badgeClass = 'bg-warning text-dark';
            tdStatus.innerHTML = `<span class="badge ${badgeClass}">${t.status}</span>`;
            tr.appendChild(tdStatus);

            const tdVal = document.createElement('td');
            tdVal.className = "text-end fw-bold";
            const valorFormatado = formatMoney(t.valor);
            if(t.tipo === 'RECEITA') {
                tdVal.classList.add('text-success');
                tdVal.textContent = valorFormatado;
            } else {
                tdVal.classList.add('text-danger');
                tdVal.textContent = '- ' + valorFormatado;
            }
            tr.appendChild(tdVal);
            tbody.appendChild(tr);
        });
    },

    renderRankings: (dados) => {
        const buildList = (lista, containerId, corBadge) => {
            const el = document.getElementById(containerId);
            el.innerHTML = '';
            if (!lista || lista.length === 0) {
                el.innerHTML = '<li class="list-group-item text-muted">Sem dados recentes.</li>';
                return;
            }
            lista.forEach(item => {
                const li = document.createElement('li');
                li.className = "list-group-item d-flex justify-content-between align-items-center";
                const iniciais = item.nome.substring(0,2).toUpperCase();
                li.innerHTML = `
                    <div class="d-flex align-items-center">
                        <div class="avatar-initial shadow-sm">${iniciais}</div>
                        <div class="fw-bold text-dark text-truncate" style="max-width: 150px;">${item.nome}</div>
                    </div>
                    <span class="badge bg-${corBadge} rounded-pill">${formatMoney(item.total)}</span>
                `;
                el.appendChild(li);
            });
        };
        buildList(dados.devedores, 'listaDevedores', 'danger');
        buildList(dados.credores, 'listaCredores', 'warning text-dark');
    },

    
    renderResultadosBusca: (resultados) => {
        const lista = document.getElementById('listaBusca');
        lista.innerHTML = '';

        if (!resultados || resultados.length === 0) {
            lista.innerHTML = '<li class="list-group-item text-muted text-center py-3">Nenhum contato encontrado.</li>';
            return;
        }

        resultados.forEach(item => {
            const li = document.createElement('li');
            li.className = "list-group-item d-flex justify-content-between align-items-center";
            
            let badgesHtml = '';
            if (item.a_receber > 0) badgesHtml += `<span class="badge bg-danger me-2">Deve: ${formatMoney(item.a_receber)}</span>`;
            if (item.a_pagar > 0) badgesHtml += `<span class="badge bg-warning text-dark">Pagar: ${formatMoney(item.a_pagar)}</span>`;
            if (item.a_receber === 0 && item.a_pagar === 0) badgesHtml = `<span class="badge bg-success">Sem pendências</span>`;

            li.innerHTML = `
                <div class="fw-bold text-dark text-truncate" style="max-width: 200px;">${item.nome}</div>
                <div>${badgesHtml}</div>
            `;
            lista.appendChild(li);
        });
    },

    toggleModoBusca: (ativarBusca) => {
        const ranking = document.getElementById('areaRankingsPadrao');
        const busca = document.getElementById('areaBuscaResultados');
        
        if (ativarBusca) {
            ranking.classList.add('hidden');
            busca.classList.remove('hidden');
        } else {
            ranking.classList.remove('hidden');
            busca.classList.add('hidden');
        }
    },

    // GRÁFICOS
    charts: {
        catChart: null,
        fluxoChart: null,
        
        renderPizza: (dados) => {
            const ctx = document.getElementById('chartCategoria');
            if (ui.charts.catChart) ui.charts.catChart.destroy();
            ui.charts.catChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: dados.map(d => d.categoria),
                    datasets: [{
                        data: dados.map(d => d.total),
                        backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'],
                        borderWidth: 0
                    }]
                },
                options: { maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'right', labels: { boxWidth: 12 } } } }
            });
        },
        renderBarras: (dados) => {
            const ctx = document.getElementById('chartFluxo');
            if (ui.charts.fluxoChart) ui.charts.fluxoChart.destroy();
            ui.charts.fluxoChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: dados.map(d => d.mes),
                    datasets: [
                        { label: 'Entradas', data: dados.map(d => d.receitas), backgroundColor: '#1cc88a', borderRadius: 4 },
                        { label: 'Saídas', data: dados.map(d => d.despesas), backgroundColor: '#e74a3b', borderRadius: 4 }
                    ]
                },
                options: { maintainAspectRatio: false, responsive: true, scales: { y: { beginAtZero: true, grid: { borderDash: [2], drawBorder: false } }, x: { grid: { display: false } } }, plugins: { legend: { position: 'top' } } }
            });
        }
    }
};