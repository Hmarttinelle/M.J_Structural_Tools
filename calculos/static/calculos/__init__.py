/* calculos/static/calculos/style.css */
:root {
    --primary-color: #0d6efd;
    --primary-color-light: #e7f0ff;
    --secondary-color: #6c757d;
    --light-gray: #f8f9fa;
    --medium-gray: #dee2e6;
    --dark-gray: #212529;
    --success-bg: #d1e7dd;
    --error-bg: #f8d7da;
    --success-text: #0f5132;
    --error-text: #842029;
    --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    --border-radius: 6px;
    --box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

html {
    height: 100%;
    min-height: 100vh;
}

body {
    font-family: var(--font-family);
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: var(--light-gray);
    color: var(--dark-gray);
    min-height: 100vh;
    /* CORREÇÃO PARA A IMAGEM DE FUNDO */
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-repeat: no-repeat;
}

.container {
    max-width: 1200px;
    margin: 40px auto;
    padding: 30px 40px;
    background-color: rgba(255, 255, 255, 0.95); /* Ligeira transparência para o fundo */
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    flex-grow: 1;
}

h1 {
    color: var(--primary-color);
    text-align: center;
    margin-bottom: 10px;
}

h3, h4 {
    color: var(--primary-color);
}

.container > p {
    text-align: center;
    font-size: 1.1rem;
    color: #6c757d;
    margin-bottom: 40px;
}

/* --- Menu Principal --- */
.header-logo {
    text-align: center;
    margin-bottom: 20px;
}
.nav-card {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
    padding: 25px;
    margin: 15px 0;
    background-image: linear-gradient(45deg, var(--primary-color), #0a58ca);
    color: white;
    text-align: center;
    border-radius: var(--border-radius);
    text-decoration: none;
    font-size: 1.4rem;
    font-weight: 500;
    transition: transform 0.3s, box-shadow 0.2s;
}
.nav-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(13, 110, 253, 0.2);
}
footer {
    text-align: center;
    padding: 20px;
    color: #888;
}

/* --- Páginas de Cálculo --- */
.back-link { 
    display: inline-block; 
    margin-bottom: 25px; 
    color: var(--primary-color); 
    text-decoration: none; 
    font-weight: bold;
}
.back-link:hover { text-decoration: underline; }

form {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 20px;
    align-items: end;
}
.form-section-title {
    grid-column: 1 / -1;
    margin-top: 20px; margin-bottom: 0;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--primary-color);
    font-size: 1.2rem;
}
.form-group label { margin-bottom: 8px; font-weight: 500; color: #495057; }
.form-group input, .form-group select {
    box-sizing: border-box;
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--medium-gray);
    border-radius: var(--border-radius);
    font-size: 1rem;
    height: 42px;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.form-group input:focus, .form-group select:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px var(--primary-color-light);
}

/* --- Botões --- */
.form-actions {
    grid-column: 1 / -1;
    display: flex;
    gap: 15px;
    margin-top: 20px;
    flex-wrap: wrap;
}
.btn-principal, .btn-secundario {
    padding: 12px 25px;
    border: none;
    border-radius: var(--border-radius);
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
    text-decoration: none;
    text-align: center;
    transition: all 0.2s ease;
}
.btn-principal {
    background-color: var(--primary-color);
    color: white;
    flex-grow: 2;
}
.btn-principal:hover { background-color: #0a58ca; }

.btn-secundario {
    background-color: #f8f9fa;
    color: var(--dark-gray);
    border: 1px solid var(--medium-gray);
    flex-grow: 1;
}
.btn-secundario:hover { background-color: #e2e6ea; }

/* --- Resultados --- */
.resultado {
    margin-top: 40px;
    padding: 20px;
    border-radius: var(--border-radius);
    border-left: 5px solid;
}
.sucesso { background-color: var(--success-bg); border-color: var(--success-text); color: var(--success-text); }
.erro { background-color: var(--error-bg); border-color: var(--error-text); color: var(--error-text); }

.resultado-detalhado {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 30px;
    margin-top: 30px;
    align-items: flex-start;
}
.desenho-wrapper {
    border: 1px solid var(--medium-gray);
    padding: 20px;
    border-radius: var(--border-radius);
    background-color: #fff;
}
.passo-a-passo {
    background-color: #fdfdfd;
    border: 1px solid var(--medium-gray);
    border-radius: var(--border-radius);
    padding: 20px;
}
.passo-a-passo ul {
    list-style: none;
    padding-left: 0;
}
.passo-a-passo li {
    padding: 15px 0;
    border-bottom: 1px solid #eee;
}
.passo-a-passo li:last-child {
    border-bottom: none;
}

/* --- Tabela de Histórico --- */
.table-container table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    font-size: 0.95rem;
}
.table-container th, .table-container td {
    border: 1px solid var(--medium-gray);
    padding: 12px 15px;
    text-align: left;
    vertical-align: middle;
}
.table-container thead th {
    background-color: var(--primary-color-light);
    color: var(--primary-color);
    font-weight: 600;
}
.table-container tbody tr:nth-child(even) {
    background-color: var(--light-gray);
}
.table-container td form {
    display: inline-block;
    margin: 0;
}
.table-container .btn-secundario {
    padding: 8px 12px;
    font-size: 0.9rem;
}

/* --- Página de Configuração --- */
.config-form { display: flex; flex-direction: column; gap: 30px; }
.form-section { border: 1px solid var(--medium-gray); border-radius: var(--border-radius); padding: 20px 25px; }
.form-section legend { font-weight: bold; font-size: 1.2rem; color: var(--primary-color); padding: 0 10px; }
.theme-selector { display: flex; gap: 15px; }
.theme-option { display: flex; align-items: center; }
.theme-option input[type="radio"] { opacity: 0; position: fixed; width: 0; }
.theme-option label { display: flex; align-items: center; gap: 8px; padding: 10px 20px; background-color: var(--light-gray); border: 1px solid var(--medium-gray); border-radius: var(--border-radius); cursor: pointer; transition: all 0.2s ease; }
.theme-option input[type="radio"]:checked + label { background-color: var(--primary-color); color: white; border-color: var(--primary-color); }
.theme-option label:hover { border-color: var(--primary-color); }
.color-picker-wrapper { position: relative; width: 150px; }
.color-picker-wrapper input[type="color"] { width: 100%; height: 42px; padding: 0; border: none; cursor: pointer; background: none; }
.color-picker-wrapper #color-preview { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; border: 1px solid var(--medium-gray); border-radius: var(--border-radius); pointer-events: none; z-index: -1; }
.image-preview-container { margin-top: 15px; }
.image-preview { max-width: 100%; height: auto; max-height: 200px; border-radius: var(--border-radius); border: 1px solid var(--medium-gray); margin-top: 5px; }
.current-image-info { font-size: 0.9rem; color: #6c757d; margin-bottom: 5px; }
.form-error { color: var(--error-text); font-size: 0.9rem; margin-top: 5px; }

/* --- Formulário de Pilares --- */
.form-group-full { grid-column: 1 / -1; }
.ligacao-wrapper { display: flex; flex-wrap: wrap; gap: 30px; margin-top: 10px; }
.ligacao-selector { display: flex; align-items: center; gap: 15px; }
.ligacao-selector > span { font-weight: 500; color: #495057; }
.ligacao-options { display: flex; }
.ligacao-options label { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 80px; height: 60px; border: 1px solid var(--medium-gray); cursor: pointer; transition: all 0.2s ease; background-color: var(--light-gray); margin-right: -1px; position: relative; }
.ligacao-options label:first-of-type { border-top-left-radius: var(--border-radius); border-bottom-left-radius: var(--border-radius); }
.ligacao-options label:last-of-type { border-top-right-radius: var(--border-radius); border-bottom-right-radius: var(--border-radius); }
.ligacao-options .label-text { font-size: 0.75rem; color: #6c757d; }
.ligacao-options input[type="radio"] { position: absolute; opacity: 0; }
.ligacao-options label:hover { background-color: #e9ecef; z-index: 1; }
.ligacao-options label.active { border-color: var(--primary-color); box-shadow: 0 0 0 2px var(--primary-color-light); z-index: 2; }
.ligacao-options label.active .label-text { color: var(--primary-color); font-weight: bold; }
.ligacao-options img {
    width: 28px;
    height: 28px;
    display: block;
    opacity: 0.6;
    transition: all 0.2s ease;
}
.ligacao-options label.active img {
    opacity: 1;
}

/* TEMA ESCURO     */
body.dark-theme {
    --primary-color-light: #424242;
    --secondary-color: #BDBDBD;
    --light-gray: #212121;
    --medium-gray: #616161;
    --dark-gray: #f5f5f5;
    --success-bg: #1B5E20;
    --error-bg: #B71C1C;
    --success-text: #E8F5E9;
    --error-text: #FFEBEE;
    --box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}

body.dark-theme .container {
    background-color: rgba(48, 48, 48, 0.95); /* #303030 com transparência */
    color: var(--dark-gray);
}
body.dark-theme p, body.dark-theme .container > p {
    color: var(--secondary-color);
}
body.dark-theme .form-group label, body.dark-theme .ligacao-selector > span {
    color: #E0E0E0;
}
body.dark-theme .form-group input, body.dark-theme .form-group select {
    background-color: #424242;
    color: #fff;
    border-color: #757575;
}
body.dark-theme .btn-secundario {
    background-color: #424242;
    color: var(--dark-gray);
    border-color: #757575;
}
body.dark-theme .btn-secundario:hover { background-color: #515151; }
body.dark-theme .passo-a-passo, body.dark-theme .desenho-wrapper {
    background-color: #2a2a2a;
}

/* ESTILOS PARA O SPINNER DE CARREGAMENTO      */
.spinner-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    display: none; /* Escondido por defeito */
    justify-content: center;
    align-items: center;
}

.spinner {
    border: 8px solid #f3f3f3; /* Cinza claro */
    border-top: 8px solid var(--primary-color); /* Cor primária */
    border-radius: 50%;
    width: 60px;
    height: 60px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}


/* PÁGINA DE CONFIGURAÇÃO  */
.config-form {
    display: flex;
    flex-direction: column;
    gap: 30px;
}

.form-section {
    border: 1px solid var(--medium-gray);
    border-radius: var(--border-radius);
    padding: 20px 25px;
}

.form-section legend {
    font-weight: bold;
    font-size: 1.2rem;
    color: var(--primary-color);
    padding: 0 10px;
}

/* --- Seletor de Tema --- */
.theme-selector {
    display: flex;
    gap: 15px;
}

.theme-option {
    display: flex;
    align-items: center;
}

/* Esconde o botão de rádio original */
.theme-option input[type="radio"] {
    opacity: 0;
    position: fixed;
    width: 0;
}

.theme-option label {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    background-color: var(--light-gray);
    border: 1px solid var(--medium-gray);
    border-radius: var(--border-radius);
    cursor: pointer;
    transition: all 0.2s ease;
}

.theme-option input[type="radio"]:checked + label {
    background-color: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.theme-option label:hover {
    border-color: var(--primary-color);
}

body.dark-theme .theme-option label {
    background-color: #555;
    border-color: #777;
}

body.dark-theme .theme-option input[type="radio"]:checked + label {
    background-color: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}


/* --- Seletor de Cor --- */
.color-picker-wrapper {
    position: relative;
    width: 150px;
}

.color-picker-wrapper input[type="color"] {
    width: 100%;
    height: 42px;
    padding: 0;
    border: none;
    cursor: pointer;
    background: none;
}

/* Caixa de pré-visualização da cor */
.color-picker-wrapper #color-preview {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border: 1px solid var(--medium-gray);
    border-radius: var(--border-radius);
    pointer-events: none; /* Permite clicar através dela */
    z-index: -1;
}

/* --- Info da Imagem Atual --- */
.current-image-info {
    font-size: 0.9rem;
    margin-top: 10px;
    color: #6c757d;
}
.current-image-info a {
    color: var(--primary-color);
}
.form-error {
    color: var(--error-text); 
    font-size: 0.9rem; 
    margin-top: 5px;
}

/* --- Pré-visualização da Imagem de Fundo --- */
.image-preview-container {
    margin-top: 15px;
}

.image-preview {
    max-width: 100%;
    height: auto;
    max-height: 200px; /* Limita a altura da pré-visualização */
    border-radius: var(--border-radius);
    border: 1px solid var(--medium-gray);
    margin-top: 5px;
}

.current-image-info {
    font-size: 0.9rem;
    color: #6c757d;
    margin-bottom: 5px;
}


/* FORMULÁRIO DE PILARES - SELETORES VISUAIS (V2)*/

.form-group-full {
    grid-column: 1 / -1; /* Ocupa a largura toda */
}

.ligacao-wrapper {
    display: flex;
    flex-wrap: wrap; 
    gap: 30px;
    margin-top: 10px;
}

.ligacao-selector {
    display: flex;
    align-items: center;
    gap: 15px;
}

.ligacao-selector > span {
    font-weight: 500;
    color: #495057;
}

.ligacao-options {
    display: flex;
}

.ligacao-options label {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 65px;
    height: 55px;
    border: 1px solid var(--medium-gray);
    cursor: pointer;
    transition: all 0.2s ease;
    background-color: var(--light-gray);
    margin-right: -1px; /* Faz as bordas sobreporem-se */
    position: relative;
}

.ligacao-options label:first-of-type {
    border-top-left-radius: var(--border-radius);
    border-bottom-left-radius: var(--border-radius);
}
.ligacao-options label:last-of-type {
    border-top-right-radius: var(--border-radius);
    border-bottom-right-radius: var(--border-radius);
}

.ligacao-options img {
    width: 28px;
    height: 28px;
    display: block;
    opacity: 0.6;
    color: var(--dark-gray); /* Cor do ícone */
    transition: all 0.2s ease;
}

.ligacao-options .label-text {
    font-size: 0.75rem;
    color: #6c757d;
}

.ligacao-options input[type="radio"] {
    position: absolute;
    opacity: 0;
}

.ligacao-options label:hover {
    background-color: #e9ecef;
    z-index: 1;
}

.ligacao-options input[type="radio"]:checked + .label-text + img {
    opacity: 1;
    color: var(--primary-color);
}

.ligacao-options input[type="radio"]:checked + .label-text {
    color: var(--primary-color);
    font-weight: bold;
}

.ligacao-options input[type="radio"]:checked ~ .border-highlight {
    opacity: 1;
}

.ligacao-options label.active {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 2px var(--primary-color-light);
    z-index: 2;
}

/* Estilos para o tema escuro */
body.dark-theme .ligacao-selector > span { color: #E0E0E0; }
body.dark-theme .container {
    border-color: #424242;
}
body.dark-theme .passo-a-passo li { border-bottom-color: #424242; }

/* Tabela modo escuro */
body.dark-theme .table-container th, body.dark-theme .table-container td {
    border-color: #424242;
}
body.dark-theme .table-container thead th {
    background-color: #303030;
    color: var(--primary-color);
}
body.dark-theme .table-container tbody tr:nth-child(even) {
    background-color: #2a2a2a;
}
body.dark-theme .back-link, body.dark-theme .current-image-info a {
    color: var(--primary-color);
}

/* Configuração modo escuro */
body.dark-theme .theme-option label {
    background-color: #424242;
    border-color: #757575;
}
body.dark-theme .theme-option input[type="radio"]:checked + label {
    color: white; /* Garante que o texto fica branco */
}
body.dark-theme .color-picker-wrapper #color-preview {
    border-color: #757575;
}

/* Pilares modo escuro */
body.dark-theme .ligacao-options label {
    background-color: #424242;
    border-color: #777;
}
body.dark-theme .ligacao-options label:hover { background-color: #515151; }
body.dark-theme .ligacao-options .label-text { color: #bdbdbd; }
body.dark-theme .ligacao-options img { color: #f5f5f5; }
body.dark-theme .ligacao-options input[type="radio"]:checked + .label-text + img { color: var(--primary-color); }
body.dark-theme .ligacao-options input[type="radio"]:checked + .label-text { color: var(--primary-color); }
body.dark-theme .ligacao-options label.active { border-color: var(--primary-color); }

/* ========================================================================== */
/* MENU PRINCIPAL V1.2                                                       */
/* ========================================================================== */

body.home-page {
    overflow-x: hidden;
    background-color: #eaf0f6;
}

body.home-page .home-container {
    max-width: none;
    width: 100%;
    min-height: 100vh;
    margin: 0;
    padding: 0;
    border-radius: 0;
    box-shadow: none;
    background: transparent;
}

.home-app-shell {
    --home-navy: #061c34;
    --home-navy-2: #0a2b4d;
    --home-blue: #0b63d8;
    --home-blue-2: #0755c7;
    --home-green: #09b878;
    --home-green-2: #069c66;
    --home-text: #0b2345;
    --home-muted: #526987;
    --home-border: rgba(117, 141, 168, 0.23);
    min-height: 100vh;
    display: grid;
    grid-template-columns: 270px minmax(0, 1fr);
    color: var(--home-text);
}

.home-sidebar {
    position: sticky;
    top: 0;
    align-self: start;
    min-height: 100vh;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, #061c34 0%, #06223e 54%, #04172b 100%);
    color: #fff;
    box-shadow: 8px 0 30px rgba(6, 28, 52, 0.18);
    z-index: 5;
    overflow: hidden;
}

.home-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 100px;
    padding: 0 24px;
    border-bottom: 1px solid rgba(255,255,255,.08);
}

.home-brand-mark {
    width: 42px;
    height: 42px;
    display: grid;
    place-items: center;
    font-size: 2rem;
    color: #fff;
}

.home-brand strong {
    display: block;
    font-size: 1.04rem;
    line-height: 1.2;
    letter-spacing: .01em;
}

.home-brand span {
    display: block;
    margin-top: 5px;
    color: #c6d8eb;
    font-size: .78rem;
}

.home-nav {
    padding: 18px 10px 0;
}

.home-nav-item {
    position: relative;
    display: flex;
    align-items: center;
    gap: 16px;
    min-height: 50px;
    margin: 3px 0;
    padding: 0 16px;
    color: #e9f1fb;
    border-radius: 8px;
    text-decoration: none;
    font-size: .94rem;
    transition: background .18s ease, color .18s ease, transform .18s ease;
}

.home-nav-item > i,
.home-nav-svg {
    width: 27px;
    flex: 0 0 27px;
    text-align: center;
    font-size: 1.25rem;
    color: #e6f0fb;
}

.home-nav-svg svg {
    width: 25px;
    height: 25px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.8;
    stroke-linecap: round;
    stroke-linejoin: round;
}

.home-nav-item:hover {
    color: #fff;
    background: rgba(255,255,255,.08);
    transform: translateX(2px);
}

.home-nav-item.active {
    background: linear-gradient(90deg, #0e76e8, #0b5ed2);
    color: #fff;
    box-shadow: 0 10px 25px rgba(4, 96, 211, .26);
}

.home-nav-sapata-label {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.home-nav-sapata-label small {
    color: #ffbd34;
    font-size: .71rem;
    line-height: 1;
}

.home-nav-separator {
    height: 1px;
    margin: 17px 16px 13px;
    background: rgba(255,255,255,.16);
}

.home-sidebar-footer {
    position: relative;
    margin-top: auto;
    padding: 0 24px 20px;
    text-align: center;
    color: #c2d2e3;
    font-size: .74rem;
    line-height: 1.5;
}

.home-wireframe {
    position: relative;
    height: 210px;
    margin: 2px -24px 12px;
    opacity: .22;
}

.home-wireframe svg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    fill: none;
    stroke: #4ba4ff;
    stroke-width: 1;
}

.home-sidebar-rule {
    height: 1px;
    margin: 16px 0;
    background: rgba(255,255,255,.18);
}

.home-sidebar-course {
    color: #dbe7f4;
}

.home-main {
    min-width: 0;
    background: rgba(237, 244, 251, .78);
    backdrop-filter: blur(2px);
}

.home-topbar {
    position: sticky;
    top: 0;
    z-index: 4;
    min-height: 80px;
    padding: 0 34px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    background: rgba(255,255,255,.94);
    border-bottom: 1px solid rgba(91, 122, 154, .15);
    box-shadow: 0 4px 18px rgba(13, 45, 78, .06);
    backdrop-filter: blur(12px);
}

.home-topbar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
}

.home-topbar-logo {
    width: 44px;
    height: 44px;
    display: grid;
    place-items: center;
    border-radius: 10px;
    background: linear-gradient(145deg, #0f76dc, #0a4fa5);
    color: #fff;
    box-shadow: 0 8px 18px rgba(11,99,216,.22);
    font-size: 1.35rem;
}

.home-topbar-brand strong {
    display: block;
    font-size: 1.03rem;
    color: #0c2344;
    line-height: 1.2;
}

.home-topbar-brand span:not(.home-topbar-logo) {
    display: block;
    margin-top: 3px;
    color: #446589;
    font-size: .82rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.home-topbar-actions {
    display: flex;
    align-items: center;
    gap: 17px;
    white-space: nowrap;
}

.home-version {
    color: #2a5181;
    font-size: .83rem;
    padding-right: 17px;
    border-right: 1px solid #d4dee8;
}

.home-icon-link {
    width: 36px;
    height: 36px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    color: #315b88;
    text-decoration: none;
    font-size: 1.15rem;
    transition: background .18s ease, color .18s ease;
}

.home-icon-link:hover {
    background: #edf5ff;
    color: #0b63d8;
}

.home-profile {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #10284a;
    font-size: .86rem;
    font-weight: 600;
}

.home-avatar {
    width: 38px;
    height: 38px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    color: #fff;
    background: linear-gradient(135deg, #168fd3, #0870b7);
    box-shadow: 0 6px 14px rgba(10,110,181,.2);
}

.home-content {
    position: relative;
    min-height: calc(100vh - 80px);
    padding: 0 34px 22px;
}

.home-content::before {
    content: "";
    position: absolute;
    z-index: 0;
    inset: 0 0 auto;
    height: 390px;
    background: linear-gradient(180deg, rgba(255,255,255,.20) 0%, rgba(239,246,252,.26) 65%, rgba(239,246,252,.38) 100%);
    pointer-events: none;
}

.home-hero,
.home-modules,
.home-info-strip,
.home-footer {
    position: relative;
    z-index: 1;
}

.home-hero {
    max-width: 1120px;
    margin: 0 auto;
    padding: 38px 20px 26px;
    text-align: center;
}

.home-hero h1 {
    margin: 0;
    color: #092550;
    font-size: clamp(2.4rem, 4vw, 4.3rem);
    line-height: 1.05;
    font-weight: 760;
    letter-spacing: .01em;
    text-shadow: 0 2px 20px rgba(255,255,255,.85);
}

.home-hero h2 {
    margin: 12px 0 0;
    color: #375a82;
    font-size: clamp(1.15rem, 2vw, 1.72rem);
    font-weight: 500;
    line-height: 1.35;
}

.home-hero-divider {
    display: block;
    width: 54px;
    height: 3px;
    margin: 20px auto 16px;
    border-radius: 3px;
    background: #1678e5;
}

.home-hero p {
    max-width: 730px;
    margin: 0 auto;
    color: #375a82;
    font-size: 1rem;
    line-height: 1.5;
}

.home-modules {
    max-width: 1180px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 22px;
}

.home-module-card {
    position: relative;
    min-width: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    background: rgba(255,255,255,.97);
    border: 1px solid rgba(255,255,255,.9);
    border-radius: 14px;
    box-shadow: 0 16px 34px rgba(26, 55, 83, .13);
    transition: transform .22s ease, box-shadow .22s ease;
}

.home-module-card:not(.is-unavailable):hover {
    transform: translateY(-5px);
    box-shadow: 0 22px 44px rgba(26, 55, 83, .18);
}

.home-module-visual {
    height: 175px;
    overflow: hidden;
    background: #eef5fa;
    border-bottom: 1px solid #e0e7ee;
}

.structural-illustration {
    width: 100%;
    height: 100%;
    display: block;
}

.home-module-footing .home-module-visual {
    filter: grayscale(1);
    opacity: .72;
}

.home-module-icon {
    position: absolute;
    top: 142px;
    left: 25px;
    width: 62px;
    height: 62px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    border: 4px solid #fff;
    color: #fff;
    box-shadow: 0 8px 20px rgba(23, 48, 73, .22);
}

.home-module-icon svg {
    width: 29px;
    height: 29px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.8;
    stroke-linecap: round;
    stroke-linejoin: round;
}

.home-module-icon-green { background: linear-gradient(145deg, #13c58a, #079f69); }
.home-module-icon-blue { background: linear-gradient(145deg, #237ee9, #085ecf); }
.home-module-icon-muted { background: linear-gradient(145deg, #b3b8bd, #8d9398); }

.home-module-body {
    flex: 1;
    padding: 38px 24px 20px;
    display: flex;
    flex-direction: column;
}

.home-module-body h3 {
    margin: 0;
    color: #0d2344;
    font-size: 1.45rem;
    line-height: 1.15;
    font-weight: 730;
}

.home-module-title-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

.home-status-badge {
    display: inline-flex;
    align-items: center;
    min-height: 25px;
    padding: 0 10px;
    border-radius: 999px;
    color: #9c5a00;
    background: #fff0d8;
    border: 1px solid #ffe0ad;
    font-size: .72rem;
    font-weight: 600;
}

.home-module-body p {
    flex: 1;
    margin: 11px 0 19px;
    color: #3c5b80;
    font-size: .91rem;
    line-height: 1.52;
}

.home-module-action {
    min-height: 48px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 11px;
    border-radius: 7px;
    color: #fff;
    text-decoration: none;
    font-size: .9rem;
    font-weight: 650;
    transition: transform .16s ease, box-shadow .16s ease, filter .16s ease;
}

.home-module-action:hover {
    transform: translateY(-1px);
    filter: brightness(1.03);
}

.action-green {
    background: linear-gradient(90deg, #0abc81, #079d68);
    box-shadow: 0 8px 16px rgba(9, 184, 120, .18);
}

.action-blue {
    background: linear-gradient(90deg, #0f73e5, #0757c8);
    box-shadow: 0 8px 16px rgba(11, 99, 216, .18);
}

.action-disabled {
    color: #77899c;
    background: #e7ebef;
    box-shadow: none;
}

.action-disabled:hover {
    color: #5a6e82;
    background: #dde3e8;
    filter: none;
}

.home-info-strip {
    max-width: 1180px;
    margin: 24px auto 0;
    padding: 20px 24px;
    display: grid;
    grid-template-columns: .85fr 1fr 1.18fr 1.12fr;
    gap: 0;
    background: rgba(255,255,255,.93);
    border: 1px solid rgba(255,255,255,.9);
    border-radius: 14px;
    box-shadow: 0 12px 28px rgba(26, 55, 83, .08);
    backdrop-filter: blur(8px);
}

.home-info-item {
    display: flex;
    gap: 15px;
    min-width: 0;
    padding: 0 20px;
    border-right: 1px solid #dce5ed;
}

.home-info-item:first-child { padding-left: 0; }
.home-info-item:last-child { border-right: 0; padding-right: 0; }

.home-info-icon {
    flex: 0 0 auto;
    color: #315e90;
    font-size: 1.75rem;
    line-height: 1;
    padding-top: 3px;
}

.home-info-item h4 {
    margin: 0 0 6px;
    color: #18365d;
    font-size: .83rem;
    font-weight: 720;
}

.home-info-item p {
    margin: 0;
    color: #486789;
    font-size: .76rem;
    line-height: 1.52;
}

.home-footer {
    max-width: 1180px;
    margin: 13px auto 0;
    display: flex;
    justify-content: space-between;
    gap: 20px;
    color: #69809b;
    font-size: .71rem;
}

/* Dark mode do menu principal */
body.dark-theme.home-page .home-main {
    background: rgba(20, 30, 43, .88);
}

body.dark-theme.home-page .home-topbar {
    background: rgba(27, 39, 54, .96);
    border-bottom-color: rgba(255,255,255,.08);
}

body.dark-theme.home-page .home-topbar-brand strong,
body.dark-theme.home-page .home-profile { color: #eef5fb; }
body.dark-theme.home-page .home-topbar-brand span:not(.home-topbar-logo),
body.dark-theme.home-page .home-version { color: #a9bfd5; }
body.dark-theme.home-page .home-version { border-right-color: #405064; }
body.dark-theme.home-page .home-icon-link { color: #b5c9dd; }
body.dark-theme.home-page .home-content::before {
    background: linear-gradient(180deg, rgba(14,23,34,.68), rgba(20,30,43,.92));
}
body.dark-theme.home-page .home-hero h1 { color: #f0f6fb; text-shadow: none; }
body.dark-theme.home-page .home-hero h2,
body.dark-theme.home-page .home-hero p { color: #bdd0e2; }
body.dark-theme.home-page .home-module-card,
body.dark-theme.home-page .home-info-strip {
    background: rgba(37, 49, 64, .97);
    border-color: rgba(255,255,255,.08);
}
body.dark-theme.home-page .home-module-body h3,
body.dark-theme.home-page .home-info-item h4 { color: #eef5fb; }
body.dark-theme.home-page .home-module-body p,
body.dark-theme.home-page .home-info-item p { color: #b9ccde; }
body.dark-theme.home-page .home-info-item { border-right-color: #465668; }
body.dark-theme.home-page .home-footer { color: #91a8be; }

@media (max-width: 1180px) {
    .home-app-shell { grid-template-columns: 220px minmax(0, 1fr); }
    .home-brand { padding: 0 16px; }
    .home-brand strong { font-size: .9rem; }
    .home-sidebar-footer { padding-left: 16px; padding-right: 16px; }
    .home-wireframe { margin-left: -16px; margin-right: -16px; }
    .home-content { padding-left: 22px; padding-right: 22px; }
    .home-modules { gap: 16px; }
    .home-module-body { padding-left: 18px; padding-right: 18px; }
    .home-module-body h3 { font-size: 1.22rem; }
    .home-info-strip { grid-template-columns: repeat(2, 1fr); row-gap: 22px; }
    .home-info-item:nth-child(2) { border-right: 0; }
    .home-info-item:nth-child(3) { padding-left: 0; }
}

@media (max-width: 900px) {
    .home-app-shell { display: block; }
    .home-sidebar {
        position: relative;
        width: 100%;
        min-height: auto;
        height: auto;
        overflow: visible;
    }
    .home-brand { min-height: 72px; }
    .home-nav {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 5px;
        padding: 10px;
    }
    .home-nav-item { margin: 0; padding: 0 12px; }
    .home-nav-separator,
    .home-sidebar-footer { display: none; }
    .home-topbar { position: relative; padding: 0 20px; }
    .home-topbar-brand span:not(.home-topbar-logo) { display: none; }
    .home-content { padding: 0 18px 20px; }
    .home-modules { grid-template-columns: 1fr; max-width: 680px; }
    .home-module-card { display: grid; grid-template-columns: 42% 58%; min-height: 250px; }
    .home-module-visual { height: 100%; min-height: 250px; border-bottom: 0; border-right: 1px solid #e0e7ee; }
    .home-module-icon { top: 26px; left: calc(42% - 31px); }
    .home-module-body { padding: 26px 22px 20px 42px; }
    .home-info-strip { max-width: 680px; }
}

@media (max-width: 650px) {
    .home-nav { grid-template-columns: 1fr 1fr; }
    .home-topbar { min-height: 66px; }
    .home-topbar-actions { gap: 8px; }
    .home-profile-name, .home-version { display: none; }
    .home-hero { padding-top: 28px; }
    .home-hero h1 { font-size: 2.35rem; }
    .home-module-card { display: flex; min-height: 0; }
    .home-module-visual { height: 165px; min-height: 165px; border-right: 0; border-bottom: 1px solid #e0e7ee; }
    .home-module-icon { top: 134px; left: 22px; }
    .home-module-body { padding: 38px 20px 20px; }
    .home-info-strip { grid-template-columns: 1fr; gap: 18px; }
    .home-info-item,
    .home-info-item:nth-child(3) { padding: 0 0 18px; border-right: 0; border-bottom: 1px solid #dce5ed; }
    .home-info-item:last-child { padding-bottom: 0; border-bottom: 0; }
    .home-footer { flex-direction: column; gap: 3px; text-align: center; }
}

/* ========================================================================== */
/* INTERFACE GLOBAL V1.2                                                     */
/* ========================================================================== */
:root {
    --app-sidebar-expanded: 268px;
    --app-sidebar-collapsed: 78px;
    --app-topbar-height: 78px;
    --app-navy: #061c34;
    --app-navy-2: #082844;
    --app-blue: #0b63d8;
    --app-sidebar-start: color-mix(in srgb, var(--primary-color) 42%, #061c34);
    --app-sidebar-mid: color-mix(in srgb, var(--primary-color) 52%, #082844);
    --app-sidebar-end: color-mix(in srgb, var(--primary-color) 32%, #031321);
    --app-accent-strong: color-mix(in srgb, var(--primary-color) 86%, #0053b8);
    --app-text: #10294b;
    --app-muted: #58708d;
    --app-card: rgba(255,255,255,.90);
    --app-card-strong: rgba(255,255,255,.96);
    --app-line: rgba(80,110,140,.18);
}

html.sidebar-collapsed-preload .app-shell,
body.sidebar-collapsed .app-shell {
    grid-template-columns: var(--app-sidebar-collapsed) minmax(0,1fr);
}

body.app-body {
    min-height: 100vh;
    overflow-x: hidden;
    background-color: #dfe8f1;
}

body.app-body::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: -2;
    background: linear-gradient(120deg, rgba(239,246,252,.24), rgba(226,238,248,.16));
    pointer-events: none;
}

body.app-body::after {
    content: "";
    position: fixed;
    inset: 0;
    z-index: -1;
    background: rgba(244,248,252,.06);
    backdrop-filter: blur(.5px);
    pointer-events: none;
}

.app-shell {
    min-height: 100vh;
    display: grid;
    grid-template-columns: var(--app-sidebar-expanded) minmax(0,1fr);
    transition: grid-template-columns .22s ease;
}

.app-sidebar {
    position: sticky;
    top: 0;
    height: 100vh;
    min-width: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    color: #fff;
    background: linear-gradient(180deg, var(--app-navy) 0%, var(--app-navy-2) 58%, #041729 100%);
    background: linear-gradient(180deg, var(--app-sidebar-start) 0%, var(--app-sidebar-mid) 58%, var(--app-sidebar-end) 100%);
    box-shadow: 7px 0 28px rgba(7,29,52,.18);
    z-index: 50;
}

.app-sidebar-head {
    min-height: var(--app-topbar-height);
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 12px;
    border-bottom: 1px solid rgba(255,255,255,.08);
}

.app-brand {
    min-width: 0;
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
    color: #fff;
    text-decoration: none;
}

.app-brand-icon {
    width: 42px;
    height: 42px;
    flex: 0 0 42px;
    display: grid;
    place-items: center;
    font-size: 1.8rem;
}

.app-brand-copy {
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    transition: opacity .15s ease, width .2s ease;
}
.app-brand-copy strong { display:block; font-size:1rem; line-height:1.15; }
.app-brand-copy small { display:block; margin-top:5px; color:#c5d8eb; font-size:.75rem; }

.sidebar-toggle {
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    display: grid;
    place-items: center;
    border: 0;
    border-radius: 8px;
    color: #cfe0f0;
    background: rgba(255,255,255,.07);
    cursor: pointer;
    transition: background .16s ease, transform .2s ease;
}
.sidebar-toggle:hover { background: rgba(255,255,255,.13); }

.app-nav { padding: 16px 9px 0; }
.app-nav-item {
    position: relative;
    min-height: 50px;
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 3px 0;
    padding: 0 14px;
    border-radius: 9px;
    color: #e7f0fa;
    text-decoration: none;
    white-space: nowrap;
    transition: background .16s ease, transform .16s ease, color .16s ease;
}
.app-nav-item:hover { color:#fff; background:rgba(255,255,255,.08); transform:translateX(2px); }
.app-nav-item.active { color:#fff; background:linear-gradient(90deg,var(--primary-color),var(--app-accent-strong,#0b5dce)); box-shadow:0 8px 20px rgba(4,95,209,.25); }
.app-nav-icon { width:32px; flex:0 0 32px; display:grid; place-items:center; font-size:1.18rem; }
.app-nav-svg svg { width:24px; height:24px; fill:none; stroke:currentColor; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.app-nav-label { overflow:hidden; transition:opacity .14s ease; }
.app-nav-sapata { display:flex; flex-direction:column; gap:2px; line-height:1.05; }
.app-nav-sapata small { color:#ffbf37; font-size:.68rem; }
.app-nav-separator { height:1px; margin:15px 14px 12px; background:rgba(255,255,255,.15); }

.app-sidebar-footer {
    margin-top: auto;
    padding: 0 18px 19px;
    text-align: center;
    color: #c2d3e4;
    font-size: .73rem;
    line-height: 1.45;
    overflow: hidden;
}
.app-sidebar-footer p { margin:8px 0 4px; white-space:nowrap; }
.app-sidebar-footer small { display:block; color:#d7e5f2; white-space:nowrap; }
.app-wireframe { height:150px; margin:0 -18px; opacity:.22; }
.app-wireframe svg { width:100%; height:100%; fill:none; stroke:color-mix(in srgb, var(--primary-color) 72%, #ffffff); stroke-width:1; }
.app-sidebar-illustration { height:150px; margin:0 -18px 8px; display:flex; align-items:center; justify-content:center; overflow:hidden; border-radius:8px; }
.app-sidebar-illustration img { width:100%; height:100%; object-fit:contain; opacity:.34; filter:brightness(1.16) saturate(.88); transition:opacity .18s ease; }
.app-sidebar:hover .app-sidebar-illustration img { opacity:.43; }

body.sidebar-collapsed .app-brand-copy,
body.sidebar-collapsed .app-nav-label,
body.sidebar-collapsed .app-sidebar-footer { opacity:0; pointer-events:none; }
body.sidebar-collapsed .app-sidebar-head { padding-left:14px; padding-right:10px; }
body.sidebar-collapsed .app-brand { flex:0 0 42px; }
body.sidebar-collapsed .sidebar-toggle { position:absolute; left:22px; bottom:14px; transform:rotate(180deg); z-index:3; }
body.sidebar-collapsed .app-sidebar-head { position:relative; min-height:126px; align-items:flex-start; padding-top:18px; }
body.sidebar-collapsed .app-nav { padding-left:8px; padding-right:8px; }
body.sidebar-collapsed .app-nav-item { justify-content:center; padding:0; gap:0; }
body.sidebar-collapsed .app-nav-icon { width:46px; flex-basis:46px; }
body.sidebar-collapsed .app-nav-separator { margin-left:9px; margin-right:9px; }

.app-main { min-width:0; min-height:100vh; }
.app-topbar {
    position: sticky;
    top: 0;
    z-index: 40;
    min-height: var(--app-topbar-height);
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:20px;
    padding:0 28px;
    background:rgba(255,255,255,.92);
    border-bottom:1px solid rgba(88,118,148,.14);
    box-shadow:0 4px 18px rgba(10,42,73,.06);
    backdrop-filter:blur(15px);
}
.app-topbar-left,.app-topbar-brand,.app-topbar-actions { display:flex; align-items:center; }
.app-topbar-left { min-width:0; gap:10px; }
.app-topbar-brand { min-width:0; gap:12px; color:inherit; text-decoration:none; }
.app-topbar-logo { width:43px; height:43px; display:grid; place-items:center; border-radius:10px; color:#fff; background:linear-gradient(145deg,var(--primary-color),var(--app-accent-strong,#084f9f)); box-shadow:0 7px 17px rgba(11,99,216,.2); }
.app-topbar-copy { min-width:0; }
.app-topbar-copy strong { display:block; color:#10294b; font-size:1rem; line-height:1.15; }
.app-topbar-copy small { display:block; margin-top:4px; color:#4f6b89; font-size:.78rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.app-topbar-actions { gap:14px; color:#163457; white-space:nowrap; }
.app-version { padding-right:14px; border-right:1px solid #d7e0e9; color:#3c6188; font-size:.8rem; }
.app-topbar-icon { width:36px; height:36px; display:grid; place-items:center; border-radius:50%; color:#315c88; text-decoration:none; }
.app-topbar-icon:hover { color:#0b63d8; background:#edf5ff; }
.app-avatar { width:37px; height:37px; display:grid; place-items:center; border-radius:50%; color:#fff; background:linear-gradient(135deg,var(--primary-color),var(--app-accent-strong,#0870b7)); font-weight:700; }
.app-user-name { font-size:.84rem; font-weight:650; }
.mobile-sidebar-toggle { display:none; width:38px; height:38px; border:0; border-radius:8px; background:#eef5fc; color:#194e81; cursor:pointer; }

.app-stage {
    position:relative;
    min-height:calc(100vh - var(--app-topbar-height));
    padding:30px;
}
.app-stage::before {
    content:"";
    position:absolute;
    inset:0;
    z-index:0;
    background:linear-gradient(180deg,rgba(240,247,252,.20),rgba(235,244,250,.30));
    pointer-events:none;
}
.app-page-container {
    position:relative;
    z-index:1;
    width:min(1220px,calc(100% - 4px));
    max-width:1220px;
    box-sizing:border-box;
    margin:0 auto;
    padding:32px 38px;
    border:1px solid rgba(255,255,255,.72);
    border-radius:16px;
    background:var(--app-card);
    box-shadow:0 18px 44px rgba(23,54,84,.13);
    backdrop-filter:blur(12px);
}
body.home-page .app-stage { padding:0; }
body.home-page .app-stage::before { background:linear-gradient(180deg,rgba(255,255,255,.14),rgba(235,244,250,.28)); }
body.home-page .home-container { width:100%; max-width:none; margin:0; padding:0 0 22px; border:0; border-radius:0; box-shadow:none; background:transparent; backdrop-filter:none; }
body.home-page .home-content { min-height:calc(100vh - var(--app-topbar-height)); padding-top:0; }

/* Harmonização das páginas internas */
.app-page-container > h1,
.app-page-container .history-header h1,
.app-page-container .detail-heading h1,
.app-page-container .config-heading h1 {
    color:#102d52;
    font-weight:760;
    letter-spacing:-.015em;
}
.app-page-container > p { color:#667b91; }
.back-link { display:inline-flex; align-items:center; gap:8px; padding:8px 11px; margin-bottom:22px; border-radius:8px; color:#265d91; background:rgba(233,243,252,.82); text-decoration:none; }
.back-link:hover { text-decoration:none; background:#e2f0fc; }

.app-page-container form:not(#csrf-helper) { background:rgba(255,255,255,.45); border:1px solid var(--app-line); border-radius:13px; padding:22px; }
.form-section-title { color:#173b63; border-bottom-color:rgba(11,99,216,.25); }
.form-group label { color:#304d69; font-weight:650; }
.form-group input,.form-group select,.form-control {
    border:1px solid #cbd8e4;
    border-radius:8px;
    background:rgba(255,255,255,.90);
    color:#17324f;
    box-shadow:0 1px 2px rgba(20,54,84,.03);
}
.form-group input:focus,.form-group select:focus,.form-control:focus { border-color:#5699df; box-shadow:0 0 0 3px rgba(30,120,215,.12); }
.btn-principal { border-radius:8px; background:linear-gradient(90deg,var(--primary-color),var(--app-accent-strong,#0757c6)); box-shadow:0 8px 16px rgba(11,99,216,.15); }
.btn-principal:hover { background:linear-gradient(90deg,var(--app-accent-strong,#0868d2),color-mix(in srgb,var(--primary-color) 70%,#032f6d)); transform:translateY(-1px); }
.btn-secundario { border-radius:8px; background:rgba(247,250,253,.92); border-color:#cbd8e4; color:#36536f; }

.resultado { border-radius:12px; box-shadow:0 8px 20px rgba(29,65,95,.06); }
.desenho-wrapper,.passo-a-passo,.detail-card,.config-card,.history-table-wrap,.no-history {
    border-color:var(--app-line) !important;
    background:rgba(255,255,255,.72) !important;
    border-radius:12px !important;
    box-shadow:0 7px 18px rgba(25,56,85,.05);
    backdrop-filter:blur(7px);
}
.history-table th { background:rgba(230,241,252,.88) !important; color:#1c527f !important; }
.history-table tbody tr:hover { background:rgba(241,247,252,.85) !important; }
.element-badge { box-shadow:0 4px 10px rgba(20,55,85,.12); }
.details-btn { border-radius:8px !important; background:rgba(255,255,255,.9) !important; }

/* Placeholder Sapata */
.module-placeholder-page { max-width:820px; margin:0 auto; text-align:center; padding:18px 0 28px; }
.page-kicker { display:inline-flex; align-items:center; gap:8px; margin-bottom:18px; color:#55718e; font-size:.85rem; font-weight:650; text-transform:uppercase; letter-spacing:.08em; }
.module-placeholder-card { position:relative; padding:42px 44px; border:1px solid var(--app-line); border-radius:18px; background:rgba(255,255,255,.78); box-shadow:0 14px 32px rgba(21,54,82,.09); backdrop-filter:blur(9px); }
.module-placeholder-icon { width:82px; height:82px; margin:0 auto 18px; display:grid; place-items:center; border-radius:50%; color:#fff; font-size:2rem; background:linear-gradient(145deg,#9ba8b5,#778592); box-shadow:0 10px 24px rgba(48,65,82,.18); }
.module-placeholder-badge { display:inline-flex; padding:5px 12px; border-radius:999px; color:#9a5a00; background:#fff0d8; border:1px solid #ffe0ad; font-size:.76rem; font-weight:700; }
.module-placeholder-card h1 { margin:14px 0 13px; color:#102d52; }
.module-placeholder-card p { max-width:610px; margin:0 auto 8px; color:#4f6680; font-size:1.05rem; }
.module-placeholder-card .module-placeholder-note { font-size:.92rem; color:#71849a; }
.module-placeholder-action { display:inline-flex; align-items:center; justify-content:center; gap:9px; margin-top:22px; width:auto; min-width:230px; }

/* Dark mode global */
body.dark-theme::before { background:rgba(13,23,34,.34); }
body.dark-theme::after { background:rgba(10,18,28,.08); }
body.dark-theme .app-topbar { background:rgba(26,38,52,.94); border-bottom-color:rgba(255,255,255,.08); }
body.dark-theme .app-topbar-copy strong,body.dark-theme .app-user-name { color:#eef5fb; }
body.dark-theme .app-topbar-copy small,body.dark-theme .app-version { color:#a9bfd5; }
body.dark-theme .app-version { border-right-color:#425164; }
body.dark-theme .app-stage::before { background:linear-gradient(180deg,rgba(15,24,35,.30),rgba(19,30,43,.42)); }
body.dark-theme .app-page-container { background:rgba(37,49,64,.91); border-color:rgba(255,255,255,.08); color:#eaf2f9; }
body.dark-theme .app-page-container > h1,
body.dark-theme .app-page-container .history-header h1,
body.dark-theme .app-page-container .detail-heading h1,
body.dark-theme .app-page-container .config-heading h1,
body.dark-theme .module-placeholder-card h1 { color:#eef5fb; }
body.dark-theme .app-page-container form:not(#csrf-helper),body.dark-theme .detail-card,body.dark-theme .config-card,body.dark-theme .history-table-wrap,body.dark-theme .module-placeholder-card { background:rgba(40,54,70,.76) !important; border-color:rgba(255,255,255,.10) !important; }
body.dark-theme .form-group input,body.dark-theme .form-group select,body.dark-theme .form-control { background:#34475b; color:#f5f8fb; border-color:#566d82; }

.sidebar-backdrop { display:none; }

@media (max-width: 1050px) {
    :root { --app-sidebar-expanded:240px; }
    .app-stage { padding:22px; }
    .app-page-container { padding:28px; }
    .app-user-name { display:none; }
}

@media (max-width: 760px) {
    .app-shell { display:block; }
    .app-sidebar {
        position:fixed;
        left:0; top:0; bottom:0;
        width:260px;
        transform:translateX(-102%);
        transition:transform .22s ease;
        z-index:100;
    }
    body.sidebar-mobile-open .app-sidebar { transform:translateX(0); }
    body.sidebar-collapsed .app-sidebar-head { min-height:var(--app-topbar-height); align-items:center; padding:0 12px; }
    body.sidebar-collapsed .app-brand { flex:1; }
    body.sidebar-collapsed .app-brand-copy,body.sidebar-collapsed .app-nav-label,body.sidebar-collapsed .app-sidebar-footer { opacity:1; pointer-events:auto; }
    body.sidebar-collapsed .sidebar-toggle { display:none; }
    body.sidebar-collapsed .app-nav-item { justify-content:flex-start; padding:0 14px; gap:14px; }
    .sidebar-toggle { display:none; }
    .mobile-sidebar-toggle { display:grid; place-items:center; }
    .sidebar-backdrop { position:fixed; inset:0; z-index:90; background:rgba(3,17,30,.45); backdrop-filter:blur(2px); }
    body.sidebar-mobile-open .sidebar-backdrop { display:block; }
    .app-topbar { min-height:68px; padding:0 14px; }
    .app-topbar-copy small,.app-version { display:none; }
    .app-topbar-actions { gap:8px; }
    .app-stage { min-height:calc(100vh - 68px); padding:14px; }
    .app-page-container { width:100%; padding:22px 18px; border-radius:13px; }
    body.home-page .app-stage { padding:0; }
    .module-placeholder-card { padding:32px 20px; }
}

@media (max-width: 520px) {
    .app-topbar-copy strong { font-size:.88rem; }
    .app-topbar-logo { width:36px; height:36px; }
    .app-topbar-icon,.app-user-name { display:none; }
    .app-page-container { padding:18px 14px; }
    .app-page-container form:not(#csrf-helper) { padding:16px; }
}

/* ========================================================================== */
/* REVISÃO VISUAL V1.2 — páginas técnicas                                    */
/* ========================================================================== */
:root {
    --tech-card: rgba(255,255,255,.84);
    --tech-card-strong: rgba(255,255,255,.93);
    --tech-line: rgba(77,105,132,.18);
    --tech-shadow: 0 12px 34px rgba(20,48,77,.10);
    --tech-radius: 16px;
}

/* O fundo permanece claramente visível em toda a aplicação. */
body.app-body::before { background: linear-gradient(120deg, rgba(239,246,252,.17), rgba(226,238,248,.10)); }
body.app-body::after { background: rgba(244,248,252,.025); backdrop-filter: blur(.2px); }
.app-stage::before { background: linear-gradient(180deg,rgba(240,247,252,.12),rgba(235,244,250,.18)); }
.app-page-container { background: rgba(255,255,255,.79); backdrop-filter: blur(8px); }

.engineering-page { width:100%; }
.page-breadcrumb { display:flex; align-items:center; gap:8px; margin-bottom:18px; color:#71859a; font-size:.78rem; font-weight:600; }
.page-breadcrumb a { color:#456885; text-decoration:none; }
.page-breadcrumb a:hover { color:var(--primary-color); }
.page-breadcrumb .fa-chevron-right { font-size:.62rem; color:#9badbe; }

.engineering-header { display:flex; align-items:center; gap:14px; margin-bottom:22px; padding:0 2px; }
.engineering-header-icon { width:48px; height:48px; flex:0 0 48px; display:grid; place-items:center; border-radius:13px; color:#fff; font-size:1.25rem; background:linear-gradient(145deg,var(--primary-color),var(--app-accent-strong)); box-shadow:0 8px 20px color-mix(in srgb,var(--primary-color) 25%, transparent); }
.engineering-header h1 { margin:0 0 3px; color:#102d52; font-size:1.68rem; line-height:1.12; letter-spacing:-.02em; }
.engineering-header p { margin:0; color:#61778e; font-size:.9rem; }
.beam-header .engineering-header-icon { background:linear-gradient(145deg,#13bd84,#079f69); }

.engineering-workbench { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(310px,.75fr); gap:20px; align-items:start; }
.column-workbench { grid-template-columns:minmax(0,1.5fr) minmax(320px,.72fr); }
.engineering-sidebar-panel { display:grid; gap:18px; position:sticky; top:calc(var(--app-topbar-height) + 20px); }

.technical-card { border:1px solid var(--tech-line); border-radius:var(--tech-radius); background:var(--tech-card); box-shadow:var(--tech-shadow); backdrop-filter:blur(9px); overflow:hidden; }
.technical-card.input-card { padding:22px; }
.technical-card-heading { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:18px; }
.technical-card-heading.compact { margin-bottom:14px; }
.technical-card-heading h2 { margin:2px 0 0; color:#173655; font-size:1.06rem; line-height:1.2; }
.eyebrow { display:block; color:#70859a; font-size:.68rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
.standard-chip { display:inline-flex; align-items:center; min-height:28px; padding:0 10px; border:1px solid color-mix(in srgb,var(--primary-color) 25%, transparent); border-radius:999px; color:color-mix(in srgb,var(--primary-color) 78%, #24435e); background:color-mix(in srgb,var(--primary-color) 8%, #fff); font-size:.7rem; font-weight:700; white-space:nowrap; }
.card-heading-icon { color:#6c86a0; font-size:1.05rem; }
.success-icon { color:#20a869; }

.engineering-form { padding:0 !important; border:0 !important; background:transparent !important; box-shadow:none !important; }
.field-grid { display:grid; gap:14px 16px; }
.field-grid.two-columns { grid-template-columns:repeat(2,minmax(0,1fr)); }
.engineering-form .form-group { margin:0; }
.engineering-form .form-group label { display:flex; align-items:baseline; justify-content:space-between; gap:10px; margin-bottom:6px; color:#294866; font-size:.79rem; font-weight:700; }
.engineering-form .form-group label span { color:#70859a; font-size:.69rem; font-weight:600; white-space:nowrap; }
.engineering-form .form-group small { display:block; margin-top:5px; color:#7b8da0; font-size:.69rem; line-height:1.35; }
.engineering-form input,.engineering-form select { min-height:42px; box-sizing:border-box; }
.engineering-actions { margin-top:18px; display:grid; grid-template-columns:1fr auto; gap:10px; }
.engineering-actions .btn-principal { width:100%; }
.compact-btn { width:auto; padding:7px 11px; font-size:.75rem; }

.form-section-block { padding:0 0 20px; margin:0 0 20px; border-bottom:1px solid var(--tech-line); }
.form-section-block:last-of-type { border-bottom:0; margin-bottom:4px; }
.section-tab-title { display:flex; align-items:center; gap:10px; margin-bottom:14px; }
.section-tab-title > span { width:28px; height:28px; display:grid; place-items:center; border-radius:8px; color:#fff; background:linear-gradient(145deg,var(--primary-color),var(--app-accent-strong)); font-size:.75rem; font-weight:800; }
.section-tab-title strong { display:block; color:#173655; font-size:.9rem; }
.section-tab-title small { display:block; margin-top:2px; color:#7b8da0; font-size:.68rem; }
.option-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px; }
.option-card { position:relative; display:grid; grid-template-columns:auto auto 1fr; align-items:start; gap:10px; padding:12px; border:1px solid var(--tech-line); border-radius:11px; background:rgba(248,251,254,.73); cursor:pointer; }
.option-card input { margin-top:4px; }
.option-card-icon { width:30px; height:30px; display:grid; place-items:center; border-radius:8px; color:var(--primary-color); background:color-mix(in srgb,var(--primary-color) 9%, #fff); }
.option-card strong { display:block; color:#294866; font-size:.78rem; }
.option-card small { display:block; margin-top:3px; color:#788b9e; font-size:.66rem; line-height:1.35; }
.conditional-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.conditional-panel { margin-top:10px; padding:12px; border:1px dashed rgba(77,105,132,.25); border-radius:10px; background:rgba(247,250,253,.54); }

.guidance-card,.result-summary-card,.section-card { padding:20px; }
.guidance-card { text-align:left; }
.guidance-icon { width:52px; height:52px; display:grid; place-items:center; margin-bottom:14px; border-radius:14px; color:#fff; font-size:1.25rem; background:linear-gradient(145deg,var(--primary-color),var(--app-accent-strong)); }
.guidance-card h2 { margin:0 0 8px; color:#173655; font-size:1.05rem; }
.guidance-card p { margin:0 0 14px; color:#61778e; font-size:.8rem; line-height:1.6; }
.guidance-list { list-style:none; padding:0; margin:0; display:grid; gap:8px; }
.guidance-list li { display:flex; align-items:center; gap:8px; color:#536d85; font-size:.75rem; }
.guidance-list i { color:#19a96a; }

.result-summary-card { border-top:3px solid #20ad70; }
.result-summary-card.result-error { border-top-color:#c84956; }
.status-dot { color:#20ad70; font-size:1.2rem; }
.result-error .status-dot { color:#c84956; }
.result-message { margin:0 0 14px; color:#5b7188; font-size:.76rem; line-height:1.45; }
.primary-result { padding:14px; border-radius:12px; background:linear-gradient(135deg,rgba(32,173,112,.10),rgba(255,255,255,.58)); border:1px solid rgba(32,173,112,.18); }
.primary-result span,.secondary-result span { display:block; color:#6c8197; font-size:.67rem; font-weight:700; text-transform:uppercase; letter-spacing:.05em; }
.primary-result strong,.secondary-result strong { display:block; margin:3px 0; color:#133a31; font-size:1.22rem; }
.primary-result small,.secondary-result small { color:#587367; font-size:.7rem; }
.secondary-result { margin-top:9px; padding:11px 13px; border:1px solid var(--tech-line); border-radius:10px; background:rgba(248,251,254,.62); }
.metric-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin-top:12px; }
.column-metrics { grid-template-columns:repeat(2,minmax(0,1fr)); }
.metric-tile { padding:10px; border:1px solid var(--tech-line); border-radius:10px; background:rgba(255,255,255,.62); }
.metric-tile span { display:block; color:#6e8398; font-size:.65rem; font-weight:700; }
.metric-tile strong { display:block; margin-top:2px; color:#173655; font-size:.9rem; line-height:1.2; }
.metric-tile small { display:block; margin-top:2px; color:#8798a8; font-size:.62rem; }
.report-link { display:flex; align-items:center; justify-content:center; gap:8px; margin-top:12px; min-height:38px; border-radius:9px; color:#b33b48; background:#fff4f5; border:1px solid #f2c6cb; text-decoration:none; font-size:.74rem; font-weight:700; }
.report-link:hover { background:#ffecef; }
.section-preview { max-width:390px; margin:0 auto; text-align:center; }
.section-preview svg { width:100%; max-height:330px; height:auto; }
.technical-note { margin:9px 0 12px; color:#74889b; font-size:.68rem; line-height:1.45; text-align:center; }

.full-width-card { margin-top:20px; padding:22px; }
.materials-visual { max-width:900px; margin:0 auto; text-align:center; }
.materials-visual svg { max-width:100%; height:auto; }
.calculation-steps { list-style:none; padding:0; margin:0; display:grid; gap:0; }
.calculation-steps li { display:grid; grid-template-columns:34px 1fr; gap:12px; padding:14px 0; border-bottom:1px solid var(--tech-line); }
.calculation-steps li:last-child { border-bottom:0; }
.step-index { width:28px; height:28px; display:grid; place-items:center; border-radius:8px; color:#fff; background:linear-gradient(145deg,var(--primary-color),var(--app-accent-strong)); font-size:.7rem; font-weight:800; }
.step-body > strong { color:#24435f; font-size:.82rem; }
.formula-line { margin:6px 0; padding:7px 9px; border-radius:8px; color:#275b86; background:rgba(231,241,251,.65); font-size:.75rem; overflow-wrap:anywhere; }
.calculation-line { margin:4px 0 0 !important; color:#5b7188; font-size:.73rem; line-height:1.65 !important; }

/* Histórico */
.history-page-modern { max-width:none; }
.history-card-modern { padding:0; overflow:hidden; }
.history-toolbar-modern { display:grid; grid-template-columns:auto minmax(220px,1fr) auto; gap:12px; align-items:center; padding:16px; border-bottom:1px solid var(--tech-line); background:rgba(255,255,255,.45); }
.history-filters { display:flex; gap:5px; padding:4px; border-radius:10px; background:rgba(229,239,249,.62); }
.history-filter { border:0; border-radius:7px; padding:8px 13px; color:#526d87; background:transparent; font-size:.72rem; font-weight:700; cursor:pointer; }
.history-filter.active { color:#fff; background:linear-gradient(90deg,var(--primary-color),var(--app-accent-strong)); box-shadow:0 4px 10px color-mix(in srgb,var(--primary-color) 20%, transparent); }
.history-search { position:relative; min-width:0; }
.history-search i { position:absolute; left:12px; top:50%; transform:translateY(-50%); color:#8294a7; }
.history-search input { width:100%; min-height:38px; box-sizing:border-box; padding:7px 12px 7px 34px; border:1px solid #cedae5; border-radius:9px; background:rgba(255,255,255,.88); color:#294866; }
.bulk-delete-btn { min-height:38px; border:1px solid #f0c4c9; border-radius:9px; padding:0 12px; color:#a33d48; background:#fff5f5; font-size:.72rem; font-weight:700; cursor:pointer; }
.bulk-delete-btn:disabled { opacity:.42; cursor:not-allowed; }
.modern-table { min-width:850px; }
.modern-table th { padding:11px 12px !important; font-size:.67rem; text-transform:uppercase; letter-spacing:.04em; }
.modern-table td { padding:13px 12px !important; font-size:.74rem; }
.check-col { width:36px; }
.element-badge { display:inline-flex !important; align-items:center; gap:6px; min-width:auto !important; padding:6px 9px !important; border-radius:8px !important; font-size:.68rem !important; }
.badge-viga { background:#19ae72 !important; }
.badge-pilar { background:#1474dd !important; }
.date-cell strong,.date-cell small { display:block; }
.date-cell strong { color:#294866; font-size:.72rem; }
.date-cell small { margin-top:3px; color:#8091a3; font-size:.65rem; }
.history-primary-data,.history-result { display:grid; gap:3px; }
.history-primary-data strong,.history-result strong { color:#25415d; }
.history-primary-data span,.history-result span { color:#71859a; font-size:.66rem; }
.history-actions { display:flex; align-items:center; gap:5px; }
.icon-action { width:32px; height:32px; display:grid; place-items:center; border-radius:8px; color:#2f6ba2; background:#eef6ff; text-decoration:none; }
.icon-action.pdf { color:#bd3e4a; background:#fff1f3; }
.icon-action:hover { filter:brightness(.97); }
.history-footer { padding:11px 16px; color:#7a8da1; font-size:.66rem; border-top:1px solid var(--tech-line); background:rgba(249,251,253,.55); }
.empty-state { max-width:620px; margin:20px auto; padding:38px; text-align:center; }
.empty-state .guidance-icon { margin-left:auto; margin-right:auto; }
.empty-state h2 { color:#173655; }
.empty-state p { color:#687e94; }

/* Detalhe do histórico */
.detail-page { max-width:1080px; margin:0 auto; }
.detail-topbar { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:14px; }
.detail-engineering-header { margin:0 0 20px; text-align:left; }
.detail-engineering-header p { margin:0; }
.detail-card { padding:20px; margin-bottom:18px; }
.detail-card .technical-card-heading { margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid var(--tech-line); }
.input-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:9px 14px; }
.input-item { padding:10px 11px; border:1px solid var(--tech-line); border-radius:10px; background:rgba(255,255,255,.55); }
.input-label { display:block; color:#71859a; font-size:.66rem; }
.input-value { display:block; margin-top:3px; color:#294866; font-size:.8rem; font-weight:800; }
.result-box { border-left:3px solid #20ad70 !important; background:rgba(246,253,249,.80) !important; }
.result-main { color:#173f33 !important; font-size:.95rem !important; }
.result-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; }
.result-metric { padding:9px 10px !important; border:1px solid var(--tech-line); border-radius:9px !important; background:rgba(255,255,255,.60) !important; }
.result-metric small { display:block; color:#778b9e; font-size:.62rem; }
.visual-container { text-align:center; }
.section-svg { max-width:420px; margin:12px auto; }
.materials-svg { max-width:820px; margin:12px auto; }
.section-svg svg,.materials-svg svg { max-width:100%; height:auto; }
.export-row { text-align:center; margin-top:12px; }
.steps-list { list-style:none; padding:0; margin:0; }
.steps-list > li { padding:12px 0; border-bottom:1px solid var(--tech-line); }
.steps-list > li:last-child { border-bottom:0; }

/* Configurações */
.config-page { max-width:1050px !important; }
.config-engineering-header { margin-bottom:20px; }
.config-form { background:transparent !important; border:0 !important; padding:0 !important; }
.config-card { background:var(--tech-card) !important; border-radius:var(--tech-radius) !important; box-shadow:var(--tech-shadow) !important; }
.config-card-wide { grid-column:1/-1; }
.sidebar-image-layout { display:grid; grid-template-columns:1.05fr .95fr; gap:18px; align-items:stretch; }
.sidebar-preview-frame { min-height:170px; display:flex; align-items:center; justify-content:center; padding:14px; border-radius:12px; background:linear-gradient(145deg,var(--app-sidebar-start),var(--app-sidebar-mid)); }
.sidebar-native-file-input { position:absolute; inset:0; width:100%; height:100%; opacity:0; cursor:pointer; }
.selected-file-name { display:block; max-width:100%; color:#637b91; font-size:.68rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.save-row { display:flex; justify-content:flex-end; }

/* Sapata */
.footing-placeholder { max-width:900px; margin:0 auto; }
.footing-title-row { display:flex; align-items:center; justify-content:center; gap:12px; margin-bottom:16px; }
.footing-title-row h1 { margin:0; color:#102d52; }
.footing-card { display:grid; grid-template-columns:1.05fr .95fr; align-items:center; min-height:430px; padding:28px; }
.footing-illustration { min-height:320px; display:grid; place-items:center; border-radius:14px; background:linear-gradient(145deg,rgba(255,255,255,.70),rgba(237,243,248,.78)); }
.footing-illustration svg { width:min(100%,420px); height:auto; }
.footing-message { padding:26px; text-align:center; }
.footing-message h2 { margin:0 0 12px; color:#294866; font-size:1.08rem; }
.footing-message p { margin:0 0 9px; color:#647b91; font-size:.82rem; line-height:1.6; }
.footing-message .btn-secundario { display:inline-flex; align-items:center; gap:8px; margin-top:14px; }

body.dark-theme .technical-card,body.dark-theme .option-card,body.dark-theme .conditional-panel { background:rgba(37,50,66,.83) !important; border-color:rgba(255,255,255,.09) !important; }
body.dark-theme .engineering-header h1,body.dark-theme .technical-card-heading h2,body.dark-theme .section-tab-title strong,body.dark-theme .guidance-card h2,body.dark-theme .metric-tile strong,body.dark-theme .footing-title-row h1,body.dark-theme .footing-message h2 { color:#eef5fb; }
body.dark-theme .engineering-header p,body.dark-theme .guidance-card p,body.dark-theme .result-message,body.dark-theme .footing-message p { color:#b7c9da; }
body.dark-theme .input-item,body.dark-theme .metric-tile { background:rgba(49,65,82,.75) !important; border-color:rgba(255,255,255,.08); }
body.dark-theme .input-value,body.dark-theme .history-primary-data strong,body.dark-theme .history-result strong { color:#eaf2f9; }

@media (max-width:980px) {
    .engineering-workbench,.column-workbench { grid-template-columns:1fr; }
    .engineering-sidebar-panel { position:static; grid-template-columns:repeat(2,minmax(0,1fr)); }
    .result-summary-card,.guidance-card { grid-column:1/-1; }
    .history-toolbar-modern { grid-template-columns:1fr 1fr; }
    .history-search { grid-column:1/-1; grid-row:2; }
}
@media (max-width:720px) {
    .field-grid.two-columns,.option-grid,.conditional-grid,.sidebar-image-layout,.footing-card { grid-template-columns:1fr; }
    .engineering-sidebar-panel { grid-template-columns:1fr; }
    .engineering-header { align-items:flex-start; }
    .engineering-header h1 { font-size:1.4rem; }
    .technical-card.input-card,.technical-card.full-width-card { padding:16px; }
    .history-toolbar-modern { grid-template-columns:1fr; }
    .history-search { grid-column:auto; grid-row:auto; }
    .history-filters { overflow-x:auto; }
    .input-grid,.result-grid { grid-template-columns:1fr 1fr; }
    .footing-card { min-height:0; }
    .footing-illustration { min-height:240px; }
}
@media (max-width:520px) {
    .engineering-actions { grid-template-columns:1fr; }
    .metric-grid,.column-metrics,.input-grid,.result-grid { grid-template-columns:1fr; }
    .page-breadcrumb { flex-wrap:wrap; }
}
