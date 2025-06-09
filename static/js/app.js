/**
 * Motor Text-to-SQL - Frontend Aprimorado
 * Integra com backend Flask para consultas reais no banco de dados
 */

// Estado da Aplicação
let contadorConsultas = 0;
let tempoTotalExecucao = 0;
let consultasBemSucedidas = 0;

// Cache dos Elementos DOM
const elementos = {
    inputPergunta: null,
    botaoSubmit: null,
    secaoSql: null,
    displaySql: null,
    secaoResultados: null,
    displayResultados: null,
    secaoCarregamento: null,
    secaoErro: null,
    displayErro: null,
    painelStats: null,
    totalConsultas: null,
    ultimaExecucao: null,
    execucaoMedia: null,
    contadorResultados: null,
    tempoExecucao: null,
    botaoCopiarSql: null,
    containerToast: null,
    itensExemplo: null
};

/**
 * Inicializa a aplicação
 */
function inicializarApp() {
    // Faz cache dos elementos DOM
    cachearElementos();
    
    // Configura os ouvintes de eventos
    configurarEventListeners();
    
    // Foca no input
    elementos.inputPergunta.focus();
    
    // Mostra mensagem de boas-vindas
    setTimeout(() => {
        if (!localStorage.getItem('jaVisitou')) {
            mostrarToast('Bem-vindo! Experimente fazer uma pergunta sobre seu banco de dados.', 'info');
            localStorage.setItem('jaVisitou', 'true');
        }
    }, 1000);
    
    console.log('🚀 Motor Text-to-SQL inicializado com sucesso!');
}

/**
 * Faz cache dos elementos DOM para melhor performance
 */
function cachearElementos() {
    elementos.inputPergunta = document.getElementById('questionInput');
    elementos.botaoSubmit = document.getElementById('submitBtn');
    elementos.secaoSql = document.getElementById('sqlSection');
    elementos.displaySql = document.getElementById('sqlDisplay');
    elementos.secaoResultados = document.getElementById('resultsSection');
    elementos.displayResultados = document.getElementById('resultsDisplay');
    elementos.secaoCarregamento = document.getElementById('loadingSection');
    elementos.secaoErro = document.getElementById('errorSection');
    elementos.displayErro = document.getElementById('errorDisplay');
    elementos.painelStats = document.getElementById('statsPanel');
    elementos.totalConsultas = document.getElementById('totalQueries');
    elementos.ultimaExecucao = document.getElementById('lastExecution');
    elementos.execucaoMedia = document.getElementById('avgExecution');
    elementos.contadorResultados = document.getElementById('resultCount');
    elementos.tempoExecucao = document.getElementById('executionTime');
    elementos.botaoCopiarSql = document.getElementById('copySqlBtn');
    elementos.containerToast = document.getElementById('toastContainer');
    elementos.itensExemplo = document.querySelectorAll('.example-item');
}

/**
 * Configura todos os ouvintes de eventos
 */
function configurarEventListeners() {
    // Clique no botão submit
    elementos.botaoSubmit.addEventListener('click', executarConsulta);
    
    // Tecla Enter no campo de input
    elementos.inputPergunta.addEventListener('keydown', function(evento) {
        if (evento.key === 'Enter' && !evento.shiftKey) {
            evento.preventDefault();
            executarConsulta();
        }
    });
    
    // Clique nas perguntas de exemplo
    elementos.itensExemplo.forEach(item => {
        item.addEventListener('click', function() {
            definirExemplo(this.textContent.trim());
        });
    });
    
    // Botão copiar SQL
    elementos.botaoCopiarSql.addEventListener('click', copiarSqlParaClipboard);
    
    // Melhorias no campo de input
    elementos.inputPergunta.addEventListener('input', lidarComMudancaInput);
    elementos.inputPergunta.addEventListener('focus', lidarComFocoInput);
    elementos.inputPergunta.addEventListener('blur', lidarComBlurInput);
}

/**
 * Define pergunta de exemplo no campo de input
 * @param {string} textoExemplo - O texto da pergunta de exemplo
 */
function definirExemplo(textoExemplo) {
    elementos.inputPergunta.value = textoExemplo;
    elementos.inputPergunta.focus();
    
    // Adiciona feedback visual
    elementos.inputPergunta.style.borderColor = 'var(--primary)';
    setTimeout(() => {
        elementos.inputPergunta.style.borderColor = '';
    }, 1000);
}

/**
 * Lida com mudanças no campo de input
 */
function lidarComMudancaInput() {
    const temValor = elementos.inputPergunta.value.trim().length > 0;
    elementos.botaoSubmit.style.opacity = temValor ? '1' : '0.7';
}

/**
 * Lida com foco no campo de input
 */
function lidarComFocoInput() {
    elementos.inputPergunta.parentElement.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
}

/**
 * Lida com saída de foco do campo de input
 */
function lidarComBlurInput() {
    elementos.inputPergunta.parentElement.style.boxShadow = '';
}

/**
 * Executa a consulta SQL
 */
async function executarConsulta() {
    const pergunta = elementos.inputPergunta.value.trim();
    
    if (!pergunta) {
        mostrarToast('Digite uma pergunta sobre seu banco de dados.', 'warning');
        elementos.inputPergunta.focus();
        return;
    }
    
    // Valida comprimento da pergunta
    if (pergunta.length < 5) {
        mostrarToast('Pergunta muito curta. Seja mais específico.', 'warning');
        return;
    }
    
    if (pergunta.length > 1000) {
        mostrarToast('Pergunta muito longa. Mantenha abaixo de 1000 caracteres.', 'warning');
        return;
    }
    
    // Reseta estado da UI
    esconderTodasSecoes();
    mostrarEstadoCarregamento();
    definirBotaoCarregamento(true);
    
    const tempoInicio = Date.now();
    
    try {
        // Faz requisição à API do Flask
        const resposta = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: pergunta })
        });
        
        if (!resposta.ok) {
            throw new Error(`HTTP ${resposta.status}: ${resposta.statusText}`);
        }
        
        const dados = await resposta.json();
        const tempoExecucao = Date.now() - tempoInicio;
        
        // Esconde estado de carregamento
        esconderEstadoCarregamento();
        
        // Exibe consulta SQL
        exibirSqlGerada(dados.query);
        
        if (dados.success) {
            // Exibe resultados
            exibirResultadosConsulta(dados);
            
            // Atualiza estatísticas
            atualizarEstatisticas(tempoExecucao, true);
            
            // Mostra toast de sucesso
            const contadorResultados = dados.data ? dados.data.length : 0;
            mostrarToast(`Consulta executada com sucesso! Encontrados ${contadorResultados} resultado${contadorResultados !== 1 ? 's' : ''}.`, 'success');
            
        } else {
            // Exibe erro
            exibirErro(dados.error || 'Erro desconhecido');
            
            // Atualiza estatísticas
            atualizarEstatisticas(tempoExecucao, false);
            
            // Mostra toast de erro
            mostrarToast('Falha na execução da consulta. Verifique os detalhes do erro abaixo.', 'error');
        }
        
    } catch (erro) {
        console.error('Erro na execução da consulta:', erro);
        
        esconderEstadoCarregamento();
        exibirErro(`Erro de conexão: ${erro.message}`);
        atualizarEstatisticas(Date.now() - tempoInicio, false);
        mostrarToast('Falha ao conectar com o servidor. Tente novamente.', 'error');
        
    } finally {
        definirBotaoCarregamento(false);
    }
}

/**
 * Mostra estado de carregamento
 */
function mostrarEstadoCarregamento() {
    elementos.secaoCarregamento.classList.remove('hidden');
    elementos.secaoCarregamento.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/**
 * Esconde estado de carregamento
 */
function esconderEstadoCarregamento() {
    elementos.secaoCarregamento.classList.add('hidden');
}

/**
 * Define estado de carregamento do botão
 * @param {boolean} estaCarregando - Se o botão deve mostrar estado de carregamento
 */
function definirBotaoCarregamento(estaCarregando) {
    if (estaCarregando) {
        elementos.botaoSubmit.disabled = true;
        elementos.botaoSubmit.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i><span>Processando...</span>';
        elementos.inputPergunta.disabled = true;
    } else {
        elementos.botaoSubmit.disabled = false;
        elementos.botaoSubmit.innerHTML = '<i class="fas fa-play"></i><span>Executar</span>';
        elementos.inputPergunta.disabled = false;
    }
}

/**
 * Esconde todas as seções de resultado
 */
function esconderTodasSecoes() {
    elementos.secaoSql.classList.add('hidden');
    elementos.secaoResultados.classList.add('hidden');
    elementos.secaoErro.classList.add('hidden');
}

/**
 * Exibe a consulta SQL gerada
 * @param {string} sql - A consulta SQL gerada
 */
function exibirSqlGerada(sql) {
    elementos.displaySql.textContent = sql;
    elementos.secaoSql.classList.remove('hidden');
    
    // Rola para a seção SQL
    setTimeout(() => {
        elementos.secaoSql.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
}

/**
 * Exibe resultados da consulta
 * @param {Object} dados - Dados do resultado da consulta
 */
function exibirResultadosConsulta(dados) {
    const { columns, data: linhas } = dados;
    
    // Atualiza contador de resultados
    const contadorResultados = linhas ? linhas.length : 0;
    elementos.contadorResultados.textContent = `${contadorResultados} linha${contadorResultados !== 1 ? 's' : ''}`;
    
    if (!linhas || linhas.length === 0) {
        elementos.displayResultados.innerHTML = `
            <div class="no-results">
                <div class="no-results-icon">
                    <i class="fas fa-search"></i>
                </div>
                <div class="no-results-text">
                    <h3>Nenhum resultado encontrado</h3>
                    <p>Sua consulta foi executada com sucesso, mas não retornou dados.</p>
                </div>
            </div>
        `;
    } else {
        // Gera HTML da tabela
        let htmlTabela = '<table class="results-table">';
        
        // Cabeçalhos da tabela
        htmlTabela += '<thead><tr>';
        columns.forEach(coluna => {
            htmlTabela += `<th>${escaparHtml(coluna)}</th>`;
        });
        htmlTabela += '</tr></thead>';
        
        // Corpo da tabela
        htmlTabela += '<tbody>';
        linhas.forEach((linha, indice) => {
            htmlTabela += `<tr>`;
            columns.forEach(coluna => {
                const valor = linha[coluna];
                const valorExibicao = valor !== null && valor !== undefined 
                    ? escaparHtml(String(valor))
                    : '<span class="null-value">NULL</span>';
                htmlTabela += `<td>${valorExibicao}</td>`;
            });
            htmlTabela += '</tr>';
        });
        htmlTabela += '</tbody></table>';
        
        elementos.displayResultados.innerHTML = htmlTabela;
    }
    
    // Mostra seção de resultados
    elementos.secaoResultados.classList.remove('hidden');
    
    // Rola para os resultados
    setTimeout(() => {
        elementos.secaoResultados.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 200);
}

/**
 * Exibe mensagem de erro
 * @param {string} mensagemErro - A mensagem de erro para exibir
 */
function exibirErro(mensagemErro) {
    elementos.displayErro.textContent = mensagemErro;
    elementos.secaoErro.classList.remove('hidden');
    
    // Rola para o erro
    setTimeout(() => {
        elementos.secaoErro.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
}

/**
 * Atualiza estatísticas da aplicação
 * @param {number} tempoExecucao - Tempo de execução da consulta em milissegundos
 * @param {boolean} foiBemSucedida - Se a consulta foi bem-sucedida
 */
function atualizarEstatisticas(tempoExecucao, foiBemSucedida) {
    contadorConsultas++;
    elementos.totalConsultas.textContent = contadorConsultas;
    elementos.ultimaExecucao.textContent = `${tempoExecucao}ms`;
    
    if (foiBemSucedida) {
        consultasBemSucedidas++;
        tempoTotalExecucao += tempoExecucao;
        
        const tempoMedio = Math.round(tempoTotalExecucao / consultasBemSucedidas);
        elementos.execucaoMedia.textContent = `${tempoMedio}ms`;
    }
    
    // Atualiza tempo de execução no rodapé dos resultados
    elementos.tempoExecucao.textContent = `Tempo de execução: ${tempoExecucao}ms`;
    
    // Mostra painel de stats se esta for a primeira consulta
    if (contadorConsultas === 1) {
        elementos.painelStats.classList.remove('hidden');
        setTimeout(() => {
            elementos.painelStats.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
    }
}

/**
 * Copia SQL para a área de transferência
 */
async function copiarSqlParaClipboard() {
    try {
        const textoSql = elementos.displaySql.textContent;
        await navigator.clipboard.writeText(textoSql);
        
        // Feedback visual
        const textoOriginal = elementos.botaoCopiarSql.innerHTML;
        elementos.botaoCopiarSql.innerHTML = '<i class="fas fa-check"></i><span>Copiado!</span>';
        elementos.botaoCopiarSql.style.background = 'rgba(16, 185, 129, 0.2)';
        elementos.botaoCopiarSql.style.borderColor = 'var(--success)';
        elementos.botaoCopiarSql.style.color = 'var(--success)';
        
        setTimeout(() => {
            elementos.botaoCopiarSql.innerHTML = textoOriginal;
            elementos.botaoCopiarSql.style.background = '';
            elementos.botaoCopiarSql.style.borderColor = '';
            elementos.botaoCopiarSql.style.color = '';
        }, 2000);
        
        mostrarToast('Consulta SQL copiada para a área de transferência!', 'success');
        
    } catch (erro) {
        console.error('Falha ao copiar SQL:', erro);
        mostrarToast('Falha ao copiar SQL. Por favor, selecione e copie manualmente.', 'error');
    }
}

/**
 * Mostra notificação toast
 * @param {string} mensagem - A mensagem para mostrar
 * @param {string} tipo - Tipo do toast: success, error, warning, info
 */
function mostrarToast(mensagem, tipo = 'info') {
    const icones = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const cores = {
        success: 'var(--success)',
        error: 'var(--danger)',
        warning: 'var(--warning)',
        info: 'var(--info)'
    };
    
    // Cria elemento toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas ${icones[tipo]}" style="color: ${cores[tipo]}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-message">${escaparHtml(mensagem)}</div>
        </div>
        <button class="toast-close" aria-label="Fechar notificação">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Adiciona ao container
    elementos.containerToast.appendChild(toast);
    
    // Remove automaticamente após 3 segundos
    const remocaoAutomatica = setTimeout(() => {
        removerToast(toast);
    }, 3000);
    
    // Botão de fechar manual
    toast.querySelector('.toast-close').addEventListener('click', () => {
        clearTimeout(remocaoAutomatica);
        removerToast(toast);
    });
    
    // Limita número de toasts
    const toasts = elementos.containerToast.children;
    if (toasts.length > 5) {
        removerToast(toasts[0]);
    }
}

/**
 * Remove toast com animação
 * @param {HTMLElement} toast - Elemento toast para remover
 */
function removerToast(toast) {
    toast.style.animation = 'fadeOutRight 0.3s ease-out forwards';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

/**
 * Escapa HTML para prevenir XSS
 * @param {string} textoInseguro - String insegura
 * @returns {string} - String HTML segura
 */
function escaparHtml(textoInseguro) {
    return textoInseguro
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Função debounce para otimização de performance
 * @param {Function} func - Função para aplicar debounce
 * @param {number} espera - Tempo de espera em milissegundos
 * @returns {Function} - Função com debounce aplicado
 */
function debounce(func, espera) {
    let timeout;
    return function funcaoExecutada(...args) {
        const depois = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(depois, espera);
    };
}

// Inicializa aplicação quando DOM é carregado
document.addEventListener('DOMContentLoaded', inicializarApp);

// Adiciona alguns estilos CSS adicionais para estado de sem resultados
const estilosAdicionais = `
    .no-results {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem 1rem;
        text-align: center;
    }
    
    .no-results-icon {
        font-size: 3rem;
        color: var(--text-muted);
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    .no-results-text h3 {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }
    
    .no-results-text p {
        font-size: 0.875rem;
        color: var(--text-muted);
    }
    
    .null-value {
        color: var(--text-muted);
        font-style: italic;
        opacity: 0.7;
    }
`;

// Injeta estilos adicionais
const folhaEstilo = document.createElement('style');
folhaEstilo.textContent = estilosAdicionais;
document.head.appendChild(folhaEstilo);