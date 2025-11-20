
const API_URL = 'http://localhost:8000';

// Cria instância do Axios com configurações padrão
const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' }
});

// Middlewares do Frontend

// 1. Request Interceptor: Injeta o Token em TODAS as requisições
api.interceptors.request.use(config => {
    const token = localStorage.getItem('token_fin');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// 2. Response Interceptor: Gerencia Token Expirado (401)
api.interceptors.response.use(
    response => response,
    error => {
        // força o logout
        if (error.response && error.response.status === 401) {
            console.warn("Token expirado ou inválido. Redirecionando...");
            localStorage.removeItem('token_fin');
            window.location.reload(); 
        }
        return Promise.reject(error);
    }
);

// --- SERVIÇOS EXPORTADOS ---

export const authService = {
    login: async (username, password) => {
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        
        // Sobrescrevemos o header para esta chamada específica
        const { data } = await api.post('/auth/login', params, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });
        return data;
    }
};

export const dashboardService = {
    // Busca todos os dados do Dashboard em paralelo (Performance)
    carregarTudo: async () => {
        const [resumo, categorias, fluxo, ultimos, ranking] = await Promise.all([
            api.get('/dashboard/resumo'),        // Cards do topo
            api.get('/dashboard/por-categoria'), // Gráfico Pizza
            api.get('/dashboard/fluxo-caixa'),   // Gráfico Barras
            api.get('/titulos?limit=10'),        // Tabela
            api.get('/dashboard/ranking')        // Devedores/Credores
        ]);
        
        return {
            resumo: resumo.data,
            categorias: categorias.data,
            fluxo: fluxo.data,
            titulos: ultimos.data,
            ranking: ranking.data
        };
    },

    // Busca lista de categorias para preencher o <select> do Modal
    listarCategorias: async () => {
        const { data } = await api.get('/categorias');
        return data;
    },

    // Envia um novo lançamento para o Backend
    salvarTitulo: async (payload) => {
        const { data } = await api.post('/titulos', payload);
        return data;
    },

    // Busca contatos por nome (Autocomplete)
    buscarContato: async (termo) => {
        const { data } = await api.get(`/dashboard/busca-contato?q=${termo}`);
        return data;
    }
};