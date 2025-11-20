import { authService, dashboardService } from './api.js';
import { ui } from './ui.js';

// ESTADO GLOBAL
const state = {
    token: localStorage.getItem('token_fin'),
    searchTimeout: null // Controle do debounce da busca
};


// INICIALIZAÇÃO
document.addEventListener('DOMContentLoaded', () => {
    // 1. Configura Data no Topo
    const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('dataAtual').innerText = new Date().toLocaleDateString('pt-BR', dateOptions);

    // 2. Verifica Login
    if (state.token) {
        initDashboard();
    } else {
        ui.toggleScreens(false);
    }

    setupBuscaInteligente();
});

// LÓGICA DE BUSCA (AUTOCOMPLETE)
function setupBuscaInteligente() {
    const inputBusca = document.getElementById('inputBuscaRanking');
    
    inputBusca.addEventListener('input', (e) => {
        const termo = e.target.value.trim();

        // Limpa o timer anterior/usuário ainda está digitando
        clearTimeout(state.searchTimeout);

        // Se limpou o campo volta ao ranking normal
        if (termo.length === 0) {
            ui.toggleModoBusca(false);
            return;
        }

        // Debounce: Espera 300ms após parar de digitar para chamar a API
        state.searchTimeout = setTimeout(async () => {
            // Só busca se tiver 2 ou mais caracteres
            if (termo.length >= 2) {
                try {
                    // Chama a API
                    const resultados = await dashboardService.buscarContato(termo);
                    
                    // Atualiza a UI
                    ui.toggleModoBusca(true); // Esconde Ranking, mostra Busca
                    ui.renderResultadosBusca(resultados);
                    
                } catch (error) {
                    console.error("Erro na busca:", error);
                }
            }
        }, 300);
    });
}

// AUTENTICAÇÃO
window.fazerLogin = async () => {
    const email = document.getElementById('email').value;
    const senha = document.getElementById('senha').value;
    const btn = document.querySelector('#loginScreen button');

    try {
        btn.disabled = true; 
        btn.innerText = "Carregando...";
        ui.showLoginError(false);

        const data = await authService.login(email, senha);
        
        localStorage.setItem('token_fin', data.access_token);
        state.token = data.access_token;
        
        initDashboard();

    } catch (error) {
        console.error("Falha no login:", error);
        ui.showLoginError(true);
    } finally {
        btn.disabled = false; 
        btn.innerText = "Entrar";
    }
};

window.logout = () => {
    localStorage.removeItem('token_fin');
    window.location.reload();
};

// DASHBOARD
async function initDashboard() {
    ui.toggleScreens(true);
    
    try {
        // Carrega Dados + Lista de Categorias
        const [dados, categoriasLista] = await Promise.all([
            dashboardService.carregarTudo(),
            dashboardService.listarCategorias()
        ]);
        
        // Renderiza Visual
        ui.renderCards(dados.resumo);
        ui.renderTabela(dados.titulos);
        ui.renderRankings(dados.ranking);
        ui.charts.renderPizza(dados.categorias.slice(0, 5));
        ui.charts.renderBarras(dados.fluxo);
        
        // Popula o Select de Categorias do Modal
        const selectCat = document.getElementById('inpCat');
        selectCat.innerHTML = '<option value="" selected disabled>Selecione...</option>';
        
        categoriasLista.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat.id;
            opt.textContent = cat.nome;
            selectCat.appendChild(opt);
        });
        
    } catch (error) {
        console.error("Erro fatal ao carregar dashboard", error);
    }
}

window.salvarTitulo = async () => {
    const btn = document.querySelector('#modalNovo .btn-primary');
    const originalText = btn.innerText;
    
    try {
        btn.disabled = true; 
        btn.innerText = "Salvando";

        const payload = {
            descricao: document.getElementById('inpDesc').value,
            valor: parseFloat(document.getElementById('inpValor').value),
            data_vencimento: document.getElementById('inpData').value,
            tipo: document.getElementById('inpTipo').value,
            categoria_id: parseInt(document.getElementById('inpCat').value),
            // Fixos para o case
            contato_id: 1,        
            conta_bancaria_id: 1,
            parcelado: false,
            total_parcelas: 1
        };

        // Validação Simples
        if (!payload.descricao || isNaN(payload.valor) || !payload.data_vencimento || isNaN(payload.categoria_id)) {
            alert("Preencha todos os campos corretamente.");
            return;
        }

        await dashboardService.salvarTitulo(payload);
        
        alert("Salvo");
        
        const modalEl = document.getElementById('modalNovo');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        
        document.getElementById('formNovoTitulo').reset();
        
        initDashboard();

    } catch (error) {
        console.error(error);
        alert("Erro ao salvar. Verifique os dados.");
    } finally {
        btn.disabled = false; 
        btn.innerText = originalText;
    }
};