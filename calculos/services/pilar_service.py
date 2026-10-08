# calculos/services/pilar_service.py
# Versão v1.2: gráfico do aço coerente com o estado real de tração/compressão.
import math

from . import armadura_service


# ==============================================================================
# PARÂMETROS DO MODELO
# ==============================================================================

ALPHA_CC = 1.00
GAMMA_C = 1.50
GAMMA_S = 1.15
E_S_MPA = 200000.0

# O modelo resistente implementado nesta versão está limitado a fck <= 50 MPa.
LAMBDA_BLOCO = 0.80
ETA_BLOCO = 1.00
EPSILON_CU2 = 3.5e-3
EPSILON_C2 = 2.0e-3
EPSILON_C_HINGE = 1.75e-3

PHI_ESTRIBO_MM = 8.0
DG_MM = 20.0

# Hipótese associada à interface com um único momento de primeira ordem:
# após a consideração da imperfeição geométrica e da excentricidade mínima,
# adota-se M01 = M02 = M0Ed, logo r_m = 1 e C = 0.70.
C_ESBELTEZA = 0.70
N_BAL = 0.40
C_CURVATURA = 10.0

# Critérios numéricos da resolução de N_Rd(x) = N_Ed por bisseção.
# São critérios de implementação, não parâmetros normativos.
EQUILIBRIO_AXIAL_MAX_EXPANSOES = 40
EQUILIBRIO_AXIAL_MAX_ITERACOES = 140
EQUILIBRIO_AXIAL_TOL_ABS_N = 1.0
EQUILIBRIO_AXIAL_TOL_REL = 1e-8

# Fatores de comprimento efetivo adotados para os casos idealizados de apoio.
# O utilizador pode substituir o valor calculado introduzindo l0 manualmente.
FATORES_COMPRIMENTO_EFETIVO = {
    "artic-artic": 1.00,
    "encab-artic": 0.70,
    "artic-encab": 0.70,
    "encab-encab": 0.50,
    "encab-livre": 2.00,
    "livre-encab": 2.00,
}

ROTULOS_LIGACAO = {
    "artic-artic": "Articulado - Articulado",
    "encab-artic": "Encastrado - Articulado",
    "artic-encab": "Articulado - Encastrado",
    "encab-encab": "Encastrado - Encastrado",
    "encab-livre": "Encastrado - Livre",
    "livre-encab": "Livre - Encastrado",
}


def _passo(titulo, formula=None, calculo=None):
    p = {"titulo": titulo}
    if formula:
        p["formula"] = formula
    if calculo:
        p["calculo"] = calculo
    return p


def _resolver_comprimento_efetivo(l_m, cond_ligacao, usar_l0_manual=False, l0_manual_m=None):
    """Resolve o comprimento efetivo l0 a partir do modo escolhido na interface.

    No modo manual, o comprimento real l não participa no cálculo e pode ser None.
    """
    if usar_l0_manual:
        if l0_manual_m is None:
            raise ValueError("Indique o comprimento efetivo l₀ quando a opção manual está ativa.")
        l0_manual_m = float(l0_manual_m)
        if not math.isfinite(l0_manual_m) or l0_manual_m <= 0:
            raise ValueError("O comprimento efetivo manual l₀ deve ser positivo e finito.")
        return l0_manual_m, None, "Introduzido manualmente"

    if l_m is None:
        raise ValueError("Indique o comprimento real l quando o comprimento efetivo não é introduzido manualmente.")
    l_m = float(l_m)
    if not math.isfinite(l_m) or l_m <= 0:
        raise ValueError("O comprimento real l deve ser positivo e finito.")

    if cond_ligacao not in FATORES_COMPRIMENTO_EFETIVO:
        raise ValueError("Selecione uma condição de ligação válida para o pilar.")

    beta_l0 = FATORES_COMPRIMENTO_EFETIVO[cond_ligacao]
    l0_m = beta_l0 * l_m
    return l0_m, beta_l0, ROTULOS_LIGACAO.get(cond_ligacao, cond_ligacao)


def _resolver_fluencia(considerar_fluencia=False, phi_ef=None):
    """Resolve phi_ef sem impor um valor oculto quando a fluência é desativada."""
    if not considerar_fluencia:
        return 0.0

    if phi_ef is None:
        raise ValueError("Indique φef quando a opção 'Considerar fluência' está ativa.")

    phi_ef = float(phi_ef)
    if not math.isfinite(phi_ef) or phi_ef < 0:
        raise ValueError("O coeficiente efetivo de fluência φef deve ser finito e não negativo.")
    return phi_ef


def _validar_entradas(b_mm, h_mm, l0_m, f_ck, f_yk, N_Ed_kN, M_Ed_kNm, c_nom_mm):
    valores = (b_mm, h_mm, l0_m, f_ck, f_yk, N_Ed_kN, M_Ed_kNm, c_nom_mm)
    if not all(math.isfinite(float(v)) for v in valores):
        raise ValueError("Todos os dados de entrada devem ser valores finitos.")

    if b_mm <= 0 or h_mm <= 0:
        raise ValueError("A largura e a altura da secção devem ser positivas.")
    if l0_m <= 0:
        raise ValueError("O comprimento efetivo l₀ deve ser positivo.")
    if not (0 < f_ck <= 50):
        raise ValueError("O modelo implementado está limitado a classes de betão com fck ≤ 50 MPa.")
    if f_yk <= 0:
        raise ValueError("A resistência característica do aço deve ser positiva.")
    if N_Ed_kN <= 0:
        raise ValueError("O esforço axial N_Ed deve ser estritamente positivo.")
    if M_Ed_kNm < 0:
        raise ValueError("M_Ed deve ser introduzido como magnitude não negativa do momento de 1.ª ordem.")
    if c_nom_mm <= 0:
        raise ValueError("O recobrimento nominal deve ser positivo.")

    if min(b_mm, h_mm) <= 2.0 * (c_nom_mm + PHI_ESTRIBO_MM + 12.0 / 2.0):
        raise ValueError("A secção não possui espaço suficiente para a armadura mínima considerada pelo módulo.")


def _propriedades_basicas(b_mm, h_mm, l0_m, f_ck, f_yk, N_Ed_kN):
    f_cd = ALPHA_CC * f_ck / GAMMA_C
    f_yd = f_yk / GAMMA_S
    Ac_mm2 = b_mm * h_mm
    i_mm = h_mm / math.sqrt(12.0)
    lambda_esb = l0_m * 1000.0 / i_mm
    N_Ed_N = N_Ed_kN * 1000.0
    n = N_Ed_N / (Ac_mm2 * f_cd)
    return f_cd, f_yd, Ac_mm2, i_mm, lambda_esb, N_Ed_N, n


def _limites_armadura(Ac_mm2, N_Ed_N, f_yd):
    As_min_1 = 0.10 * N_Ed_N / f_yd
    As_min_2 = 0.002 * Ac_mm2
    As_min = max(As_min_1, As_min_2)
    As_max = 0.04 * Ac_mm2
    return As_min_1, As_min_2, As_min, As_max


def _parametros_estabilidade(
    As_total_mm2,
    d_mm,
    f_ck,
    f_yd,
    f_cd,
    Ac_mm2,
    n,
    lambda_esb,
    l0_m,
    N_Ed_N,
    M0_Ed_kNm,
    phi_ef,
    C_esbelteza=C_ESBELTEZA,
    usar_momentos_extremidade=False,
    M01_kNm=None,
    M02_kNm=None,
    M_min_kNm=0.0,
):
    """Avalia a esbelteza e os efeitos de 2.ª ordem para uma armadura candidata.

    No modo simples é preservada a formulação histórica da aplicação:
    M01 = M02 = M0Ed, C = 0,70 e MEd,total = M0Ed + M2.

    No modo avançado, C é obtido a partir da relação entre os momentos de
    extremidade provenientes da análise. M01 e M02 usados no momento final já
    incluem a imperfeição geométrica aplicada numa única direção. Para pilares
    esbeltos usa-se:
        M0e = max(0,6 M02 + 0,4 M01 ; 0,4 M02)
        MEd = max(M02 ; M0e + M2 ; M01 + 0,5 M2 ; Mmin)
    """
    omega = As_total_mm2 * f_yd / (Ac_mm2 * f_cd)
    A = 1.0 / (1.0 + 0.2 * phi_ef)
    B = math.sqrt(1.0 + 2.0 * omega)
    C = float(C_esbelteza)

    lambda_lim = float("inf") if n <= 0 else 20.0 * A * B * C / math.sqrt(n)
    esbelto = lambda_esb > lambda_lim

    M01 = float(M01_kNm) if M01_kNm is not None else float(M0_Ed_kNm)
    M02 = float(M02_kNm) if M02_kNm is not None else float(M0_Ed_kNm)
    M_min = float(M_min_kNm)
    M0e = max(0.6 * M02 + 0.4 * M01, 0.4 * M02) if usar_momentos_extremidade else float(M0_Ed_kNm)

    if usar_momentos_extremidade:
        termos = {
            "M02": M02,
            "M_min": M_min,
        }
        M_total_inicial = max(termos.values())
        termo_governante = max(termos, key=termos.get)
    else:
        M_total_inicial = float(M0_Ed_kNm)
        termo_governante = "M0Ed"

    dados = {
        "omega": omega,
        "A": A,
        "B": B,
        "C": C,
        "lambda_lim": lambda_lim,
        "esbelto": esbelto,
        "phi_ef": phi_ef,
        "K_phi": 1.0,
        "beta_phi": 0.0,
        "K_r": 1.0,
        "n_u": 1.0 + omega,
        "inv_r0_mm": 0.0,
        "inv_r_mm": 0.0,
        "e2_mm": 0.0,
        "M2_kNm": 0.0,
        "M0e_kNm": M0e,
        "M01_kNm": M01,
        "M02_kNm": M02,
        "M_total_kNm": M_total_inicial,
        "termo_governante": termo_governante,
        "termos_momento_final": termos if usar_momentos_extremidade else {"M0Ed": float(M0_Ed_kNm)},
        "admissivel": True,
    }

    if not esbelto:
        return dados

    n_u = 1.0 + omega
    if n >= n_u - 1e-12:
        dados["admissivel"] = False
        dados["motivo"] = "n ≥ n_u no cálculo de K_r"
        return dados

    den = n_u - N_BAL
    if den <= 0:
        dados["admissivel"] = False
        dados["motivo"] = "denominador não positivo no cálculo de K_r"
        return dados

    K_r = min(1.0, (n_u - n) / den)
    if K_r <= 0:
        dados["admissivel"] = False
        dados["motivo"] = "K_r não positivo"
        return dados

    beta_phi = 0.35 + f_ck / 200.0 - lambda_esb / 150.0
    K_phi = max(1.0, 1.0 + beta_phi * phi_ef)

    epsilon_yd = f_yd / E_S_MPA
    inv_r0 = epsilon_yd / (0.45 * d_mm)
    inv_r = K_r * K_phi * inv_r0

    l0_mm = l0_m * 1000.0
    e2_mm = inv_r * l0_mm * l0_mm / C_CURVATURA
    M2_kNm = N_Ed_N * e2_mm / 1e6

    if usar_momentos_extremidade:
        termos = {
            "M02": M02,
            "M0e + M2": M0e + M2_kNm,
            "M01 + 0,5 M2": M01 + 0.5 * M2_kNm,
            "M_min": M_min,
        }
        M_total = max(termos.values())
        termo_governante = max(termos, key=termos.get)
    else:
        termos = {"M0Ed + M2": float(M0_Ed_kNm) + M2_kNm}
        M_total = float(M0_Ed_kNm) + M2_kNm
        termo_governante = "M0Ed + M2"

    dados.update({
        "K_r": K_r,
        "beta_phi": beta_phi,
        "K_phi": K_phi,
        "inv_r0_mm": inv_r0,
        "inv_r_mm": inv_r,
        "e2_mm": e2_mm,
        "M2_kNm": M2_kNm,
        "M_total_kNm": M_total,
        "termo_governante": termo_governante,
        "termos_momento_final": termos,
    })
    return dados


def _epsilon_c_max_pilar(x_mm, h_mm):
    """Extensão máxima de compressão do betão para o domínio da secção.

    Para fck <= 50 MPa:
      * se x <= h, adota-se epsilon_cu2 = 3,5 por mil;
      * se x > h, a secção está integralmente comprimida e a extensão da fibra
        superior é obtida pela reta que passa pelo ponto de charneira
        epsilon = 1,75 por mil a meia altura da secção.

    Da compatibilidade linear:
        epsilon_c,max * (1 - h/(2x)) = 1,75 por mil
    logo:
        epsilon_c,max = 1,75 por mil / (1 - h/(2x)).

    A expressão tende para 1,75 por mil em compressão uniforme e vale
    3,5 por mil quando x = h.
    """
    x_mm = float(x_mm)
    h_mm = float(h_mm)
    if x_mm <= 0.0 or h_mm <= 0.0:
        raise ValueError("x e h devem ser positivos.")

    if x_mm <= h_mm + 1e-12:
        return EPSILON_CU2, "eixo_neutro_na_secao"

    den = 1.0 - h_mm / (2.0 * x_mm)
    if den <= 0.0:
        raise ValueError("Geometria inválida no cálculo da extensão máxima do betão.")

    eps_c = EPSILON_C_HINGE / den
    eps_c = max(EPSILON_C_HINGE, min(EPSILON_CU2, eps_c))
    return eps_c, "secao_integralmente_comprimida"


def _estado_secao(x_mm, b_mm, h_mm, f_cd, f_yd, posicoes):
    """
    Calcula N_Rd e M_Rd para uma profundidade x do eixo neutro.

    Convenção de sinais:
      compressão positiva;
      tração negativa.

    Para x > h, a distribuição de extensões é ajustada pelo ponto de charneira
    epsilon = 1,75 por mil a meia altura, em vez de manter artificialmente
    epsilon_cu2 = 3,5 por mil na fibra superior. O bloco retangular equivalente
    de compressão mantém-se como aproximação resistente adotada no módulo.

    A força do aço comprimido é tomada como contribuição líquida relativamente
    ao betão substituído quando o centro do varão se encontra dentro do bloco
    equivalente de compressão.
    """
    if x_mm <= 0:
        raise ValueError("x deve ser positivo.")

    epsilon_c_top, regime_deformacao = _epsilon_c_max_pilar(x_mm, h_mm)
    epsilon_c_bottom = epsilon_c_top * (1.0 - h_mm / x_mm)

    bloco_mm = min(LAMBDA_BLOCO * x_mm, h_mm)
    Cc_N = ETA_BLOCO * f_cd * b_mm * bloco_mm
    y_c = bloco_mm / 2.0

    N_aco = 0.0
    M_aco = 0.0
    estados = []

    for barra in posicoes:
        y = float(barra["y_mm"])
        phi = float(barra["phi_mm"])
        As_i = math.pi * phi * phi / 4.0

        eps_s = epsilon_c_top * (1.0 - y / x_mm)
        sigma_s = max(-f_yd, min(E_S_MPA * eps_s, f_yd))

        sigma_betao_sub = ETA_BLOCO * f_cd if y <= bloco_mm + 1e-12 else 0.0
        sigma_liq = sigma_s - sigma_betao_sub
        F_s = As_i * sigma_liq
        z_i = h_mm / 2.0 - y

        N_aco += F_s
        M_aco += F_s * z_i
        estados.append({
            "y_mm": y,
            "phi_mm": phi,
            "As_mm2": As_i,
            "epsilon_s": eps_s,
            "sigma_s_mpa": sigma_s,
            "sigma_liquida_mpa": sigma_liq,
            "F_s_N": F_s,
        })

    N_Rd = Cc_N + N_aco
    M_Rd = Cc_N * (h_mm / 2.0 - y_c) + M_aco

    return {
        "x_mm": x_mm,
        "bloco_mm": bloco_mm,
        "Cc_N": Cc_N,
        "N_Rd_N": N_Rd,
        "M_Rd_Nmm": M_Rd,
        "estados_barras": estados,
        "epsilon_c_top": epsilon_c_top,
        "epsilon_c_bottom": epsilon_c_bottom,
        "regime_deformacao": regime_deformacao,
    }


def _resolver_equilibrio_axial(b_mm, h_mm, f_cd, f_yd, posicoes, N_Ed_N):
    """Resolve N_Rd(x) = N_Ed por bisseção."""
    x_inf = 1e-6
    e_inf = _estado_secao(x_inf, b_mm, h_mm, f_cd, f_yd, posicoes)

    x_sup = max(h_mm, 1.0)
    e_sup = _estado_secao(x_sup, b_mm, h_mm, f_cd, f_yd, posicoes)

    for _ in range(EQUILIBRIO_AXIAL_MAX_EXPANSOES):
        if e_sup["N_Rd_N"] >= N_Ed_N:
            break
        x_sup *= 2.0
        e_sup = _estado_secao(x_sup, b_mm, h_mm, f_cd, f_yd, posicoes)
    else:
        return None

    if e_inf["N_Rd_N"] > N_Ed_N:
        return None

    for _ in range(EQUILIBRIO_AXIAL_MAX_ITERACOES):
        x = 0.5 * (x_inf + x_sup)
        e = _estado_secao(x, b_mm, h_mm, f_cd, f_yd, posicoes)
        erro = e["N_Rd_N"] - N_Ed_N
        tolerancia_N = max(
            EQUILIBRIO_AXIAL_TOL_ABS_N,
            abs(N_Ed_N) * EQUILIBRIO_AXIAL_TOL_REL,
        )
        if abs(erro) <= tolerancia_N:
            return e
        if erro < 0:
            x_inf = x
        else:
            x_sup = x

    return _estado_secao(0.5 * (x_inf + x_sup), b_mm, h_mm, f_cd, f_yd, posicoes)


def _avaliar_candidata(
    c, b_mm, h_mm, l0_m, f_ck, f_cd, f_yd, Ac_mm2, n,
    lambda_esb, N_Ed_N, M0_Ed_kNm, phi_ef,
    C_esbelteza=C_ESBELTEZA,
    usar_momentos_extremidade=False,
    M01_kNm=None,
    M02_kNm=None,
    M_min_kNm=0.0,
):
    As_mm2 = c["area_total_cm2"] * 100.0
    a_extremo = min(p["y_mm"] for p in c["posicoes"])
    d_mm = h_mm - a_extremo

    est = _parametros_estabilidade(
        As_total_mm2=As_mm2,
        d_mm=d_mm,
        f_ck=f_ck,
        f_yd=f_yd,
        f_cd=f_cd,
        Ac_mm2=Ac_mm2,
        n=n,
        lambda_esb=lambda_esb,
        l0_m=l0_m,
        N_Ed_N=N_Ed_N,
        M0_Ed_kNm=M0_Ed_kNm,
        phi_ef=phi_ef,
        C_esbelteza=C_esbelteza,
        usar_momentos_extremidade=usar_momentos_extremidade,
        M01_kNm=M01_kNm,
        M02_kNm=M02_kNm,
        M_min_kNm=M_min_kNm,
    )
    if not est["admissivel"]:
        return None

    sec = _resolver_equilibrio_axial(
        b_mm=b_mm, h_mm=h_mm, f_cd=f_cd, f_yd=f_yd,
        posicoes=c["posicoes"], N_Ed_N=N_Ed_N,
    )
    if sec is None:
        return None

    M_Rd = sec["M_Rd_Nmm"] / 1e6
    if M_Rd + 1e-9 < est["M_total_kNm"]:
        return None

    r = dict(c)
    r.update({
        "As_total_mm2": As_mm2,
        "d_mm": d_mm,
        "estabilidade": est,
        "estado_secao": sec,
        "M_Rd_kNm": M_Rd,
        "M_total_kNm": est["M_total_kNm"],
    })
    return r


def _criterio(sol):
    """Critério hierárquico de seleção da solução resistente.

    O último termo apenas torna explícito o desempate determinístico já
    implícito na ordem de geração: em igualdade integral dos restantes
    critérios, mantém-se preferência pela disposição perimetral.
    """
    return (
        round(sol["area_total_cm2"], 9),
        sol["n_barras"],
        sol["n_diametros"],
        sol["diametro_max_mm"],
        sol["combinacao_str"],
        0 if sol.get("disposicao") == "perimetral" else 1,
    )


def _calcular_imperfeicao_geometrica(l0_m, h_mm, N_Ed_kN, M_Ed_kNm):
    """Calcula separadamente imperfeição geométrica e excentricidade mínima.

    Procedimento adotado:
        e_i = l0 / 400
        M_i = N_Ed * e_i
        M_1 = M_Ed + M_i
        e_0 = max(h / 30, 20 mm)
        M_min = N_Ed * e_0
        M_0Ed = max(M_1, M_min)
    """
    l0_mm = float(l0_m) * 1000.0
    h_mm = float(h_mm)
    N_Ed_kN = float(N_Ed_kN)
    M_Ed_kNm = float(M_Ed_kNm)

    e_i_mm = l0_mm / 400.0
    M_i_kNm = N_Ed_kN * (e_i_mm / 1000.0)
    M1_Ed_kNm = M_Ed_kNm + M_i_kNm

    e_h_mm = h_mm / 30.0
    e0_mm = max(e_h_mm, 20.0)
    M_min_kNm = N_Ed_kN * (e0_mm / 1000.0)

    M0_Ed_kNm = max(M1_Ed_kNm, M_min_kNm)

    return {
        "e_i_mm": e_i_mm,
        "M_i_kNm": M_i_kNm,
        "M1_Ed_kNm": M1_Ed_kNm,
        "e_h_mm": e_h_mm,
        "e0_mm": e0_mm,
        "M_min_kNm": M_min_kNm,
        "M0_Ed_kNm": M0_Ed_kNm,
    }


def _preparar_momentos_extremidade(M_01_kNm, M_02_kNm, M_i_kNm, M_min_kNm):
    """Normaliza os momentos de extremidade para a análise de estabilidade.

    Os momentos introduzidos provêm da análise estrutural e conservam o respetivo
    sinal. Internamente, o maior momento em módulo é orientado como M02 positivo e
    o menor momento mantém o sinal relativo a M02. Assim, |M02,an| >= |M01,an|.

    O parâmetro de distribuição de curvatura é calculado com os momentos da análise:
        r_m = M01,an / M02,an
        C = 1,7 - r_m

    A imperfeição geométrica é considerada numa única direção e, por isso, o mesmo
    incremento M_i = N_Ed e_i é somado algebricamente aos dois momentos normalizados:
        M01 = M01,an + M_i
        M02 = M02,an + M_i

    Este tratamento reproduz a sequência usada no Exemplo 5.1 de Goodchild et al.
    para momentos de extremidade opostos.
    """
    m1_raw = float(M_01_kNm)
    m2_raw = float(M_02_kNm)
    M_i = float(M_i_kNm)
    M_min = float(M_min_kNm)

    if not all(math.isfinite(v) for v in (m1_raw, m2_raw, M_i, M_min)):
        raise ValueError("Os momentos de extremidade e os termos de imperfeição devem ser finitos.")

    # Ordenar por módulo para garantir |M02| >= |M01|.
    pares = sorted((m1_raw, m2_raw), key=lambda v: abs(v))
    m_menor_raw, m_maior_raw = pares[0], pares[1]

    if abs(m_maior_raw) <= 1e-12:
        raise ValueError(
            "No modo de momentos distintos, pelo menos um momento de extremidade "
            "deve ser diferente de zero."
        )

    # Orientar o maior momento como positivo, preservando o sinal relativo do menor.
    orientacao = 1.0 if m_maior_raw >= 0.0 else -1.0
    M02_analise = abs(m_maior_raw)
    M01_analise = m_menor_raw * orientacao

    # r_m e C dependem dos momentos provenientes da análise, antes da imperfeição.
    r_m = M01_analise / M02_analise
    r_m = max(-1.0, min(1.0, r_m))
    C = 1.7 - r_m

    # A imperfeição atua numa única direção, sendo somada algebricamente aos dois.
    M01 = M01_analise + M_i
    M02 = M02_analise + M_i

    # Momento equivalente de primeira ordem e mínimo regulamentar adotado no módulo.
    M0e = max(0.6 * M02 + 0.4 * M01, 0.4 * M02)
    M0Ed = max(M02, M_min)

    return {
        "M_01_entrada_kNm": m1_raw,
        "M_02_entrada_kNm": m2_raw,
        "M_01_ordenado_entrada_kNm": M01_analise,
        "M_02_ordenado_entrada_kNm": M02_analise,
        "M01_analise_kNm": M01_analise,
        "M02_analise_kNm": M02_analise,
        "M01_kNm": M01,
        "M02_kNm": M02,
        "r_m": r_m,
        "C": C,
        "M0e_kNm": M0e,
        "M0_Ed_kNm": M0Ed,
        "dupla_curvatura": r_m < 0.0,
    }

def _html_substituicao(*linhas):
    """Formata a substituição numérica mostrada depois da fórmula."""
    return "<br>".join(str(l) for l in linhas)


def _substituicao_area_armadura(solucao):
    """Produz a substituição numérica da área da combinação selecionada."""
    termos = []
    for phi, qtd in sorted(solucao.get("counts", {}).items()):
        phi = float(phi)
        termos.append(f"{int(qtd)} × (π × {phi:g}² / 4)")
    expressao = " + ".join(termos) if termos else "ΣAφ"
    area_mm2 = solucao["area_total_cm2"] * 100.0
    return (
        f"A_s,prov = {expressao} = {area_mm2:.2f} mm² "
        f"= {solucao['area_total_cm2']:.2f} cm²"
    )


def _detalhe_equilibrio_numerico(sec, b_mm, h_mm, f_cd, f_yd, N_Ed_kN):
    """Mostra a substituição numérica do equilíbrio N-M da secção adotada."""
    x = sec["x_mm"]
    bloco = sec["bloco_mm"]
    Cc_N = sec["Cc_N"]
    y_c = bloco / 2.0
    z_c = h_mm / 2.0 - y_c
    M_c_Nmm = Cc_N * z_c

    eps_c_top = float(sec.get("epsilon_c_top", EPSILON_CU2))
    regime = sec.get("regime_deformacao", "eixo_neutro_na_secao")

    linhas = [
        f"a_c = min(0,80 × x ; h) = min(0,80 × {x:.2f} ; {h_mm:.2f}) = {bloco:.2f} mm",
        f"C_c = η × f_cd × b × a_c = {ETA_BLOCO:.2f} × {f_cd:.2f} × {b_mm:.2f} × {bloco:.2f} = {Cc_N:.2f} N = {Cc_N/1000.0:.2f} kN",
    ]
    if regime == "secao_integralmente_comprimida":
        linhas.append(
            f"Como x = {x:.2f} mm > h = {h_mm:.2f} mm, "
            f"ε_c,max = 1,75‰ / [1 - h/(2x)] = {eps_c_top*1000.0:.3f}‰ "
            f"(ponto de charneira de 1,75‰ a h/2)."
        )
    else:
        linhas.append(
            f"Como x = {x:.2f} mm ≤ h = {h_mm:.2f} mm, "
            f"ε_c,max = ε_cu2 = {eps_c_top*1000.0:.3f}‰."
        )

    # Agrupar varões mecanicamente equivalentes (mesmo y, phi e tensão líquida).
    grupos = {}
    for e in sec["estados_barras"]:
        chave = (
            round(float(e["y_mm"]), 6),
            round(float(e["phi_mm"]), 6),
            round(float(e["epsilon_s"]), 12),
            round(float(e["sigma_s_mpa"]), 8),
            round(float(e["sigma_liquida_mpa"]), 8),
            round(float(e["F_s_N"]), 6),
        )
        grupos[chave] = grupos.get(chave, 0) + 1

    soma_F = 0.0
    soma_M = 0.0
    for idx, (chave, qtd) in enumerate(sorted(grupos.items(), key=lambda kv: kv[0][0]), start=1):
        y, phi, eps_s, sigma_s, sigma_liq, F_unit = chave
        A_i = math.pi * phi * phi / 4.0
        F_grupo = qtd * F_unit
        z_i = h_mm / 2.0 - y
        M_grupo = F_grupo * z_i
        soma_F += F_grupo
        soma_M += M_grupo
        linhas.append(
            f"Grupo de aço {idx}: {qtd} Ø {phi:g}, y = {y:.2f} mm; "
            f"ε_s = {eps_c_top*1000.0:.3f}‰ × (1 - {y:.2f}/{x:.2f}) = {eps_s*1000.0:.3f}‰; "
            f"σ_s = {sigma_s:.2f} MPa; σ_s,liq = {sigma_liq:.2f} MPa; "
            f"F_s = {qtd} × {A_i:.2f} × {sigma_liq:.2f} = {F_grupo:.2f} N = {F_grupo/1000.0:.2f} kN"
        )

    N_Rd = Cc_N + soma_F
    linhas.extend([
        f"ΣF_s = {soma_F:.2f} N = {soma_F/1000.0:.2f} kN",
        f"N_Rd = C_c + ΣF_s = {Cc_N:.2f} + ({soma_F:.2f}) = {N_Rd:.2f} N = {N_Rd/1000.0:.2f} kN ≈ N_Ed = {N_Ed_kN:.2f} kN",
        f"z_c = h/2 - a_c/2 = {h_mm:.2f}/2 - {bloco:.2f}/2 = {z_c:.2f} mm",
        f"M_c = C_c × z_c = {Cc_N:.2f} × {z_c:.2f} = {M_c_Nmm:.2f} Nmm",
        f"Σ(F_s z_i) = {soma_M:.2f} Nmm",
        f"M_Rd = M_c + Σ(F_s z_i) = {M_c_Nmm:.2f} + ({soma_M:.2f}) = {(M_c_Nmm+soma_M):.2f} Nmm = {(M_c_Nmm+soma_M)/1e6:.2f} kNm",
    ])
    return linhas


def desenhar_pilar_svg(dados_desenho):
    """Representação SVG da secção com os varões realmente selecionados."""
    b = float(dados_desenho.get("b", 300.0))
    h = float(dados_desenho.get("h", 400.0))
    c_nom = float(dados_desenho.get("c_nom", 30.0))
    phi_estribo = float(dados_desenho.get("phi_estribo", PHI_ESTRIBO_MM))
    posicoes = dados_desenho.get("posicoes", [])

    P = 60.0
    svg = (
        f'<svg width="100%" viewBox="0 0 {b+2*P} {h+2*P}" '
        'xmlns="http://www.w3.org/2000/svg">'
    )
    svg += (
        '<style>.dim-text{font-family:Arial,sans-serif;font-size:14px;fill:#333;'
        'text-anchor:middle}.bar-text{font-family:Arial,sans-serif;font-size:10px;'
        'fill:#444;text-anchor:middle}</style>'
    )
    svg += f'<rect x="{P}" y="{P}" width="{b}" height="{h}" fill="#e0e0e0" stroke="#555" stroke-width="2"/>'

    ex, ey = P + c_nom, P + c_nom
    ew, eh = b - 2*c_nom, h - 2*c_nom
    svg += (
        f'<rect x="{ex}" y="{ey}" width="{ew}" height="{eh}" fill="none" '
        f'stroke="#777" stroke-width="{max(phi_estribo/2,2)}" '
        f'rx="{2*phi_estribo}" ry="{2*phi_estribo}"/>'
    )

    for p in posicoes:
        x = P + float(p["x_mm"])
        y = P + float(p["y_mm"])
        phi = float(p["phi_mm"])
        svg += (
            f'<circle cx="{x}" cy="{y}" r="{phi/2}" '
            f'fill="#e53935" stroke="#b71c1c" stroke-width="1.4" '
            f'data-phi="{phi:g}"/>'
        )

    svg += (
        f'<path d="M {P/4} {P} L {3*P/4} {P} M {P/2} {P} L {P/2} {P+h} '
        f'M {P/4} {P+h} L {3*P/4} {P+h}" stroke="#333" stroke-width="1" fill="none"/>'
    )
    svg += f'<text x="{P/2-10}" y="{P+h/2}" class="dim-text" transform="rotate(-90,{P/2-10},{P+h/2})">{h:g}</text>'
    svg += (
        f'<path d="M {P} {P/4} L {P} {3*P/4} M {P} {P/2} L {P+b} {P/2} '
        f'M {P+b} {P/4} L {P+b} {3*P/4}" stroke="#333" stroke-width="1" fill="none"/>'
    )
    svg += f'<text x="{P+b/2}" y="{P/2-10}" class="dim-text">{b:g}</text>'
    svg += '</svg>'
    return svg



def _classificar_modo_rotura_pilar(sec, h_mm, f_yd):
    """Classifica convencionalmente o estado resistente final da secção.

    A análise resistente usa epsilon_cu2 = 3,5 por mil quando x <= h e,
    para x > h, ajusta epsilon_c,max pelo ponto de charneira de 1,75 por mil
    a meia altura. A classificação abaixo descreve o estado de deformação da
    armadura longitudinal nesse ponto de equilíbrio. Não representa uma
    verificação de rotura física do aço, pois epsilon_ud não integra o modelo.
    """
    eps_yd = f_yd / E_S_MPA
    estados = sec.get("estados_barras", [])
    tol = 1e-12

    eps_tensao = [
        -float(e["epsilon_s"])
        for e in estados
        if float(e["epsilon_s"]) < -tol
    ]
    eps_comp = [
        float(e["epsilon_s"])
        for e in estados
        if float(e["epsilon_s"]) > tol
    ]

    eps_t_max = max(eps_tensao, default=0.0)
    eps_c_aco_max = max(eps_comp, default=0.0)
    x_mm = float(sec.get("x_mm", 0.0))

    if eps_tensao:
        if eps_t_max >= eps_yd - tol:
            return {
                "grupo": "betao_com_aco_tracionado_em_cedencia",
                "designacao": "Betão no limite último com armadura tracionada em cedência",
                "descricao": (
                    f"A fibra comprimida do betão é considerada em εc,max = {float(sec.get('epsilon_c_top', EPSILON_CU2))*1000.0:.3f} ‰ e "
                    "pelo menos um grupo de varões tracionados apresenta |εs| ≥ εyd. "
                    "Trata-se de uma classificação convencional do estado resistente; "
                    "εud do aço não é utilizado nesta implementação."
                ),
                "epsilon_s_tracao_max": eps_t_max,
                "epsilon_s_compressao_max": eps_c_aco_max,
            }
        return {
            "grupo": "betao_com_aco_tracionado_elastico",
            "designacao": "Betão no limite último com armadura tracionada em regime elástico",
            "descricao": (
                f"A fibra comprimida do betão é considerada em εc,max = {float(sec.get('epsilon_c_top', EPSILON_CU2))*1000.0:.3f} ‰ e "
                "a armadura longitudinal tracionada permanece com |εs| < εyd. "
                "O estado corresponde a uma resposta convencional menos dúctil."
            ),
            "epsilon_s_tracao_max": eps_t_max,
            "epsilon_s_compressao_max": eps_c_aco_max,
        }

    if x_mm >= h_mm - 1e-9:
        designacao = "Betão no limite último com secção integralmente comprimida"
        descricao = (
            "O eixo neutro encontra-se fora ou no limite inferior da secção e todos "
            "os grupos de armadura longitudinal estão comprimidos. Para x > h, "
            "εc,max é ajustada pelo ponto de charneira de 1,75 ‰ a meia altura."
        )
        grupo = "secao_integralmente_comprimida"
    else:
        designacao = "Betão no limite último sem armadura longitudinal tracionada"
        descricao = (
            "No estado resistente calculado não existem varões longitudinais em tração, "
            "embora o eixo neutro ainda intersete a secção."
        )
        grupo = "sem_armadura_tracionada"

    return {
        "grupo": grupo,
        "designacao": designacao,
        "descricao": descricao,
        "epsilon_s_tracao_max": 0.0,
        "epsilon_s_compressao_max": eps_c_aco_max,
    }


def gerar_graficos_materiais_svg(f_ck, f_cd, f_yd, E_s, epsilon_c,
                                 epsilon_st=0.0, epsilon_sc=None, marcadores_aco=None):
    """Estado resistente final, não estado de serviço sob MEd.

    A curva parábola-retângulo é apenas uma referência para fck <= 50 MPa.
    O equilíbrio resistente continua a usar o bloco retangular equivalente.
    Não se apresenta extrapolação para fck > 50 MPa, porque essas classes
    estão fora do âmbito do modelo implementado nesta versão.
    """
    from html import escape

    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="100%" '
           'viewBox="0 0 760 390" role="img" '
           'aria-label="Estado limite resistente: gráficos dos materiais">']

    out.append('<rect width="760" height="390" fill="white"/>')

    def text(x, y, value, size=13, color='#243447'):
        out.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" '
                   f'font-size="{size}" fill="{color}">{escape(value)}</text>')

    def line(x1, y1, x2, y2, color='#64748b', dashed=False):
        dash = ' stroke-dasharray="4 4"' if dashed else ''
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                   f'stroke="{color}"{dash}/>')

    def panel(left, title, xmax, ymax, points, markers, references):
        text(left, 27, title, 16)
        ox, oy, w, ht = left + 42, 235, 265, 157
        def xy(e, s):
            return ox + w * e / xmax, oy - ht * s / ymax
        line(ox, oy, ox + w + 10, oy)
        line(ox, oy, ox, oy - ht - 15)
        text(ox - 34, oy - ht - 22, '|σ| (MPa)', 12)
        text(ox + w - 20, oy + 18, '|ε| (‰)', 12)
        text(ox - 12, oy + 16, '0', 11)
        if points:
            coords = ' '.join(f'{x:.3f},{y:.3f}' for x, y in
                              (xy(e, s) for e, s in points))
            out.append(f'<polyline points="{coords}" fill="none" '
                       'stroke="#334155" stroke-width="2.5"/>')
        for e, subscript, value in references:
            px, _ = xy(e, 0)
            line(px, oy, px, oy - ht, '#94a3b8', True)
            out.append(
                f'<text x="{px}" y="{oy + 16}" text-anchor="middle" '
                'font-family="Arial,sans-serif" font-size="12" fill="#243447">'
                f'ε<tspan baseline-shift="sub" font-size="9">{subscript}</tspan>'
                f'<tspan x="{px}" dy="16">{value} ‰</tspan></text>'
            )
        for i, (e, s, label, color) in enumerate(markers):
            px, py = xy(e, s)
            line(ox, py, px, py, color, True)
            line(px, oy, px, py, color, True)
            # Hollow compression marker remains distinguishable if points overlap.
            radius = 7 if i else 4
            fill = 'none' if i else color
            out.append(f'<circle cx="{px}" cy="{py}" r="{radius}" '
                       f'fill="{fill}" stroke="{color}" stroke-width="2"/>')
            text(left, 296 + i * 23,
                 f'{label}: {e * 1000:.3f} ‰; {s:.2f} MPa', 12, color)

    if f_ck <= 50:
        eps_c2 = EPSILON_C2
        concrete = [(eps_c2 * i / 40,
                     f_cd * (1 - (1 - i / 40) ** 2)) for i in range(41)]
        concrete.append((EPSILON_CU2, f_cd))
        if epsilon_c <= eps_c2:
            razao = max(0.0, min(1.0, epsilon_c / eps_c2))
            sigma_c_ref = f_cd * (1.0 - (1.0 - razao) ** 2)
        else:
            sigma_c_ref = f_cd
        panel(18, 'Betão — referência teórica', 0.0042, f_cd * 1.2,
              concrete, [(epsilon_c, sigma_c_ref, 'Fibra superior', '#0f766e')],
              [(eps_c2, 'c2', '2,0'), (EPSILON_CU2, 'cu2', '3,5')])
    else:
        text(18, 27, 'Betão — referência indisponível', 16)
        text(18, 110, 'fck > 50 MPa: rever os parâmetros do modelo.')
        text(18, 135, 'Não se apresenta uma curva extrapolada.')
        text(18, 296, f'Extensão usada no cálculo: {epsilon_c*1000:.3f} ‰', 12)

    eps_yd = f_yd / E_s

    # Os marcadores podem ser fornecidos explicitamente para refletir o estado
    # real da armadura. Isto evita identificar como "tração" um varão que, em
    # secções integralmente comprimidas, está apenas menos comprimido.
    if marcadores_aco is not None:
        markers = []
        for i, m in enumerate(marcadores_aco):
            e = max(0.0, float(m.get("epsilon", 0.0)))
            label = str(m.get("label", "Aço"))
            color = str(m.get("color", '#2563eb' if i == 0 else '#c2410c'))
            markers.append((e, min(E_s * e, f_yd), label, color))
        max_eps_aco = max((m[0] for m in markers), default=0.0)
    else:
        # Compatibilidade com chamadas anteriores.
        markers = [(epsilon_st, min(E_s * epsilon_st, f_yd),
                    'Tração (ponto cheio)', '#2563eb')]
        if epsilon_sc is not None:
            markers.append((epsilon_sc, min(E_s * epsilon_sc, f_yd),
                            'Compressão (círculo)', '#c2410c'))
        max_eps_aco = max(epsilon_st, epsilon_sc or 0.0)

    end = 1.2 * max(max_eps_aco, eps_yd)
    panel(398, 'Aço — modelo do cálculo', end, f_yd * 1.2,
          [(0, 0), (eps_yd, f_yd), (end, f_yd)], markers,
          [(eps_yd, 'yd', f'{eps_yd * 1000:.3f}'.replace('.', ','))])
    text(18, 352, 'Estado resistente em MRd; valores em módulo. Não representa o estado sob MEd.', 12)
    text(18, 372, 'Betão: curva de referência; equilíbrio pelo bloco retangular equivalente. Aço: patamar sem limite εud definido.', 12)
    out.append('</svg>')
    return ''.join(out)

def gerar_diagrama_extensoes_pilar_svg(h_mm, sec, f_yd, modo_rotura):
    """Gera o diagrama linear de extensões do estado resistente final do pilar.

    Convenção gráfica:
      - compressão à esquerda do eixo ε = 0;
      - tração à direita;
      - εc,max = 3,5 ‰ para x <= h; para x > h, valor ajustado pelo ponto de charneira;
      - extensões reais dos grupos de varões posicionadas ao longo da altura.
    """
    h_mm = float(h_mm)
    x_mm = float(sec.get("x_mm", 0.0))
    estados = sec.get("estados_barras", [])
    if h_mm <= 0 or x_mm <= 0 or not estados:
        return ""

    eps_yd = float(f_yd) / E_S_MPA
    eps_top = float(sec.get("epsilon_c_top", _epsilon_c_max_pilar(x_mm, h_mm)[0]))
    eps_bottom = float(sec.get("epsilon_c_bottom", eps_top * (1.0 - h_mm / x_mm)))

    # Agrupar varões que ocupam a mesma cota e apresentam a mesma extensão.
    grupos = {}
    for e in estados:
        key = (round(float(e["y_mm"]), 6), round(float(e["epsilon_s"]), 12))
        g = grupos.setdefault(key, {"y_mm": float(e["y_mm"]), "epsilon_s": float(e["epsilon_s"]), "barras": []})
        g["barras"].append(float(e["phi_mm"]))
    grupos = [grupos[k] for k in sorted(grupos)]

    all_eps = [eps_top, eps_bottom, eps_yd, -eps_yd]
    all_eps.extend(float(g["epsilon_s"]) for g in grupos)
    eps_max = max(abs(v) for v in all_eps) if all_eps else eps_top
    eps_max = max(eps_max, 1e-9)

    width, height = 820, 450
    top, bottom = 62, 365
    sec_x = 155
    axis_x = 420
    label_x = 575
    geom_h = bottom - top
    scale = 165.0 / eps_max

    def y_plot(y_mm):
        return top + geom_h * (float(y_mm) / h_mm)

    def x_plot(eps):
        # epsilon positivo = compressão -> esquerda; negativo = tração -> direita.
        return axis_x - float(eps) * scale

    def esc(txt):
        return (str(txt).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

    out = [f'<svg width="100%" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagrama de extensões do pilar">']
    out.append('<rect width="820" height="450" fill="white"/>')
    out.append('<style>.t{font-family:Arial,sans-serif;font-size:14px;fill:#222}.s{font-family:Arial,sans-serif;font-size:12px;fill:#555}.b{font-family:Arial,sans-serif;font-size:14px;font-weight:700;fill:#222}</style>')

    # Secção esquemática.
    out.append(f'<rect x="{sec_x-36}" y="{top}" width="72" height="{geom_h}" fill="#efefef" stroke="#555" stroke-width="2"/>')
    if x_mm < h_mm:
        yn = y_plot(x_mm)
        out.append(f'<line x1="{sec_x-46}" y1="{yn}" x2="{sec_x+46}" y2="{yn}" stroke="#777" stroke-dasharray="5,4"/>')
        out.append(f'<text x="{sec_x+55}" y="{yn+5}" class="s">eixo neutro, x = {x_mm:.1f} mm</text>')
    else:
        out.append(f'<text x="{sec_x-45}" y="{bottom+24}" class="s">eixo neutro exterior, x = {x_mm:.1f} mm</text>')
    out.append(f'<text x="{sec_x-48}" y="{top-15}" class="s">fibra comprimida</text>')
    out.append(f'<text x="{sec_x-36}" y="{bottom+45}" class="s">h = {h_mm:.1f} mm</text>')

    # Eixo de deformações e orientação.
    out.append(f'<line x1="{axis_x}" y1="{top-20}" x2="{axis_x}" y2="{bottom+20}" stroke="#444" stroke-width="1.5"/>')
    out.append(f'<text x="{axis_x-26}" y="{top-29}" class="s">ε = 0</text>')
    out.append(f'<text x="{axis_x-156}" y="{bottom+42}" class="s">compressão ←</text>')
    out.append(f'<text x="{axis_x+46}" y="{bottom+42}" class="s">→ tração</text>')

    # Limites ± epsilon_yd.
    xcyd = x_plot(eps_yd)
    xtyd = x_plot(-eps_yd)
    for xx in (xcyd, xtyd):
        out.append(f'<line x1="{xx}" y1="{top+5}" x2="{xx}" y2="{bottom}" stroke="#94a3b8" stroke-dasharray="4,4"/>')
    out.append(f'<text x="{xcyd-8}" y="{top+18}" text-anchor="end" class="s">+εyd</text>')
    out.append(f'<text x="{xtyd+8}" y="{top+18}" class="s">−εyd</text>')

    # Distribuição linear de deformações do betão.
    xtop = x_plot(eps_top)
    xbot = x_plot(eps_bottom)
    out.append(f'<line x1="{xtop}" y1="{top}" x2="{xbot}" y2="{bottom}" stroke="#111" stroke-width="3"/>')
    out.append(f'<circle cx="{xtop}" cy="{top}" r="4" fill="#111"/>')
    out.append(f'<circle cx="{xbot}" cy="{bottom}" r="4" fill="#111"/>')
    if x_mm < h_mm:
        yn = y_plot(x_mm)
        out.append(f'<circle cx="{axis_x}" cy="{yn}" r="4" fill="#111"/>')

    # Grupos de armadura.
    label_y = top + 95
    for idx, g in enumerate(grupos, 1):
        yy = y_plot(g["y_mm"])
        eps = g["epsilon_s"]
        xx = x_plot(eps)
        cor = '#c2410c' if eps > 1e-12 else ('#2563eb' if eps < -1e-12 else '#64748b')
        out.append(f'<circle cx="{xx}" cy="{yy}" r="5" fill="{cor}" stroke="white" stroke-width="1.5"/>')
        out.append(f'<line x1="{axis_x}" y1="{yy}" x2="{xx}" y2="{yy}" stroke="{cor}" stroke-dasharray="3,3"/>')
        n = len(g["barras"])
        phis = sorted(set(g["barras"]))
        if len(phis) == 1:
            barras_txt = f'{n}Ø{phis[0]:g}'
        else:
            barras_txt = f'{n} varões'
        sinal = 'C' if eps > 1e-12 else ('T' if eps < -1e-12 else '0')
        out.append(f'<text x="{label_x}" y="{label_y + (idx-1)*27}" class="s">{esc(barras_txt)} a y={g["y_mm"]:.1f} mm: εs={eps*1000.0:.3f} ‰ ({sinal})</text>')

    out.append(f'<text x="{label_x}" y="{top+8}" class="t">εcu2 = {EPSILON_CU2*1000.0:.3f} ‰</text>')
    out.append(f'<text x="{label_x}" y="{top+35}" class="t">εyd = {eps_yd*1000.0:.3f} ‰</text>')
    out.append(f'<text x="{label_x}" y="{top+62}" class="t">x = {x_mm:.2f} mm</text>')
    out.append('</svg>')
    return ''.join(out)

def dimensionar_pilar(
    b_mm,
    h_mm,
    l_m,
    cond_ligacao,
    f_ck,
    f_yk,
    N_Ed_kN,
    M_Ed_kNm,
    c_nom_mm,
    usar_l0_manual=False,
    l0_manual_m=None,
    considerar_fluencia=False,
    phi_ef=None,
    usar_momentos_extremidade=False,
    M_01_kNm=None,
    M_02_kNm=None,
):
    """
    Dimensionamento de pilar retangular em flexão composta reta.

    Por defeito, a interface mantém o modo simples com um único momento de
    1.ª ordem. Nesse modo preserva-se M01 = M02 = M0Ed, r_m = 1 e C = 0,70.

    Opcionalmente podem ser introduzidos os momentos de extremidade M01 e M02
    com sinal. Nesse modo, a aplicação preserva a relação de curvatura, calcula
    r_m = M01/M02 e C = 1,7-r_m, e usa o momento equivalente M0e e a expressão
    de combinação com M2 para pilares esbeltos.

    A imperfeição geométrica e_i = l0/400 e a excentricidade mínima
    e_0 = max(h/30, 20 mm) são verificadas sem duplicar M_i.

    O comprimento efetivo pode ser obtido por um fator idealizado associado
    às condições de ligação ou introduzido diretamente pelo utilizador.
    A fluência é opcional: quando desativada, phi_ef = 0 e K_phi = 1.
    """
    l0_m, beta_l0, descricao_l0 = _resolver_comprimento_efetivo(
        l_m=l_m,
        cond_ligacao=cond_ligacao,
        usar_l0_manual=usar_l0_manual,
        l0_manual_m=l0_manual_m,
    )
    phi_ef_usado = _resolver_fluencia(
        considerar_fluencia=considerar_fluencia,
        phi_ef=phi_ef,
    )

    usar_momentos_extremidade = bool(usar_momentos_extremidade)
    M_Ed_validacao = 0.0 if usar_momentos_extremidade else M_Ed_kNm
    _validar_entradas(
        b_mm, h_mm, l0_m, f_ck, f_yk,
        N_Ed_kN, M_Ed_validacao, c_nom_mm,
    )

    if usar_momentos_extremidade:
        if M_01_kNm is None or M_02_kNm is None:
            raise ValueError(
                "Indique M_01 e M_02 quando a opção de momentos distintos nas extremidades está ativa."
            )
        M_01_kNm = float(M_01_kNm)
        M_02_kNm = float(M_02_kNm)
        if not (math.isfinite(M_01_kNm) and math.isfinite(M_02_kNm)):
            raise ValueError("M_01 e M_02 devem ser valores finitos.")

    b_mm = float(b_mm)
    h_mm = float(h_mm)
    l_m = None if usar_l0_manual else float(l_m)
    l0_m = float(l0_m)
    f_ck = float(f_ck)
    f_yk = float(f_yk)
    N_Ed_kN = float(N_Ed_kN)
    M_Ed_kNm = 0.0 if usar_momentos_extremidade else float(M_Ed_kNm)
    c_nom_mm = float(c_nom_mm)

    f_cd, f_yd, Ac, i_mm, lamb, N_Ed_N, n = _propriedades_basicas(
        b_mm, h_mm, l0_m, f_ck, f_yk, N_Ed_kN
    )

    imperfeicao = _calcular_imperfeicao_geometrica(
        l0_m=l0_m,
        h_mm=h_mm,
        N_Ed_kN=N_Ed_kN,
        M_Ed_kNm=M_Ed_kNm,
    )

    if usar_momentos_extremidade:
        momentos = _preparar_momentos_extremidade(
            M_01_kNm=M_01_kNm,
            M_02_kNm=M_02_kNm,
            M_i_kNm=imperfeicao["M_i_kNm"],
            M_min_kNm=imperfeicao["M_min_kNm"],
        )
        M0_Ed_kNm = momentos["M0_Ed_kNm"]
        C_usado = momentos["C"]
        M01_usado = momentos["M01_kNm"]
        M02_usado = momentos["M02_kNm"]
    else:
        M0_Ed_kNm = imperfeicao["M0_Ed_kNm"]
        C_usado = C_ESBELTEZA
        M01_usado = M0_Ed_kNm
        M02_usado = M0_Ed_kNm
        momentos = {
            "M_01_entrada_kNm": M_Ed_kNm,
            "M_02_entrada_kNm": M_Ed_kNm,
            "M01_kNm": M01_usado,
            "M02_kNm": M02_usado,
            "r_m": 1.0,
            "C": C_usado,
            "M0e_kNm": M0_Ed_kNm,
            "M0_Ed_kNm": M0_Ed_kNm,
            "dupla_curvatura": False,
        }

    Asmin1, Asmin2, Asmin, Asmax = _limites_armadura(Ac, N_Ed_N, f_yd)

    if Asmin > Asmax:
        raise ValueError(
            "A armadura mínima ultrapassa 4% da área da secção. "
            "Recomenda-se aumentar a secção."
        )

    candidatas = armadura_service.gerar_combinacoes_pilar(
        b_mm=b_mm,
        h_mm=h_mm,
        c_nom_mm=c_nom_mm,
        phi_estribo_mm=PHI_ESTRIBO_MM,
        dg_mm=DG_MM,
    )
    candidatas = [
        c for c in candidatas
        if c["area_total_cm2"] * 100.0 + 1e-9 >= Asmin
        and c["area_total_cm2"] * 100.0 <= Asmax + 1e-9
    ]
    if not candidatas:
        raise ValueError(
            "Não existem combinações de armadura compatíveis com a geometria "
            "e os limites adotados."
        )

    validas = []
    for c in candidatas:
        r = _avaliar_candidata(
            c, b_mm, h_mm, l0_m, f_ck, f_cd, f_yd, Ac, n, lamb,
            N_Ed_N, M0_Ed_kNm, phi_ef_usado,
            C_esbelteza=C_usado,
            usar_momentos_extremidade=usar_momentos_extremidade,
            M01_kNm=M01_usado,
            M02_kNm=M02_usado,
            M_min_kNm=imperfeicao["M_min_kNm"],
        )
        if r is not None:
            validas.append(r)

    if not validas:
        raise ValueError(
            "Não foi encontrada uma combinação que satisfaça simultaneamente "
            "a estabilidade, o equilíbrio N-M, os limites de armadura e a geometria. "
            "Recomenda-se redimensionar a secção."
        )

    validas.sort(key=_criterio)
    melhor = validas[0]
    unicas = [s for s in validas if s["n_diametros"] == 1]
    mistas = [s for s in validas if s["n_diametros"] > 1]
    melhor_unica = min(unicas, key=_criterio) if unicas else None
    melhor_mista = min(mistas, key=_criterio) if mistas else None

    est = melhor["estabilidade"]
    sec = melhor["estado_secao"]

    modo_rotura = _classificar_modo_rotura_pilar(sec, h_mm, f_yd)
    epsilon_yd_final = f_yd / E_S_MPA

    # Gráfico único apresentado ao utilizador: estado limite resistente dos materiais.
    # As extensões do aço correspondem ao estado resistente final da secção adotada.
    eps_assinadas = [
        float(e["epsilon_s"])
        for e in sec.get("estados_barras", [])
    ]
    eps_tensao = [-e for e in eps_assinadas if e < -1e-12]
    eps_compressao = [e for e in eps_assinadas if e > 1e-12]

    marcadores_aco = []
    if eps_tensao and eps_compressao:
        # Flexão composta com armadura em ambos os regimes.
        marcadores_aco = [
            {
                "epsilon": max(eps_tensao),
                "label": "Tração (ponto cheio)",
                "color": "#2563eb",
            },
            {
                "epsilon": max(eps_compressao),
                "label": "Compressão (círculo)",
                "color": "#c2410c",
            },
        ]
    elif eps_compressao:
        # Secção integralmente comprimida: não chamar "tração" ao grupo
        # de menor deformação. Mostrar os dois extremos de compressão.
        eps_min = min(eps_compressao)
        eps_max = max(eps_compressao)
        if abs(eps_max - eps_min) <= 1e-12:
            marcadores_aco = [{
                "epsilon": eps_max,
                "label": "Aço comprimido",
                "color": "#c2410c",
            }]
        else:
            marcadores_aco = [
                {
                    "epsilon": eps_min,
                    "label": "Aço menos comprimido (ponto cheio)",
                    "color": "#2563eb",
                },
                {
                    "epsilon": eps_max,
                    "label": "Aço mais comprimido (círculo)",
                    "color": "#c2410c",
                },
            ]
    elif eps_tensao:
        # Caso limite pouco usual: todos os grupos em tração.
        eps_min = min(eps_tensao)
        eps_max = max(eps_tensao)
        if abs(eps_max - eps_min) <= 1e-12:
            marcadores_aco = [{
                "epsilon": eps_max,
                "label": "Aço tracionado",
                "color": "#2563eb",
            }]
        else:
            marcadores_aco = [
                {
                    "epsilon": eps_min,
                    "label": "Aço menos tracionado (ponto cheio)",
                    "color": "#2563eb",
                },
                {
                    "epsilon": eps_max,
                    "label": "Aço mais tracionado (círculo)",
                    "color": "#c2410c",
                },
            ]
    else:
        marcadores_aco = [{
            "epsilon": 0.0,
            "label": "Aço sem extensão longitudinal",
            "color": "#2563eb",
        }]

    graficos_materiais_svg = gerar_graficos_materiais_svg(
        f_ck=f_ck,
        f_cd=f_cd,
        f_yd=f_yd,
        E_s=E_S_MPA,
        epsilon_c=float(sec.get("epsilon_c_top", EPSILON_CU2)),
        marcadores_aco=marcadores_aco,
    )

    passos = []

    # 1. Comprimento efetivo
    if usar_l0_manual:
        formula_l0 = r"l_0=l_{0,manual}"
        calculo_l0 = _html_substituicao(
            f"Comprimento efetivo introduzido manualmente: l₀ = {l0_m:.3f} m",
        )
    else:
        formula_l0 = r"l_0=\beta\,l"
        calculo_l0 = _html_substituicao(
            f"Condição de ligação = {descricao_l0}",
            f"β = {beta_l0:.2f}",
            f"l₀ = β × l = {beta_l0:.2f} × {l_m:.3f} = {l0_m:.3f} m",
        )

    passos.append(_passo(
        "1. Comprimento efetivo de encurvadura",
        formula_l0,
        calculo_l0,
    ))

    # 2. Materiais
    passos.append(_passo(
        "2. Resistências de cálculo dos materiais",
        r"f_{cd}=\frac{\alpha_{cc}f_{ck}}{\gamma_c}\ ;\ f_{yd}=\frac{f_{yk}}{\gamma_s}",
        _html_substituicao(
            f"f_cd = (α_cc × f_ck) / γ_c = ({ALPHA_CC:.2f} × {f_ck:.2f}) / {GAMMA_C:.2f} = {f_cd:.2f} MPa",
            f"f_yd = f_yk / γ_s = {f_yk:.2f} / {GAMMA_S:.2f} = {f_yd:.2f} MPa",
        )
    ))

    # 3. Geometria e esbelteza
    passos.append(_passo(
        "3. Área da secção, raio de giração e esbelteza",
        r"A_c=bh\ ;\ i=\frac{h}{\sqrt{12}}\ ;\ \lambda=\frac{l_0}{i}",
        _html_substituicao(
            f"A_c = b × h = {b_mm:.2f} × {h_mm:.2f} = {Ac:.2f} mm²",
            f"i = h / √12 = {h_mm:.2f} / √12 = {i_mm:.2f} mm",
            f"λ = l₀ / i = {l0_m*1000.0:.2f} / {i_mm:.2f} = {lamb:.2f}",
        )
    ))

    # 4 e 5. Momentos de primeira ordem e hipóteses de estabilidade
    fluencia_linha = (
        f"φ_ef = {phi_ef_usado:.3f} (fluência considerada)"
        if considerar_fluencia
        else "φ_ef = 0,000 e K_φ = 1,000 (fluência não considerada)"
    )

    if usar_momentos_extremidade:
        passos.append(_passo(
            "4. Momentos de extremidade, imperfeição geométrica e excentricidade mínima",
            (
                r"e_i=\frac{l_0}{400}\ ;\ M_i=N_{Ed}e_i\ ;\ "
                r"M_{01}=M_{01,an}+M_i\ ;\ M_{02}=M_{02,an}+M_i\ ;\ "
                r"e_0=\max\left(\frac{h}{30}\ ;\ 20\right)\ ;\ "
                r"M_{min}=N_{Ed}e_0"
            ),
            _html_substituicao(
                f"Momentos da análise introduzidos: M_01 = {momentos['M_01_entrada_kNm']:.2f} kNm ; M_02 = {momentos['M_02_entrada_kNm']:.2f} kNm",
                f"Orientação adotada: |M_02,an| ≥ |M_01,an|, com M_01,an = {momentos['M01_analise_kNm']:.2f} kNm e M_02,an = {momentos['M02_analise_kNm']:.2f} kNm",
                f"e_i = l₀/400 = {l0_m*1000.0:.2f} / 400 = {imperfeicao['e_i_mm']:.2f} mm",
                f"M_i = N_Ed × e_i = {N_Ed_kN:.2f} × {imperfeicao['e_i_mm']/1000.0:.5f} = {imperfeicao['M_i_kNm']:.2f} kNm",
                f"M_01 = M_01,an + M_i = {momentos['M01_analise_kNm']:.2f} + {imperfeicao['M_i_kNm']:.2f} = {momentos['M01_kNm']:.2f} kNm",
                f"M_02 = M_02,an + M_i = {momentos['M02_analise_kNm']:.2f} + {imperfeicao['M_i_kNm']:.2f} = {momentos['M02_kNm']:.2f} kNm",
                f"h/30 = {h_mm:.2f} / 30 = {imperfeicao['e_h_mm']:.2f} mm",
                f"e_0 = max(h/30 ; 20,00) = max({imperfeicao['e_h_mm']:.2f} ; 20,00) = {imperfeicao['e0_mm']:.2f} mm",
                f"M_min = N_Ed × e_0 = {N_Ed_kN:.2f} × {imperfeicao['e0_mm']/1000.0:.5f} = {imperfeicao['M_min_kNm']:.2f} kNm",
            )
        ))

        passos.append(_passo(
            "5. Distribuição dos momentos e parâmetro C",
            (
                r"r_m=\frac{M_{01,an}}{M_{02,an}}\ ;\ C=1.7-r_m\ ;\ "
                r"M_{0e}=\max(0.6M_{02}+0.4M_{01}\ ;\ 0.4M_{02})"
            ),
            _html_substituicao(
                f"r_m = M_01,an / M_02,an = {momentos['M01_analise_kNm']:.2f} / {momentos['M02_analise_kNm']:.2f} = {momentos['r_m']:.4f}",
                f"C = 1,7 - r_m = 1,7 - ({momentos['r_m']:.4f}) = {momentos['C']:.4f}",
                f"M_0e = max(0,6 × {momentos['M02_kNm']:.2f} + 0,4 × ({momentos['M01_kNm']:.2f}) ; 0,4 × {momentos['M02_kNm']:.2f}) = {momentos['M0e_kNm']:.2f} kNm",
                fluencia_linha,
            )
        ))
    else:
        passos.append(_passo(
            "4. Imperfeição geométrica, excentricidade mínima e momento de primeira ordem adotado",
            r"e_i=\frac{l_0}{400}\ ;\ M_i=N_{Ed}e_i\ ;\ M_1=M_{Ed}+M_i\ ;\ e_0=\max\left(\frac{h}{30}\ ;\ 20\right)\ ;\ M_{min}=N_{Ed}e_0\ ;\ M_{0Ed}=\max(M_1,M_{min})",
            _html_substituicao(
                f"e_i = l₀/400 = {l0_m*1000.0:.2f} / 400 = {imperfeicao['e_i_mm']:.2f} mm",
                f"M_i = N_Ed × e_i = {N_Ed_kN:.2f} × {imperfeicao['e_i_mm']/1000.0:.5f} = {imperfeicao['M_i_kNm']:.2f} kNm",
                f"M_1 = M_Ed + M_i = {M_Ed_kNm:.2f} + {imperfeicao['M_i_kNm']:.2f} = {imperfeicao['M1_Ed_kNm']:.2f} kNm",
                f"h/30 = {h_mm:.2f} / 30 = {imperfeicao['e_h_mm']:.2f} mm",
                f"e_0 = max(h/30 ; 20,00) = max({imperfeicao['e_h_mm']:.2f} ; 20,00) = {imperfeicao['e0_mm']:.2f} mm",
                f"M_min = N_Ed × e_0 = {N_Ed_kN:.2f} × {imperfeicao['e0_mm']/1000.0:.5f} = {imperfeicao['M_min_kNm']:.2f} kNm",
                f"M_0Ed = max(M_1 ; M_min) = max({imperfeicao['M1_Ed_kNm']:.2f} ; {imperfeicao['M_min_kNm']:.2f}) = {M0_Ed_kNm:.2f} kNm",
            )
        ))

        passos.append(_passo(
            "5. Hipóteses da análise de estabilidade",
            r"M_{01}=M_{02}=M_{0Ed}\ ;\ r_m=\frac{M_{01}}{M_{02}}\ ;\ C=1.7-r_m",
            _html_substituicao(
                f"M_01 = M_02 = M_0Ed = {M0_Ed_kNm:.2f} kNm",
                f"r_m = M_01 / M_02 = {M0_Ed_kNm:.2f} / {M0_Ed_kNm:.2f} = 1,000",
                f"C = 1,7 - r_m = 1,7 - 1,000 = {C_ESBELTEZA:.2f}",
                fluencia_linha,
            )
        ))

    # 6. Limites de armadura
    passos.append(_passo(
        "6. Limites da armadura longitudinal",
        r"A_{s,min}=\max\left(0.10\frac{N_{Ed}}{f_{yd}}\ ;\ 0.002A_c\right)\ ;\ A_{s,max}=0.04A_c",
        _html_substituicao(
            f"A_s,min,1 = 0,10 × N_Ed / f_yd = 0,10 × {N_Ed_N:.2f} / {f_yd:.2f} = {Asmin1:.2f} mm²",
            f"A_s,min,2 = 0,002 × A_c = 0,002 × {Ac:.2f} = {Asmin2:.2f} mm²",
            f"A_s,min = max({Asmin1:.2f} ; {Asmin2:.2f}) = {Asmin:.2f} mm² = {Asmin/100.0:.2f} cm²",
            f"A_s,max = 0,04 × A_c = 0,04 × {Ac:.2f} = {Asmax:.2f} mm² = {Asmax/100.0:.2f} cm²",
        )
    ))

    # 7. Esbelteza limite da solução selecionada
    passos.append(_passo(
        "7. Esbelteza limite da solução selecionada",
        r"n=\frac{N_{Ed}}{A_cf_{cd}}\ ;\ A=\frac{1}{1+0.2\phi_{ef}}\ ;\ \omega=\frac{A_sf_{yd}}{A_cf_{cd}}\ ;\ B=\sqrt{1+2\omega}\ ;\ \lambda_{lim}=\frac{20ABC}{\sqrt{n}}",
        _html_substituicao(
            f"n = N_Ed / (A_c × f_cd) = {N_Ed_N:.2f} / ({Ac:.2f} × {f_cd:.2f}) = {n:.4f}",
            f"A = 1 / (1 + 0,2φ_ef) = 1 / (1 + 0,2 × {phi_ef_usado:.3f}) = {est['A']:.4f}",
            f"A_s = {melhor['area_total_cm2']*100.0:.2f} mm²",
            f"ω = A_s f_yd / (A_c f_cd) = {melhor['area_total_cm2']*100.0:.2f} × {f_yd:.2f} / ({Ac:.2f} × {f_cd:.2f}) = {est['omega']:.4f}",
            f"B = √(1 + 2ω) = √(1 + 2 × {est['omega']:.4f}) = {est['B']:.4f}",
            f"C = {est['C']:.2f}",
            f"λ_lim = 20ABC / √n = 20 × {est['A']:.4f} × {est['B']:.4f} × {est['C']:.2f} / √{n:.4f} = {est['lambda_lim']:.2f}",
        )
    ))

    # 8. Classificação
    if est["esbelto"]:
        passos.append(_passo(
            "8. Classificação do pilar",
            r"\lambda>\lambda_{lim}\ ;\ M_2=N_{Ed}e_2",
            _html_substituicao(
                f"λ = {lamb:.2f}",
                f"λ_lim = {est['lambda_lim']:.2f}",
                f"{lamb:.2f} > {est['lambda_lim']:.2f} ⇒ pilar esbelto",
            )
        ))

        # 9. Curvatura nominal e segunda ordem
        eps_yd = f_yd / E_S_MPA
        passos.append(_passo(
            "9. Curvatura nominal e efeitos de segunda ordem",
            r"n_u=1+\omega\ ;\ K_r=\frac{n_u-n}{n_u-n_{bal}}\leq1\ ;\ \beta=0.35+\frac{f_{ck}}{200}-\frac{\lambda}{150}\ ;\ K_\phi=\max\left[1,1+\beta\phi_{ef}\right]\ ;\ \frac{1}{r_0}=\frac{\epsilon_{yd}}{0.45d}\ ;\ \frac{1}{r}=K_rK_\phi\frac{1}{r_0}\ ;\ e_2=\frac{(1/r)l_0^2}{10}\ ;\ M_2=N_{Ed}e_2",
            _html_substituicao(
                f"n_u = 1 + ω = 1 + {est['omega']:.4f} = {est['n_u']:.4f}",
                f"K_r = (n_u - n) / (n_u - n_bal) = ({est['n_u']:.4f} - {n:.4f}) / ({est['n_u']:.4f} - {N_BAL:.2f}) = {est['K_r']:.4f}",
                f"β = 0,35 + f_ck/200 - λ/150 = 0,35 + {f_ck:.2f}/200 - {lamb:.2f}/150 = {est['beta_phi']:.4f}",
                f"K_φ = max[1 ; 1 + βφ_ef] = max[1 ; 1 + {est['beta_phi']:.4f} × {phi_ef_usado:.3f}] = {est['K_phi']:.4f}",
                f"ε_yd = f_yd/E_s = {f_yd:.2f}/{E_S_MPA:.0f} = {eps_yd:.8f}",
                f"d = h - a = {h_mm:.2f} - {h_mm-melhor['d_mm']:.2f} = {melhor['d_mm']:.2f} mm",
                f"1/r₀ = ε_yd/(0,45d) = {eps_yd:.8f}/(0,45 × {melhor['d_mm']:.2f}) = {est['inv_r0_mm']:.8e} mm⁻¹",
                f"1/r = K_r K_φ (1/r₀) = {est['K_r']:.4f} × {est['K_phi']:.4f} × {est['inv_r0_mm']:.8e} = {est['inv_r_mm']:.8e} mm⁻¹",
                f"e₂ = (1/r)l₀²/10 = {est['inv_r_mm']:.8e} × ({l0_m*1000.0:.2f})² / 10 = {est['e2_mm']:.2f} mm",
                f"M₂ = N_Ed e₂ = {N_Ed_kN:.2f} × {est['e2_mm']/1000.0:.5f} = {est['M2_kNm']:.2f} kNm",
            )
        ))
        k = 10
    else:
        passos.append(_passo(
            "8. Classificação do pilar",
            r"\lambda\leq\lambda_{lim}\ ;\ M_2=0",
            _html_substituicao(
                f"λ = {lamb:.2f}",
                f"λ_lim = {est['lambda_lim']:.2f}",
                f"{lamb:.2f} ≤ {est['lambda_lim']:.2f} ⇒ pilar não esbelto e M₂ = 0,00 kNm",
            )
        ))
        k = 9

    # Momento final
    if usar_momentos_extremidade:
        if est["esbelto"]:
            passos.append(_passo(
                f"{k}. Momento final de dimensionamento",
                r"M_{Ed}=\max\left(M_{02}\ ;\ M_{0e}+M_2\ ;\ M_{01}+0.5M_2\ ;\ M_{min}\right)",
                _html_substituicao(
                    f"M_02 = {momentos['M02_kNm']:.2f} kNm",
                    f"M_0e + M₂ = {momentos['M0e_kNm']:.2f} + {est['M2_kNm']:.2f} = {momentos['M0e_kNm'] + est['M2_kNm']:.2f} kNm",
                    f"M_01 + 0,5M₂ = {momentos['M01_kNm']:.2f} + 0,5 × {est['M2_kNm']:.2f} = {momentos['M01_kNm'] + 0.5 * est['M2_kNm']:.2f} kNm",
                    f"M_min = {imperfeicao['M_min_kNm']:.2f} kNm",
                    f"Termo governante = {est['termo_governante']}",
                    f"M_Ed,total = {est['M_total_kNm']:.2f} kNm",
                )
            ))
        else:
            passos.append(_passo(
                f"{k}. Momento final de dimensionamento",
                r"M_{Ed}=\max(M_{02}\ ;\ M_{min})",
                _html_substituicao(
                    f"M_02 = {momentos['M02_kNm']:.2f} kNm",
                    f"M_min = {imperfeicao['M_min_kNm']:.2f} kNm",
                    f"M_Ed,total = max({momentos['M02_kNm']:.2f} ; {imperfeicao['M_min_kNm']:.2f}) = {est['M_total_kNm']:.2f} kNm",
                    f"Termo governante = {est['termo_governante']}",
                )
            ))
    else:
        passos.append(_passo(
            f"{k}. Momento final de dimensionamento",
            r"M_{Ed,tot}=M_{0Ed}+M_2",
            _html_substituicao(
                f"M_Ed,tot = M_0Ed + M₂ = {M0_Ed_kNm:.2f} + {est['M2_kNm']:.2f} = {est['M_total_kNm']:.2f} kNm",
            )
        ))

    # Seleção da armadura
    passos.append(_passo(
        f"{k+1}. Seleção e disposição da armadura longitudinal",
        r"A_{s,prov}=\sum\frac{\pi\phi_i^2}{4}",
        _html_substituicao(
            "Combinações avaliadas: 4, 6 ou 8 varões; Ø12, Ø16, Ø20, Ø25 e Ø32; distribuição perimetral e por duas faces opostas, com simetria e verificação geométrica.",
            f"Solução selecionada = {melhor['combinacao_str']}",
            f"Disposição selecionada = {melhor.get('disposicao_label', 'Distribuição perimetral')}",
            _substituicao_area_armadura(melhor),
        )
    ))

    # Equilíbrio da secção
    linhas_eq = _detalhe_equilibrio_numerico(
        sec=sec,
        b_mm=b_mm,
        h_mm=h_mm,
        f_cd=f_cd,
        f_yd=f_yd,
        N_Ed_kN=N_Ed_kN,
    )
    passos.append(_passo(
        f"{k+2}. Verificação resistente da secção com a armadura adotada",
        r"N_{Rd}=C_c+\sum F_{s,i}\ ;\ M_{Rd}=C_cz_c+\sum F_{s,i}z_i",
        _html_substituicao(*linhas_eq)
    ))

    # Verificação final
    passos.append(_passo(
        f"{k+3}. Síntese das verificações finais",
        r"A_{s,prov}\leq A_{s,max}\ ;\ N_{Rd}\approx N_{Ed}\ ;\ M_{Rd}\geq M_{Ed,tot}",
        _html_substituicao(
            f"A_s,prov = {melhor['area_total_cm2']:.2f} cm² ≤ A_s,max = {Asmax/100.0:.2f} cm²",
            f"N_Rd = {sec['N_Rd_N']/1000.0:.2f} kN ≈ N_Ed = {N_Ed_kN:.2f} kN",
            f"M_Rd = {melhor['M_Rd_kNm']:.2f} kNm ≥ M_Ed,tot = {est['M_total_kNm']:.2f} kNm",
            "Resultado: as verificações consideradas no âmbito do módulo foram satisfeitas.",
        )
    ))

    def resumo(solucao):
        if not solucao:
            return None
        return {
            "combinacao_str": solucao["combinacao_str"],
            "As_final_cm2": round(solucao["area_total_cm2"], 2),
            "area_total_cm2": solucao["area_total_cm2"],
            "disposicao": solucao.get("disposicao"),
            "disposicao_label": solucao.get("disposicao_label"),
        }

    desenho = {
        "b": b_mm,
        "h": h_mm,
        "c_nom": c_nom_mm,
        "phi_estribo": PHI_ESTRIBO_MM,
        "posicoes": melhor["posicoes"],
    }

    return {
        "status": "Sucesso",
        "mensagem": "Dimensionamento do pilar efetuado com sucesso.",
        "combinacao_final": melhor["combinacao_str"],
        "As_final_cm2": f"{melhor['area_total_cm2']:.2f}",
        "disposicao": melhor.get("disposicao"),
        "disposicao_label": melhor.get("disposicao_label"),
        "combinacao_unica": resumo(melhor_unica),
        "combinacao_mista": resumo(melhor_mista),
        "passos": passos,
        "dados_desenho": desenho,
        "comprimento_real_m": None if usar_l0_manual else l_m,
        "l0_m": l0_m,
        "beta_l0": beta_l0,
        "modo_l0": descricao_l0,
        "cond_ligacao": cond_ligacao,
        "cond_ligacao_label": descricao_l0 if not usar_l0_manual else "Comprimento efetivo introduzido manualmente",
        "e_i_mm": imperfeicao["e_i_mm"],
        "M_i_kNm": imperfeicao["M_i_kNm"],
        "M1_Ed_kNm": (imperfeicao["M1_Ed_kNm"] if not usar_momentos_extremidade else momentos["M02_kNm"]),
        "e0_mm": imperfeicao["e0_mm"],
        "M_min_kNm": imperfeicao["M_min_kNm"],
        "M0_Ed_kNm": M0_Ed_kNm,
        "M_Ed_entrada_kNm": (M_Ed_kNm if not usar_momentos_extremidade else None),
        "usar_momentos_extremidade": usar_momentos_extremidade,
        "M_01_entrada_kNm": (momentos["M_01_entrada_kNm"] if usar_momentos_extremidade else None),
        "M_02_entrada_kNm": (momentos["M_02_entrada_kNm"] if usar_momentos_extremidade else None),
        "M_01_analise_kNm": (momentos.get("M01_analise_kNm") if usar_momentos_extremidade else None),
        "M_02_analise_kNm": (momentos.get("M02_analise_kNm") if usar_momentos_extremidade else None),
        "M_01_kNm": momentos["M01_kNm"],
        "M_02_kNm": momentos["M02_kNm"],
        "r_m": momentos["r_m"],
        "M0e_kNm": momentos["M0e_kNm"],
        "termo_momento_governante": est.get("termo_governante"),
        "termos_momento_final": est.get("termos_momento_final", {}),
        "phi_ef": phi_ef_usado,
        "considerar_fluencia": bool(considerar_fluencia),
        "lambda": lamb,
        "lambda_lim": est["lambda_lim"],
        "classificacao": "Esbelto" if est["esbelto"] else "Não esbelto",
        "M2_kNm": est["M2_kNm"],
        "M_Ed_total_kNm": est["M_total_kNm"],
        "M_Rd_kNm": melhor["M_Rd_kNm"],
        "N_Rd_kN": sec["N_Rd_N"] / 1000.0,
        "x_mm": sec["x_mm"],
        "As_min_cm2": Asmin / 100.0,
        "As_max_cm2": Asmax / 100.0,
        "omega": est["omega"],
        "A_esbelteza": est["A"],
        "B_esbelteza": est["B"],
        "C_esbelteza": est["C"],
        "K_r": est["K_r"],
        "K_phi": est["K_phi"],
        "e2_mm": est["e2_mm"],

        # Diagrama de extensões e classificação convencional do estado resistente
        "epsilon_cu2": EPSILON_CU2,
        "epsilon_c_max": float(sec.get("epsilon_c_top", EPSILON_CU2)),
        "epsilon_c_bottom": float(sec.get("epsilon_c_bottom", EPSILON_CU2 * (1.0 - h_mm / sec["x_mm"]))),
        "regime_deformacao": sec.get("regime_deformacao", "eixo_neutro_na_secao"),
        "epsilon_yd": epsilon_yd_final,
        "epsilon_cu2_permille": round(EPSILON_CU2 * 1000.0, 3),
        "epsilon_c_max_permille": round(float(sec.get("epsilon_c_top", EPSILON_CU2)) * 1000.0, 3),
        "epsilon_yd_permille": round(epsilon_yd_final * 1000.0, 3),
        "epsilon_s_tracao_permille": round(modo_rotura["epsilon_s_tracao_max"] * 1000.0, 3),
        "epsilon_s_compressao_permille": round(modo_rotura["epsilon_s_compressao_max"] * 1000.0, 3),
        "modo_rotura": modo_rotura["grupo"],
        "modo_rotura_designacao": modo_rotura["designacao"],
        "modo_rotura_descricao": modo_rotura["descricao"],
        "graficos_materiais_svg": graficos_materiais_svg,
    }
