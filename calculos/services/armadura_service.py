# calculos/services/armadura_service.py
import math
from itertools import combinations

"""
Geração e seleção finita de armaduras longitudinais.

O módulo contém apenas os domínios construtivos atualmente utilizados pela
aplicação:
  - vigas: Ø10, Ø12, Ø16, Ø20, Ø25 e Ø32, uma camada por face;
  - pilares: Ø12, Ø16, Ø20, Ø25 e Ø32, com disposições simétricas.

"""

# ==============================================================================
# SELEÇÃO FINITA DE ARMADURAS PARA PILARES
# ==============================================================================

DIAMETROS_PILAR = (12, 16, 20, 25, 32)


def _area_varao_pilar_cm2(phi_mm):
    phi_mm = float(phi_mm)
    return math.pi * phi_mm * phi_mm / 400.0


def gerar_posicoes_pilar(
    b_mm,
    h_mm,
    c_nom_mm,
    phi_estribo_mm,
    n_barras,
    phi_canto_mm,
    phi_lateral_mm=None,
):
    """
    Gera as posições dos centros dos varões para o modelo construtivo
    adotado no módulo de pilares.

    São consideradas disposições simétricas com 4, 6 ou 8 varões. Os quatro
    varões de canto têm o mesmo diâmetro. Quando existem varões adicionais,
    estes são distribuídos simetricamente pelas duas faces laterais.
    """
    b_mm = float(b_mm)
    h_mm = float(h_mm)
    c_nom_mm = float(c_nom_mm)
    phi_estribo_mm = float(phi_estribo_mm)
    n_barras = int(n_barras)
    phi_canto_mm = float(phi_canto_mm)
    phi_lateral_mm = (
        phi_canto_mm if phi_lateral_mm is None else float(phi_lateral_mm)
    )

    if n_barras not in (4, 6, 8):
        return []

    a_canto = c_nom_mm + phi_estribo_mm + phi_canto_mm / 2.0
    if 2.0 * a_canto >= b_mm or 2.0 * a_canto >= h_mm:
        return []

    posicoes = [
        {"x_mm": a_canto, "y_mm": a_canto,
         "phi_mm": phi_canto_mm, "tipo": "canto"},
        {"x_mm": b_mm - a_canto, "y_mm": a_canto,
         "phi_mm": phi_canto_mm, "tipo": "canto"},
        {"x_mm": a_canto, "y_mm": h_mm - a_canto,
         "phi_mm": phi_canto_mm, "tipo": "canto"},
        {"x_mm": b_mm - a_canto, "y_mm": h_mm - a_canto,
         "phi_mm": phi_canto_mm, "tipo": "canto"},
    ]

    if n_barras == 4:
        return posicoes

    a_lateral_x = c_nom_mm + phi_estribo_mm + phi_lateral_mm / 2.0
    if 2.0 * a_lateral_x >= b_mm:
        return []

    y_sup = a_canto
    y_inf = h_mm - a_canto
    n_por_face = (n_barras - 4) // 2

    for i in range(1, n_por_face + 1):
        y = y_sup + i * (y_inf - y_sup) / (n_por_face + 1)
        posicoes.append({
            "x_mm": a_lateral_x, "y_mm": y,
            "phi_mm": phi_lateral_mm, "tipo": "lateral"
        })
        posicoes.append({
            "x_mm": b_mm - a_lateral_x, "y_mm": y,
            "phi_mm": phi_lateral_mm, "tipo": "lateral"
        })

    return posicoes


def gerar_posicoes_pilar_duas_faces(
    b_mm,
    h_mm,
    c_nom_mm,
    phi_estribo_mm,
    n_barras,
    phi_canto_mm,
    phi_face_mm=None,
):
    """
    Gera uma disposição simétrica por duas faces opostas, adequada ao modelo
    de flexão composta reta considerado no módulo.

    Disposições:
      * 4 varões -> 2 + 2;
      * 6 varões -> 3 + 3;
      * 8 varões -> 4 + 4.

    Mantêm-se quatro varões de canto. Os varões adicionais são colocados
    nas faces superior e inferior, de forma simétrica.
    """
    b_mm = float(b_mm)
    h_mm = float(h_mm)
    c_nom_mm = float(c_nom_mm)
    phi_estribo_mm = float(phi_estribo_mm)
    n_barras = int(n_barras)
    phi_canto_mm = float(phi_canto_mm)
    phi_face_mm = (
        phi_canto_mm if phi_face_mm is None else float(phi_face_mm)
    )

    if n_barras not in (4, 6, 8):
        return []

    a_canto = c_nom_mm + phi_estribo_mm + phi_canto_mm / 2.0
    if 2.0 * a_canto >= b_mm or 2.0 * a_canto >= h_mm:
        return []

    posicoes = [
        {"x_mm": a_canto, "y_mm": a_canto,
         "phi_mm": phi_canto_mm, "tipo": "canto"},
        {"x_mm": b_mm - a_canto, "y_mm": a_canto,
         "phi_mm": phi_canto_mm, "tipo": "canto"},
        {"x_mm": a_canto, "y_mm": h_mm - a_canto,
         "phi_mm": phi_canto_mm, "tipo": "canto"},
        {"x_mm": b_mm - a_canto, "y_mm": h_mm - a_canto,
         "phi_mm": phi_canto_mm, "tipo": "canto"},
    ]

    if n_barras == 4:
        return posicoes

    a_face_y = c_nom_mm + phi_estribo_mm + phi_face_mm / 2.0
    if 2.0 * a_face_y >= h_mm:
        return []

    n_interior_por_face = (n_barras - 4) // 2
    x_esq = a_canto
    x_dir = b_mm - a_canto

    for i in range(1, n_interior_por_face + 1):
        x = x_esq + i * (x_dir - x_esq) / (n_interior_por_face + 1)

        posicoes.append({
            "x_mm": x,
            "y_mm": a_face_y,
            "phi_mm": phi_face_mm,
            "tipo": "face"
        })
        posicoes.append({
            "x_mm": x,
            "y_mm": h_mm - a_face_y,
            "phi_mm": phi_face_mm,
            "tipo": "face"
        })

    return posicoes


def _verificar_geometria_pilar_duas_faces(
    b_mm,
    h_mm,
    c_nom_mm,
    phi_estribo_mm,
    n_barras,
    phi_canto_mm,
    phi_face_mm,
    dg_mm,
):
    """Verifica recobrimento e espaçamento livre na disposição por duas faces."""
    posicoes = gerar_posicoes_pilar_duas_faces(
        b_mm=b_mm,
        h_mm=h_mm,
        c_nom_mm=c_nom_mm,
        phi_estribo_mm=phi_estribo_mm,
        n_barras=n_barras,
        phi_canto_mm=phi_canto_mm,
        phi_face_mm=phi_face_mm,
    )
    if len(posicoes) != n_barras:
        return False, None, None

    s_min = max(
        float(phi_canto_mm),
        float(phi_face_mm),
        20.0,
        float(dg_mm) + 5.0,
    )

    # Verifica separadamente as duas faces resistentes.
    y_meio = float(h_mm) / 2.0
    face_sup = sorted(
        [p for p in posicoes if p["y_mm"] < y_meio],
        key=lambda p: p["x_mm"],
    )
    face_inf = sorted(
        [p for p in posicoes if p["y_mm"] > y_meio],
        key=lambda p: p["x_mm"],
    )

    livres = []
    for face in (face_sup, face_inf):
        for p1, p2 in zip(face, face[1:]):
            dist = p2["x_mm"] - p1["x_mm"]
            livre = dist - (p1["phi_mm"] + p2["phi_mm"]) / 2.0
            livres.append(livre)

    if livres and min(livres) + 1e-9 < s_min:
        return False, None, None

    # A distância livre vertical entre faces é apenas informativa.
    y_sup_max = max(p["y_mm"] + p["phi_mm"]/2.0 for p in face_sup)
    y_inf_min = min(p["y_mm"] - p["phi_mm"]/2.0 for p in face_inf)
    livre_vertical = y_inf_min - y_sup_max
    if livre_vertical <= 0:
        return False, None, None

    livre_horizontal = min(livres) if livres else float("inf")
    return True, livre_horizontal, livre_vertical

def _verificar_geometria_pilar(
    b_mm,
    h_mm,
    c_nom_mm,
    phi_estribo_mm,
    n_barras,
    phi_canto_mm,
    phi_lateral_mm,
    dg_mm,
):
    posicoes = gerar_posicoes_pilar(
        b_mm=b_mm,
        h_mm=h_mm,
        c_nom_mm=c_nom_mm,
        phi_estribo_mm=phi_estribo_mm,
        n_barras=n_barras,
        phi_canto_mm=phi_canto_mm,
        phi_lateral_mm=phi_lateral_mm,
    )
    if len(posicoes) != n_barras:
        return False, None, None

    s_min = max(
        float(phi_canto_mm),
        float(phi_lateral_mm),
        20.0,
        float(dg_mm) + 5.0,
    )

    # Face superior/inferior: os varões de canto são os extremos.
    a_canto = float(c_nom_mm) + float(phi_estribo_mm) + float(phi_canto_mm)/2.0
    dist_centros_h = float(b_mm) - 2.0 * a_canto
    livre_h = dist_centros_h - float(phi_canto_mm)
    if livre_h + 1e-9 < s_min:
        return False, None, None

    # Faces laterais: verificar todos os intervalos verticais.
    x_esq_lim = float(b_mm) / 2.0
    esquerda = sorted(
        [p for p in posicoes if p["x_mm"] <= x_esq_lim],
        key=lambda p: p["y_mm"],
    )
    livres_v = []
    for p1, p2 in zip(esquerda, esquerda[1:]):
        dist = p2["y_mm"] - p1["y_mm"]
        livre = dist - (p1["phi_mm"] + p2["phi_mm"]) / 2.0
        livres_v.append(livre)

    if livres_v and min(livres_v) + 1e-9 < s_min:
        return False, None, None

    livre_v = min(livres_v) if livres_v else float("inf")
    return True, livre_h, livre_v


def gerar_combinacoes_pilar(
    b_mm,
    h_mm,
    c_nom_mm,
    phi_estribo_mm=8.0,
    dg_mm=20.0,
    diametros=DIAMETROS_PILAR,
):
    """
    Gera as combinações de armadura longitudinal consideradas para pilares.

    São avaliadas duas famílias geométricas:
      1. distribuição perimetral, já usada nas versões anteriores;
      2. distribuição por duas faces opostas, adequada à flexão composta reta.

    Âmbito construtivo:
      * 4, 6 ou 8 varões;
      * quatro varões de canto obrigatórios;
      * diâmetros Ø12, Ø16, Ø20, Ø25 e Ø32;
      * disposições simétricas relativamente ao eixo de flexão;
      * dimensão máxima do agregado assumida igual a dg_mm.

    A geração é finita. A escolha resistente continua a ser feita em
    pilar_service.py, sem alteração das equações de estabilidade ou equilíbrio.
    """
    valores = (b_mm, h_mm, c_nom_mm, phi_estribo_mm, dg_mm)
    if not all(math.isfinite(float(v)) for v in valores):
        raise ValueError("Os parâmetros geométricos do pilar devem ser finitos.")

    b_mm = float(b_mm)
    h_mm = float(h_mm)
    c_nom_mm = float(c_nom_mm)
    phi_estribo_mm = float(phi_estribo_mm)
    dg_mm = float(dg_mm)

    if b_mm <= 0 or h_mm <= 0 or c_nom_mm <= 0:
        raise ValueError("As dimensões e o recobrimento devem ser positivos.")

    diametros = tuple(sorted(set(float(v) for v in diametros)))
    if not diametros:
        raise ValueError("O catálogo de diâmetros do pilar está vazio.")

    solucoes = []

    def fmt_phi(phi):
        return str(int(phi)) if float(phi).is_integer() else f"{phi:g}"

    def adicionar_solucao(
        n_barras,
        phi_canto,
        phi_extra,
        posicoes,
        livre_h,
        livre_v,
        disposicao,
        disposicao_label,
    ):
        n_extra = n_barras - 4
        area_cm2 = (
            4 * _area_varao_pilar_cm2(phi_canto)
            + n_extra * _area_varao_pilar_cm2(phi_extra)
        )

        counts = {phi_canto: 4}
        if n_extra:
            counts[phi_extra] = counts.get(phi_extra, 0) + n_extra
        counts = {phi: n for phi, n in sorted(counts.items()) if n > 0}

        combinacao = " + ".join(
            f"{n} Ø {fmt_phi(phi)}" for phi, n in counts.items()
        )

        solucoes.append({
            "combinacao_str": combinacao,
            "area_total_cm2": area_cm2,
            "As_final_cm2": round(area_cm2, 2),
            "counts": counts,
            "n_barras": n_barras,
            "n_diametros": len(counts),
            "diametro_max_mm": max(counts),
            "phi_canto_mm": phi_canto,
            "phi_lateral_mm": phi_extra,
            "espacamento_livre_horizontal_mm": livre_h,
            "espacamento_livre_vertical_mm": livre_v,
            "posicoes": posicoes,
            "disposicao": disposicao,
            "disposicao_label": disposicao_label,
        })

    for n_barras in (4, 6, 8):
        n_extra = n_barras - 4

        for phi_canto in diametros:
            extras = (phi_canto,) if n_extra == 0 else diametros

            for phi_extra in extras:
                # ------------------------------------------------------------
                # Família 1: distribuição perimetral.
                # Mantida primeiro para preservar o comportamento anterior
                # quando duas soluções equivalentes passam nas verificações.
                # ------------------------------------------------------------
                ok, livre_h, livre_v = _verificar_geometria_pilar(
                    b_mm=b_mm, h_mm=h_mm, c_nom_mm=c_nom_mm,
                    phi_estribo_mm=phi_estribo_mm, n_barras=n_barras,
                    phi_canto_mm=phi_canto, phi_lateral_mm=phi_extra,
                    dg_mm=dg_mm,
                )
                if ok:
                    posicoes = gerar_posicoes_pilar(
                        b_mm=b_mm, h_mm=h_mm, c_nom_mm=c_nom_mm,
                        phi_estribo_mm=phi_estribo_mm, n_barras=n_barras,
                        phi_canto_mm=phi_canto, phi_lateral_mm=phi_extra,
                    )
                    adicionar_solucao(
                        n_barras, phi_canto, phi_extra, posicoes,
                        livre_h, livre_v,
                        "perimetral",
                        "Distribuição perimetral",
                    )

                # ------------------------------------------------------------
                # Família 2: duas faces opostas.
                # Para 4 varões coincide geometricamente com os quatro cantos,
                # pelo que não é necessário duplicar a solução.
                # ------------------------------------------------------------
                if n_barras > 4:
                    ok2, livre_h2, livre_v2 = _verificar_geometria_pilar_duas_faces(
                        b_mm=b_mm, h_mm=h_mm, c_nom_mm=c_nom_mm,
                        phi_estribo_mm=phi_estribo_mm, n_barras=n_barras,
                        phi_canto_mm=phi_canto, phi_face_mm=phi_extra,
                        dg_mm=dg_mm,
                    )
                    if ok2:
                        posicoes2 = gerar_posicoes_pilar_duas_faces(
                            b_mm=b_mm, h_mm=h_mm, c_nom_mm=c_nom_mm,
                            phi_estribo_mm=phi_estribo_mm, n_barras=n_barras,
                            phi_canto_mm=phi_canto, phi_face_mm=phi_extra,
                        )
                        adicionar_solucao(
                            n_barras, phi_canto, phi_extra, posicoes2,
                            livre_h2, livre_v2,
                            "duas_faces",
                            "Duas faces opostas",
                        )

    # Elimina apenas duplicados dentro da mesma família geométrica.
    unicas = {}
    for s in solucoes:
        chave = (
            s["n_barras"],
            s["phi_canto_mm"],
            s["phi_lateral_mm"],
            s["disposicao"],
        )
        unicas[chave] = s

    return sorted(
        unicas.values(),
        key=lambda s: (
            s["area_total_cm2"],
            s["n_barras"],
            s["n_diametros"],
            s["diametro_max_mm"],
            s["combinacao_str"],
            0 if s["disposicao"] == "perimetral" else 1,
        ),
    )


# ==============================================================================
# SELEÇÃO FINITA DE ARMADURAS PARA VIGAS
# ==============================================================================
#
# Âmbito construtivo desta pesquisa:
#   - uma camada por face;
#   - 2 a 8 varões por camada;
#   - no máximo dois diâmetros distintos por camada;
#   - catálogo Ø10, Ø12, Ø16, Ø20, Ø25 e Ø32;
#   - distribuição simétrica dos varões;
#   - verificação do espaçamento livre horizontal;
#   - fck <= 50 MPa no modelo de viga atualmente implementado.
#
# A simetria, o limite de dois diâmetros e o catálogo são opções do programa,
# não imposições gerais do Eurocódigo 2.
# ==============================================================================

DIAMETROS_VIGA = (10, 12, 16, 20, 25, 32)


def gerar_combinacoes_viga(
    largura_disponivel_mm,
    dg_mm=20.0,
    diametros=DIAMETROS_VIGA,
):
    """
    Gera todas as combinações construtivas consideradas no âmbito da viga.

    A disposição é simétrica. Quando existe um número ímpar de um determinado
    diâmetro, o varão não emparelhado é colocado na zona central da camada.

    A área de cada varão é calculada por A = pi*phi²/4, sendo convertida para
    cm² através da divisão por 100.
    """
    largura_disponivel_mm = float(largura_disponivel_mm)
    dg_mm = float(dg_mm)

    if not all(
        math.isfinite(x) and x > 0
        for x in (largura_disponivel_mm, dg_mm)
    ):
        raise ValueError(
            "A largura disponível e a dimensão máxima do agregado "
            "devem ser positivas e finitas."
        )

    diametros = tuple(sorted(set(float(p) for p in diametros)))

    if not diametros:
        raise ValueError("O catálogo de diâmetros da viga não pode estar vazio.")

    if not all(math.isfinite(p) and p > 0 for p in diametros):
        raise ValueError("Os diâmetros da viga devem ser positivos e finitos.")

    resultados = []

    for n_barras in range(2, 9):
        # Soluções de diâmetro único.
        counts_list = [{phi: n_barras} for phi in diametros]

        # Soluções com dois diâmetros.
        for phi_1, phi_2 in combinations(diametros, 2):
            for n_1 in range(1, n_barras):
                counts = {
                    phi_1: n_1,
                    phi_2: n_barras - n_1,
                }

                # Permite no máximo um grupo com quantidade ímpar.
                # Isto garante a construção de uma camada simétrica.
                if sum(qtd % 2 for qtd in counts.values()) <= 1:
                    counts_list.append(counts)

        for counts in counts_list:
            # Pares exteriores de maior diâmetro e, quando exista,
            # um varão não emparelhado na região central.
            metade = [
                phi
                for phi in sorted(counts, reverse=True)
                for _ in range(counts[phi] // 2)
            ]
            centro = [
                phi
                for phi in counts
                if counts[phi] % 2
            ]
            barras = metade + centro + metade[::-1]

            if len(barras) != n_barras:
                continue

            espacamento_livre = (
                largura_disponivel_mm - sum(barras)
            ) / (n_barras - 1)

            espacamento_minimo = max(
                max(barras),
                20.0,
                dg_mm + 5.0,
            )

            if espacamento_livre + 1e-9 < espacamento_minimo:
                continue

            area_total_cm2 = sum(
                math.pi * phi * phi / 400.0
                for phi in barras
            )

            resultados.append({
                "counts": counts,
                "barras": barras,
                "area_total_cm2": area_total_cm2,
                "As_final_cm2": area_total_cm2,
                "n_barras": n_barras,
                "n_diametros": len(counts),
                "diametro_max_mm": max(barras),
                "espacamento_livre_mm": espacamento_livre,
                "combinacao_str": " + ".join(
                    f"{counts[phi]} Ø {int(phi) if float(phi).is_integer() else phi:g}"
                    for phi in sorted(counts)
                ),
            })

    # Remover duplicados lógicos, caso ocorram.
    unicos = {}
    for solucao in resultados:
        chave = tuple(solucao["barras"])
        if chave not in unicos:
            unicos[chave] = solucao

    return sorted(
        unicos.values(),
        key=lambda s: (
            s["area_total_cm2"],
            s["n_barras"],
            s["n_diametros"],
            s["diametro_max_mm"],
        ),
    )


def selecionar_viga(
    b,
    h,
    f_ck,
    f_yk,
    M_Ed_kNm,
    c_nom,
    dg_mm,
    resolver_equilibrio_duplamente_armada,
    diametros=DIAMETROS_VIGA,
):
    """
    Pesquisa finita da armadura longitudinal da viga.

    A função devolve:
        (melhor_solucao, solucoes_validas)

    Cada solução válida é representada por:
        (solucao_tracao, solucao_compressao, d, x, M_Rd_Nmm)

    Para secção simplesmente armada, solucao_compressao é None.

    O critério final é hierárquico:
      1. menor área total de aço (tração + compressão);
      2. menor número total de varões;
      3. menor número total de diâmetros distintos;
      4. menor diâmetro máximo utilizado.
    """
    valores = (b, h, f_ck, f_yk, M_Ed_kNm, c_nom, dg_mm)
    if not all(math.isfinite(float(x)) for x in valores):
        raise ValueError("Os parâmetros da seleção da viga devem ser finitos.")

    b = float(b)
    h = float(h)
    f_ck = float(f_ck)
    f_yk = float(f_yk)
    M_Ed_kNm = float(M_Ed_kNm)
    c_nom = float(c_nom)
    dg_mm = float(dg_mm)

    if b <= 0 or h <= 0:
        raise ValueError("As dimensões da secção devem ser positivas.")
    if not 0 < f_ck <= 50:
        raise ValueError(
            "O modelo atual da viga está limitado a fck ≤ 50 MPa."
        )
    if f_yk <= 0:
        raise ValueError("A resistência característica do aço deve ser positiva.")
    if M_Ed_kNm < 0:
        raise ValueError("O momento fletor de cálculo deve ser não negativo.")
    if c_nom <= 0:
        raise ValueError(
            "O recobrimento nominal deve ser positivo."
        )
    if dg_mm <= 0:
        raise ValueError(
            "A dimensão máxima do agregado deve ser positiva."
        )

    gamma_c = 1.50
    gamma_s = 1.15
    phi_estribo = 8.0
    E_s = 200000.0
    epsilon_cu2 = 3.5e-3
    xi_lim = 0.45

    f_cd = f_ck / gamma_c
    f_yd = f_yk / gamma_s

    # O catálogo definido para a viga é pesquisado integralmente.
    # A admissibilidade de cada diâmetro é determinada pelas verificações
    # geométricas e resistentes, sem pré-filtro em função de c_nom.
    diametros_pesquisa = tuple(
        float(phi)
        for phi in diametros
    )

    largura_disponivel = b - 2.0 * (c_nom + phi_estribo)

    if largura_disponivel <= 0:
        raise ValueError(
            "A largura disponível para a armadura longitudinal é não positiva."
        )

    combinacoes_viga = [
        solucao
        for solucao in gerar_combinacoes_viga(
            largura_disponivel,
            dg_mm,
            diametros_pesquisa,
        )
        if solucao["area_total_cm2"] * 100.0
        <= 0.04 * b * h + 1e-9
    ]

    validas = []

    for tracao in combinacoes_viga:
        A_st_mm2 = tracao["area_total_cm2"] * 100.0

        d = (
            h
            - c_nom
            - phi_estribo
            - max(tracao["barras"]) / 2.0
        )

        if d <= 0:
            continue

        f_ctm = 0.30 * f_ck ** (2.0 / 3.0)

        A_s_min_mm2 = max(
            0.26 * (f_ctm / f_yk) * b * d,
            0.0013 * b * d,
        )

        if A_st_mm2 + 1e-9 < A_s_min_mm2:
            continue

        x_lim = xi_lim * d
        C_c_lim_N = 0.8 * x_lim * b * f_cd
        M_lim_Nmm = C_c_lim_N * (d - 0.4 * x_lim)

        # ------------------------------------------------------------------
        # Secção simplesmente armada
        # ------------------------------------------------------------------
        if M_Ed_kNm * 1e6 <= M_lim_Nmm + 1e-9:
            x = A_st_mm2 * f_yd / (0.8 * b * f_cd)
            M_Rd_Nmm = A_st_mm2 * f_yd * (d - 0.4 * x)

            # Verificações geométricas da camada superior de montagem 2Ø10:
            #   - deve caber na largura disponível;
            #   - não deve cruzar a camada inferior.
            montagem_cabe = (
                largura_disponivel
                >= 20.0 + max(20.0, dg_mm + 5.0)
            )

            separacao_vertical = (
                d
                - (c_nom + 13.0)
                - (max(tracao["barras"]) + 10.0) / 2.0
            )

            separacao_vertical_minima = max(
                max(tracao["barras"]),
                20.0,
                dg_mm + 5.0,
            )

            if (
                x / d <= xi_lim + 1e-9
                and M_Rd_Nmm + 1e-6 >= M_Ed_kNm * 1e6
                and montagem_cabe
                and separacao_vertical + 1e-9
                >= separacao_vertical_minima
            ):
                validas.append(
                    (tracao, None, d, x, M_Rd_Nmm)
                )

            continue

        # ------------------------------------------------------------------
        # Secção com armadura de compressão
        # ------------------------------------------------------------------
        for compressao in combinacoes_viga:
            A_sc_mm2 = compressao["area_total_cm2"] * 100.0

            a = (
                c_nom
                + phi_estribo
                + max(compressao["barras"]) / 2.0
            )

            if a >= x_lim:
                continue

            separacao_vertical = (
                d
                - a
                - (
                    max(tracao["barras"])
                    + max(compressao["barras"])
                ) / 2.0
            )

            separacao_vertical_minima = max(
                max(tracao["barras"]),
                max(compressao["barras"]),
                20.0,
                dg_mm + 5.0,
            )

            if (
                separacao_vertical + 1e-9
                < separacao_vertical_minima
            ):
                continue

            epsilon_sc_lim = epsilon_cu2 * (
                1.0 - a / x_lim
            )

            sigma_sc_lim = min(
                E_s * epsilon_sc_lim,
                f_yd,
            )

            if sigma_sc_lim <= 0:
                continue

            A_sc_req_mm2 = (
                M_Ed_kNm * 1e6 - M_lim_Nmm
            ) / ((d - a) * sigma_sc_lim)

            A_st_req_mm2 = max(
                A_s_min_mm2,
                C_c_lim_N / f_yd
                + A_sc_req_mm2 * sigma_sc_lim / f_yd,
            )

            if A_sc_mm2 + 1e-9 < A_sc_req_mm2:
                continue

            if A_st_mm2 + 1e-9 < A_st_req_mm2:
                continue

            # Pré-filtro de ductilidade em x = x_lim.
            if (
                A_st_mm2 * f_yd
                > C_c_lim_N + A_sc_mm2 * sigma_sc_lim + 1e-6
            ):
                continue

            try:
                estado = resolver_equilibrio_duplamente_armada(
                    A_st_mm2,
                    A_sc_mm2,
                    b,
                    d,
                    a,
                    f_cd,
                    f_yd,
                    E_s,
                    epsilon_cu2,
                )
            except ValueError:
                continue

            if (
                estado["x_mm"] / d <= xi_lim + 1e-9
                and estado["M_Rd_Nmm"] + 1e-6
                >= M_Ed_kNm * 1e6
            ):
                validas.append(
                    (
                        tracao,
                        compressao,
                        d,
                        estado["x_mm"],
                        estado["M_Rd_Nmm"],
                    )
                )

                # As combinações estão ordenadas por área. Para esta armadura
                # de tração, esta é a menor armadura de compressão admissível.
                break

    if not validas:
        raise ValueError(
            "Não foi encontrada uma solução de armadura compatível com os "
            "limites geométricos e construtivos definidos no âmbito da aplicação "
            "(uma camada por face, 2 a 8 varões e diâmetros permitidos). "
            "Recomenda-se o redimensionamento da secção. A disposição em "
            "múltiplas camadas não é considerada nesta implementação."
        )

    def criterio_final(item):
        tracao, compressao, *_ = item

        return (
            tracao["area_total_cm2"]
            + (
                compressao["area_total_cm2"]
                if compressao
                else 0.0
            ),
            tracao["n_barras"]
            + (
                compressao["n_barras"]
                if compressao
                else 0
            ),
            tracao["n_diametros"]
            + (
                compressao["n_diametros"]
                if compressao
                else 0
            ),
            max(
                tracao["barras"]
                + (
                    compressao["barras"]
                    if compressao
                    else []
                )
            ),
        )

    melhor = min(validas, key=criterio_final)

    return melhor, validas
