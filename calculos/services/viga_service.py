# calculos/services/viga_service.py
import math
import re

from . import armadura_service


# ==============================================================================
# UTILITÁRIOS
# ==============================================================================

def _validar_entradas(b, h, f_ck, f_yk, M_Ed_kNm, c_nom):
    valores = {
        "b": b,
        "h": h,
        "f_ck": f_ck,
        "f_yk": f_yk,
        "M_Ed_kNm": M_Ed_kNm,
        "c_nom": c_nom,
    }

    for nome, valor in valores.items():
        if valor is None or not math.isfinite(float(valor)):
            raise ValueError(f"O parâmetro '{nome}' deve ser numérico e finito.")

    if b <= 0 or h <= 0:
        raise ValueError("As dimensões da secção devem ser positivas.")
    if f_ck <= 0 or f_yk <= 0:
        raise ValueError("As resistências dos materiais devem ser positivas.")
    if M_Ed_kNm < 0:
        raise ValueError("O momento fletor de cálculo deve ser não negativo.")
    if c_nom < 0:
        raise ValueError("O recobrimento nominal não pode ser negativo.")


def _f_ctm(f_ck):
    """
    Resistência média à tração do betão usada no cálculo de As,min.
    """
    if f_ck <= 50:
        return 0.30 * f_ck ** (2.0 / 3.0)

    f_cm = f_ck + 8.0
    return 2.12 * math.log(1.0 + f_cm / 10.0)


def _parse_combinacao(combinacao_str):
    """
    Converte:
        '2 Ø 16 + 2 Ø 25'
    em:
        [16, 16, 25, 25]
    """
    if not combinacao_str:
        return []

    barras = []
    for parcela in combinacao_str.split("+"):
        match = re.search(r"(\d+)\s*Ø\s*(\d+)", parcela.strip())
        if match:
            n = int(match.group(1))
            phi = int(match.group(2))
            barras.extend([phi] * n)

    return barras


def _diametro_representativo(solucao):
    """
    Para o cálculo conservativo de d numa única camada, adota-se o maior diâmetro
    presente na combinação selecionada.
    """
    if not solucao:
        return 0.0

    barras = _parse_combinacao(solucao.get("combinacao_str", ""))
    return float(max(barras)) if barras else 0.0


def _passo(titulo, formula=None, substituicao=None, resultado=None, observacao=None):
    """
    Cria um item compatível com o quadro 'Cálculo Detalhado (Passo a Passo)'.

    A fórmula é mantida no campo próprio. No campo de cálculo são apresentadas
    apenas as linhas numéricas e conclusões, sem os rótulos "Substituição",
    "Resultado" ou "Observação".
    """
    dados = {"titulo": titulo}

    if formula:
        dados["formula"] = formula

    partes = []

    if substituicao:
        partes.append(substituicao)

    if resultado:
        partes.append(resultado)

    if observacao:
        partes.append(observacao)

    if partes:
        dados["calculo"] = "<br>".join(partes)

    return dados


# ==============================================================================
# VERIFICAÇÃO RESISTENTE
# ==============================================================================

def _momento_resistente_simples(As_prov_mm2, b, d, f_cd, f_yd):
    """
    Verificação final de secção simplesmente armada com a armadura fornecida.

    Equilíbrio:
        As fyd = 0.8 x b fcd

    Resistência:
        MRd = 0.8 x b fcd (d - 0.4x)
    """
    x = (As_prov_mm2 * f_yd) / (0.8 * b * f_cd)
    z = d - 0.4 * x
    M_Rd_Nmm = 0.8 * x * b * f_cd * z

    return {
        "x_mm": x,
        "z_mm": z,
        "sigma_st_MPa": f_yd,
        "sigma_sc_MPa": 0.0,
        "M_Rd_Nmm": M_Rd_Nmm,
    }


def _estado_secao_duplamente_armada(
    x,
    Ast_mm2,
    Asc_mm2,
    b,
    d,
    a,
    f_cd,
    f_yd,
    E_s,
    epsilon_cu,
):
    """
    Calcula o estado interno da secção para um valor prescrito de x.

    Betão:
        Cc = 0.8 x b fcd

    Aço de tração:
        eps_st = eps_cu (d/x - 1)
        sigma_st = min(Es eps_st, fyd)

    Aço de compressão:
        eps_sc = eps_cu (1 - a/x)
        sigma_sc = min(Es eps_sc, fyd), para x > a

    Equilíbrio axial:
        T - Cc - Cs = 0
    """
    if x <= 0 or x >= d:
        raise ValueError("Profundidade do eixo neutro fora do domínio admissível.")

    epsilon_st = epsilon_cu * (d / x - 1.0)
    sigma_st = min(max(E_s * epsilon_st, 0.0), f_yd)

    if x > a:
        epsilon_sc = epsilon_cu * (1.0 - a / x)
        sigma_sc = min(max(E_s * epsilon_sc, 0.0), f_yd)
    else:
        # Se x <= a, a armadura superior já não está comprimida.
        epsilon_sc = epsilon_cu * (1.0 - a / x)
        sigma_sc = 0.0

    T = Ast_mm2 * sigma_st
    Cc = 0.8 * x * b * f_cd
    Cs = Asc_mm2 * sigma_sc

    residuo = T - Cc - Cs

    M_Rd_Nmm = Cc * (d - 0.4 * x) + Cs * (d - a)

    return {
        "x_mm": x,
        "epsilon_st": epsilon_st,
        "epsilon_sc": epsilon_sc,
        "sigma_st_MPa": sigma_st,
        "sigma_sc_MPa": sigma_sc,
        "T_N": T,
        "Cc_N": Cc,
        "Cs_N": Cs,
        "residuo_N": residuo,
        "M_Rd_Nmm": M_Rd_Nmm,
    }


def _resolver_equilibrio_duplamente_armada(
    Ast_mm2,
    Asc_mm2,
    b,
    d,
    a,
    f_cd,
    f_yd,
    E_s,
    epsilon_cu,
):
    """
    Resolve numericamente T - Cc - Cs = 0 através de bisseção.

    O intervalo é limitado a x > a, porque o modelo adotado considera a
    armadura superior como armadura de compressão.
    """
    x_min = max(a + 1e-6, 1e-6)
    x_max = d - 1e-6

    estado_min = _estado_secao_duplamente_armada(
        x_min, Ast_mm2, Asc_mm2, b, d, a, f_cd, f_yd, E_s, epsilon_cu
    )
    estado_max = _estado_secao_duplamente_armada(
        x_max, Ast_mm2, Asc_mm2, b, d, a, f_cd, f_yd, E_s, epsilon_cu
    )

    f_min = estado_min["residuo_N"]
    f_max = estado_max["residuo_N"]

    if f_min == 0:
        return estado_min

    if f_max == 0:
        return estado_max

    if f_min * f_max > 0:
        raise ValueError(
            "Não foi possível encontrar equilíbrio interno para a combinação "
            "de armaduras fornecida no domínio x > a."
        )

    estado_meio = None

    for _ in range(120):
        x_meio = 0.5 * (x_min + x_max)

        estado_meio = _estado_secao_duplamente_armada(
            x_meio,
            Ast_mm2,
            Asc_mm2,
            b,
            d,
            a,
            f_cd,
            f_yd,
            E_s,
            epsilon_cu,
        )

        f_meio = estado_meio["residuo_N"]

        if abs(f_meio) <= 1e-3:
            break

        if f_min * f_meio <= 0:
            x_max = x_meio
            f_max = f_meio
        else:
            x_min = x_meio
            f_min = f_meio

    return estado_meio



def _classificar_modo_rotura(epsilon_s, epsilon_yd, epsilon_c, epsilon_ud=None):
    """
    Classifica o modo convencional de rotura segundo o enquadramento do antigo
    ponto 2.6.1 da dissertação.

    No algoritmo atual a verificação final é efetuada com epsilon_c = epsilon_cu2.
    Assim, distinguem-se:
      - rotura pelo betão com aço ainda em regime elástico;
      - rotura pelo betão com aço em cedência.

    A classificação "rotura pelo aço" fica prevista para futura extensão, caso
    epsilon_s atinja epsilon_ud antes de epsilon_c atingir epsilon_cu2.
    """
    epsilon_cu2 = 3.5e-3
    tol = 1e-12

    if epsilon_ud is not None and epsilon_s >= epsilon_ud - tol and epsilon_c < epsilon_cu2 - tol:
        return {
            "grupo": "rotura_pelo_aco",
            "designacao": "Rotura pelo aço",
            "descricao": (
                "A armadura tracionada atinge a extensão limite adotada para o aço "
                "antes de o betão comprimido atingir a extensão última."
            ),
        }

    if epsilon_c >= epsilon_cu2 - tol:
        if epsilon_s <= epsilon_yd + tol:
            return {
                "grupo": "rotura_pelo_betao",
                "designacao": "Rotura pelo betão com aço em regime elástico",
                "descricao": (
                    "O betão comprimido atinge ε_cu2 enquanto a armadura tracionada "
                    "ainda não atingiu ε_yd, correspondendo a uma resposta menos dúctil."
                ),
            }

        return {
            "grupo": "rotura_pelo_betao",
            "designacao": "Rotura pelo betão com aço em cedência",
            "descricao": (
                "O betão comprimido atinge ε_cu2 e a armadura tracionada apresenta "
                "ε_s > ε_yd, correspondente ao domínio dúctil adotado no dimensionamento."
            ),
        }

    return {
        "grupo": "indeterminado",
        "designacao": "Modo de rotura não classificado",
        "descricao": (
            "O estado calculado não coincide com os estados-limite convencionais "
            "considerados nesta implementação."
        ),
    }


def gerar_graficos_materiais_svg(f_ck, f_cd, f_yd, E_s, epsilon_c,
                                 epsilon_st, epsilon_sc=None):
    """Estado resistente final, não estado de serviço sob MEd.

    A curva parábola-retângulo é apenas uma referência para fck <= 50 MPa.
    O equilíbrio existente continua a usar o bloco retangular equivalente.
    Não se extrapola esta referência para betões de alta resistência, pois
    o serviço atual mantém epsilon_cu = 3,5 por mil para todas as classes.
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
        eps_c2 = 0.002
        concrete = [(eps_c2 * i / 40,
                     f_cd * (1 - (1 - i / 40) ** 2)) for i in range(41)]
        concrete.append((0.0035, f_cd))
        panel(18, 'Betão — referência teórica', 0.0042, f_cd * 1.2,
              concrete, [(epsilon_c, f_cd, 'Fibra superior', '#0f766e')],
              [(eps_c2, 'c2', '2,0'), (0.0035, 'cu2', '3,5')])
    else:
        text(18, 27, 'Betão — referência indisponível', 16)
        text(18, 110, 'fck > 50 MPa: rever os parâmetros do modelo.')
        text(18, 135, 'Não se apresenta uma curva extrapolada.')
        text(18, 296, f'Extensão usada no cálculo: {epsilon_c*1000:.3f} ‰', 12)

    eps_yd = f_yd / E_s
    end = 1.2 * max(epsilon_st, epsilon_sc or 0, eps_yd)
    markers = [(epsilon_st, min(E_s * epsilon_st, f_yd),
                'Tração (ponto cheio)', '#2563eb')]
    if epsilon_sc is not None:
        markers.append((epsilon_sc, min(E_s * epsilon_sc, f_yd),
                        'Compressão (círculo)', '#c2410c'))
    panel(398, 'Aço — modelo do cálculo', end, f_yd * 1.2,
          [(0, 0), (eps_yd, f_yd), (end, f_yd)], markers,
          [(eps_yd, 'yd', f'{eps_yd * 1000:.3f}'.replace('.', ','))])
    text(18, 352, 'Estado resistente em MRd; valores em módulo. Não representa o estado sob MEd.', 12)
    text(18, 372, 'Betão: curva de referência; equilíbrio pelo bloco 0,8x. Aço: patamar sem limite εud definido.', 12)
    out.append('</svg>')
    return ''.join(out)


def gerar_diagrama_extensoes_svg(d, x, epsilon_c, epsilon_s, epsilon_yd, modo_rotura):
    """
    Gera um SVG esquemático do diagrama linear de extensões da secção.

    Representa:
      - ε_c na fibra comprimida superior;
      - ε = 0 no eixo neutro;
      - ε_s ao nível da armadura tracionada;
      - ε_yd como referência de início de cedência.
    """
    if d <= 0 or x <= 0 or x >= d:
        return ""

    width = 760
    height = 420
    top = 50
    bottom = 360
    sec_x = 180
    axis_x = 390
    label_x = 535

    geom_h = bottom - top
    y_neutral = top + geom_h * (x / d)
    y_steel = bottom

    eps_max = max(abs(epsilon_c), abs(epsilon_s), abs(epsilon_yd), 1e-9)
    scale = 150.0 / eps_max

    x_comp = axis_x - epsilon_c * scale
    x_steel = axis_x + epsilon_s * scale
    x_yd = axis_x + epsilon_yd * scale

    svg = (
        f'<svg width="100%" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )
    svg += (
        '<style>'
        '.t{font-family:Arial,sans-serif;font-size:14px;fill:#222;}'
        '.s{font-family:Arial,sans-serif;font-size:12px;fill:#555;}'
        '.b{font-family:Arial,sans-serif;font-size:14px;font-weight:700;fill:#222;}'
        '</style>'
    )

    # Secção geométrica
    svg += (
        f'<rect x="{sec_x-35}" y="{top}" width="70" height="{geom_h}" '
        f'fill="#efefef" stroke="#555" stroke-width="2"/>'
    )
    svg += (
        f'<line x1="{sec_x-45}" y1="{y_neutral}" x2="{sec_x+45}" '
        f'y2="{y_neutral}" stroke="#777" stroke-dasharray="5,4"/>'
    )
    svg += (
        f'<text x="{sec_x+55}" y="{y_neutral+5}" class="s">'
        f'eixo neutro, x = {x:.1f} mm</text>'
    )
    svg += (
        f'<text x="{sec_x-35}" y="{top-12}" class="s">fibra comprimida</text>'
    )
    svg += (
        f'<text x="{sec_x-35}" y="{bottom+24}" class="s">'
        f'armadura a d = {d:.1f} mm</text>'
    )

    # Eixo de extensões
    svg += (
        f'<line x1="{axis_x}" y1="{top-15}" x2="{axis_x}" y2="{bottom+20}" '
        f'stroke="#444" stroke-width="1.5"/>'
    )
    svg += f'<text x="{axis_x-8}" y="{top-22}" class="s">ε = 0</text>'

    # Distribuição linear
    svg += (
        f'<polyline points="{x_comp},{top} {axis_x},{y_neutral} '
        f'{x_steel},{y_steel}" fill="none" stroke="#111" stroke-width="3"/>'
    )
    svg += f'<circle cx="{x_comp}" cy="{top}" r="4" fill="#111"/>'
    svg += f'<circle cx="{axis_x}" cy="{y_neutral}" r="4" fill="#111"/>'
    svg += f'<circle cx="{x_steel}" cy="{y_steel}" r="4" fill="#111"/>'

    # Referência epsilon_yd
    svg += (
        f'<line x1="{x_yd}" y1="{top+10}" x2="{x_yd}" y2="{bottom}" '
        f'stroke="#888" stroke-dasharray="5,4"/>'
    )
    svg += (
        f'<text x="{x_yd+6}" y="{top+26}" class="s">'
        f'ε_yd = {epsilon_yd*1000:.3f} ‰</text>'
    )

    # Valores e classificação
    svg += (
        f'<text x="{label_x}" y="{top+10}" class="t">'
        f'ε_c = {epsilon_c*1000:.3f} ‰</text>'
    )
    svg += (
        f'<text x="{label_x}" y="{top+38}" class="t">'
        f'ε_s = {epsilon_s*1000:.3f} ‰</text>'
    )
    svg += (
        f'<text x="{label_x}" y="{top+66}" class="t">'
        f'ε_yd = {epsilon_yd*1000:.3f} ‰</text>'
    )

    svg += "</svg>"
    return svg


# ==============================================================================
# REPRESENTAÇÃO SVG
# ==============================================================================

def desenhar_viga_svg(dados_desenho, resultado=None):
    """
    Representação esquemática da secção transversal.

    Ajuste visual:
    - os varões longitudinais são desenhados com raio visual uniforme;
    - o diâmetro real continua armazenado nos dados e é usado nos cálculos;
    - evita-se que Ø25 apareça visualmente muito maior do que Ø16 no relatório.

    Esta escolha é apenas gráfica e não altera qualquer cálculo estrutural.
    """
    b = float(dados_desenho.get("b", 300))
    h = float(dados_desenho.get("h", 500))
    c_nom = float(dados_desenho.get("c_nom", 30))
    phi_estribo = float(dados_desenho.get("phi_estribo", 8))

    barras_tracao = dados_desenho.get("barras_tracao", [])
    barras_compressao = dados_desenho.get("barras_compressao", [])

    # Compatibilidade com cálculos históricos: versões anteriores podem ter
    # guardado a combinação de compressão no resultado, mas não a lista
    # barras_compressao dentro de dados_desenho. Nesse caso a lista é
    # reconstruída a partir da combinação adotada.
    if (
        not barras_compressao
        and resultado
        and resultado.get("tipo_secao") == "armadura_compressao"
    ):
        barras_compressao = _parse_combinacao(
            resultado.get("combinacao_compressao", "")
        )

    # Permite distinguir a armadura superior resistente, efetivamente calculada,
    # da armadura superior meramente construtiva usada na representação gráfica.
    # A lista barras_compressao existe também em vigas simplesmente armadas, onde
    # representa apenas os dois varões construtivos de montagem. Por isso, a cor
    # vermelha no topo depende do tipo de secção e não apenas da existência da lista.
    tem_armadura_compressao_calculada = bool(
        resultado and resultado.get("tipo_secao") == "armadura_compressao"
    )

    if not barras_tracao:
        n_barras = int(dados_desenho.get("n_barras", 0))
        phi_long = float(dados_desenho.get("phi_long", 0))
        barras_tracao = [phi_long] * n_barras if n_barras and phi_long else []

    if not barras_compressao:
        barras_compressao = [10.0, 10.0]

    PADDING = 60
    viewbox_width = b + 2 * PADDING
    viewbox_height = h + 2 * PADDING

    # Raio apenas visual, independente do diâmetro real.
    raio_visual = max(5.5, min(8.0, min(b, h) * 0.022))

    svg = (
        f'<svg width="100%" viewBox="0 0 {viewbox_width} {viewbox_height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )

    svg += (
        '<style>'
        '.dim-text {font-family: Arial, sans-serif; font-size: 14px; '
        'fill: #333; text-anchor: middle;}'
        '.bar-label {font-family: Arial, sans-serif; font-size: 10px; '
        'fill: #444; text-anchor: middle;}'
        '</style>'
    )

    svg += (
        f'<rect x="{PADDING}" y="{PADDING}" width="{b}" height="{h}" '
        f'fill="#e0e0e0" stroke="#555" stroke-width="2"/>'
    )

    estribo_x = PADDING + c_nom
    estribo_y = PADDING + c_nom
    estribo_w = b - 2 * c_nom
    estribo_h = h - 2 * c_nom

    svg += (
        f'<rect x="{estribo_x}" y="{estribo_y}" width="{estribo_w}" '
        f'height="{estribo_h}" fill="none" stroke="#777" '
        f'stroke-width="{max(phi_estribo/2, 2)}" '
        f'rx="{phi_estribo*2}" ry="{phi_estribo*2}"/>'
    )

    def desenhar_camada(barras, topo=False):
        nonlocal svg

        if not barras:
            return

        barras = [float(v) for v in barras]
        phi_max_real = max(barras)

        # Cor dos varões:
        # - tração adotada: vermelho;
        # - compressão calculada: vermelho;
        # - armadura superior apenas construtiva/de montagem: cinzento escuro.
        armadura_resistente = (not topo) or tem_armadura_compressao_calculada
        cor_varao = "#e53935" if armadura_resistente else "#444"
        contorno_varao = "#b71c1c" if armadura_resistente else "#2f2f2f"

        # As posições dos centros continuam relacionadas com a geometria real.
        margem_real = c_nom + phi_estribo + phi_max_real / 2.0

        if topo:
            y_pos = PADDING + margem_real
        else:
            y_pos = PADDING + h - margem_real

        livre = (b - 2 * (c_nom + phi_estribo) - sum(barras)) / max(len(barras) - 1, 1)
        bordo_varao = PADDING + c_nom + phi_estribo
        for i, phi_real in enumerate(barras):
            if len(barras) == 1:
                x_pos = PADDING + b / 2.0
            else:
                x_pos = bordo_varao + phi_real / 2.0
                bordo_varao += phi_real + livre

            svg += (
                f'<circle cx="{x_pos}" cy="{y_pos}" r="{raio_visual}" '
                f'fill="{cor_varao}" stroke="{contorno_varao}" stroke-width="1.4" '
                f'data-phi="{phi_real:g}"/>'
            )

    desenhar_camada(barras_compressao, topo=True)
    desenhar_camada(barras_tracao, topo=False)

    # Cota vertical
    svg += (
        f'<path d="M {PADDING/4} {PADDING} L {PADDING*3/4} {PADDING} '
        f'M {PADDING/2} {PADDING} L {PADDING/2} {PADDING+h} '
        f'M {PADDING/4} {PADDING+h} L {PADDING*3/4} {PADDING+h}" '
        f'stroke="#333" stroke-width="1" fill="none"/>'
    )
    svg += (
        f'<text x="{PADDING/2 - 10}" y="{PADDING+h/2}" class="dim-text" '
        f'transform="rotate(-90, {PADDING/2 - 10}, {PADDING+h/2})">'
        f'{h:g}</text>'
    )

    # Cota horizontal
    svg += (
        f'<path d="M {PADDING} {PADDING/4} L {PADDING} {PADDING*3/4} '
        f'M {PADDING} {PADDING/2} L {PADDING+b} {PADDING/2} '
        f'M {PADDING+b} {PADDING/4} L {PADDING+b} {PADDING*3/4}" '
        f'stroke="#333" stroke-width="1" fill="none"/>'
    )
    svg += (
        f'<text x="{PADDING+b/2}" y="{PADDING/2 - 10}" '
        f'class="dim-text">{b:g}</text>'
    )

    svg += "</svg>"
    return svg


# ==============================================================================
# DIMENSIONAMENTO
# ==============================================================================

def _dimensionar_viga_relatorio(b, h, f_ck, f_yk, M_Ed_kNm, c_nom, dg_mm=20.0, selecionadas=None):
    """
    Dimensionamento de viga retangular à flexão de acordo com o modelo definido
    no Capítulo 3 da dissertação.

    Unidades internas:
        comprimentos -> mm
        tensões -> MPa = N/mm²
        momentos -> N.mm
        áreas -> mm²
    """
    _validar_entradas(b, h, f_ck, f_yk, M_Ed_kNm, c_nom)

    dg_mm = float(dg_mm)
    if not math.isfinite(dg_mm) or dg_mm <= 0:
        raise ValueError("A dimensão máxima do agregado deve ser positiva e finita.")

    def escolher(face, area, largura, dg_mm=20.0):
        sol = selecionadas[face]
        if sol is None or sol["area_total_cm2"] + 1e-9 < area:
            raise ValueError("Inconsistência entre a pesquisa e a área requerida.")
        return sol, (sol if sol["n_diametros"] == 1 else None), (sol if sol["n_diametros"] > 1 else None)

    passos = []

    # --------------------------------------------------------------------------
    # 1. CONSTANTES
    # --------------------------------------------------------------------------
    gamma_c = 1.50
    gamma_s = 1.15
    alpha_cc = 1.00
    lambda_val = 0.80
    eta = 1.00

    xi_lim = 0.45

    E_s = 200000.0
    epsilon_cu = 3.5e-3

    phi_estribo = 8.0
    phi_long_inicial = max(selecionadas[0]["barras"])
    phi_comp_inicial = max(selecionadas[1]["barras"]) if selecionadas[1] else 10.0

    max_iteracoes = 12
    tolerancia_d_mm = 0.10

    # --------------------------------------------------------------------------
    # 2. MATERIAIS
    # --------------------------------------------------------------------------
    f_cd = alpha_cc * f_ck / gamma_c
    f_yd = f_yk / gamma_s
    f_ctm = _f_ctm(f_ck)

    passos.append(_passo(
        titulo="1. Resistência de cálculo do betão",
        formula=r"f_{cd}=\frac{\alpha_{cc}f_{ck}}{\gamma_c}",
        substituicao=(
            f"f_cd = ({alpha_cc:.2f} × {f_ck:.2f}) / {gamma_c:.2f}"
        ),
        resultado=f"f_cd = <b>{f_cd:.2f} MPa</b>",
    ))

    passos.append(_passo(
        titulo="2. Resistência de cálculo do aço",
        formula=r"f_{yd}=\frac{f_{yk}}{\gamma_s}",
        substituicao=f"f_yd = {f_yk:.2f} / {gamma_s:.2f}",
        resultado=f"f_yd = <b>{f_yd:.2f} MPa</b>",
    ))

    if f_ck <= 50:
        fctm_sub = (
            f"f_ctm = 0.30 × {f_ck:.2f}^(2/3)"
        )
        fctm_formula = r"f_{ctm}=0.30f_{ck}^{2/3}"
    else:
        f_cm = f_ck + 8.0
        fctm_sub = (
            f"f_cm = {f_ck:.2f} + 8 = {f_cm:.2f} MPa; "
            f"f_ctm = 2.12 × ln(1 + {f_cm:.2f}/10)"
        )
        fctm_formula = r"f_{ctm}=2.12\ln\left(1+\frac{f_{cm}}{10}\right)"

    passos.append(_passo(
        titulo="3. Resistência média à tração do betão",
        formula=fctm_formula,
        substituicao=fctm_sub,
        resultado=f"f_ctm = <b>{f_ctm:.2f} MPa</b>",
    ))

    # --------------------------------------------------------------------------
    # 3. LIMITES DE ARMADURA
    # --------------------------------------------------------------------------
    Ac_mm2 = b * h
    As_max_mm2 = 0.04 * Ac_mm2
    As_max_cm2 = As_max_mm2 / 100.0

    passos.append(_passo(
        titulo="4. Área da secção de betão",
        formula=r"A_c=bh",
        substituicao=f"A_c = {b:.2f} × {h:.2f}",
        resultado=f"A_c = <b>{Ac_mm2:.2f} mm²</b>",
    ))

    passos.append(_passo(
        titulo="5. Armadura longitudinal máxima",
        formula=r"A_{s,max}=0.04A_c",
        substituicao=f"A_s,max = 0.04 × {Ac_mm2:.2f}",
        resultado=(
            f"A_s,max = {As_max_mm2:.2f} mm² "
            f"= <b>{As_max_cm2:.2f} cm²</b>"
        ),
    ))

    M_Ed_Nmm = M_Ed_kNm * 1e6

    largura_disponivel = b - 2.0 * c_nom - 2.0 * phi_estribo

    if largura_disponivel <= 0:
        raise ValueError("A largura disponível para as armaduras é não positiva.")

    # --------------------------------------------------------------------------
    # 4. ITERAÇÃO GEOMÉTRICA
    # --------------------------------------------------------------------------
    phi_long = phi_long_inicial
    phi_comp = phi_comp_inicial

    resultado_iteracao = None
    solucao_unica = None
    solucao_mista = None

    for iteracao in range(1, max_iteracoes + 1):

        # ----------------------------------------------------------------------
        # 4.1 ALTURA ÚTIL
        # ----------------------------------------------------------------------
        d = h - c_nom - phi_estribo - phi_long / 2.0

        if d <= 0:
            raise ValueError("A altura útil calculada é não positiva.")

        titulo_d = (
            "6. Altura útil correspondente à combinação selecionada"
            if iteracao == 1
            else f"6. Altura útil correspondente à combinação selecionada "
                 f"(atualização {iteracao})"
        )

        passos.append(_passo(
            titulo=titulo_d,
            formula=r"d=h-c_{nom}-\phi_{est}\;-\;\frac{\phi_{long}}{2}",
            substituicao=(
                f"d = {h:.2f} - {c_nom:.2f} - {phi_estribo:.2f} "
                f"- {phi_long:.2f}/2"
            ),
            resultado=f"d = <b>{d:.2f} mm</b>",
        ))

        # ----------------------------------------------------------------------
        # 4.2 POSIÇÃO LIMITE DO EIXO NEUTRO
        # ----------------------------------------------------------------------
        x_lim = xi_lim * d

        passos.append(_passo(
            titulo=("7. Profundidade limite do eixo neutro" if iteracao == 1 else f"7. Profundidade limite do eixo neutro (atualização {iteracao})"),
            formula=r"x_{lim}=0.45d",
            substituicao=f"x_lim = 0.45 × {d:.2f}",
            resultado=f"x_lim = <b>{x_lim:.2f} mm</b>",
        ))

        z_lim = d - 0.4 * x_lim

        passos.append(_passo(
            titulo=("8. Braço do binário no estado limite" if iteracao == 1 else f"8. Braço do binário no estado limite (atualização {iteracao})"),
            formula=r"z_{lim}=d-0.4x_{lim}",
            substituicao=f"z_lim = {d:.2f} - 0.4 × {x_lim:.2f}",
            resultado=f"z_lim = <b>{z_lim:.2f} mm</b>",
        ))

        M_lim_Nmm = (
            eta
            * lambda_val
            * x_lim
            * b
            * f_cd
            * z_lim
        )
        M_lim_kNm = M_lim_Nmm / 1e6

        passos.append(_passo(
            titulo=("9. Momento limite" if iteracao == 1 else f"9. Momento limite (atualização {iteracao})"),
            formula=r"M_{lim}=0.8x_{lim}bf_{cd}z_{lim}",
            substituicao=(
                f"M_lim = 0.8 × {x_lim:.2f} × {b:.2f} × "
                f"{f_cd:.2f} × {z_lim:.2f}"
            ),
            resultado=(
                f"M_lim = {M_lim_Nmm:.2f} N.mm "
                f"= <b>{M_lim_kNm:.2f} kNm</b>"
            ),
        ))

        # ======================================================================
        # A. SECÇÃO SIMPLESMENTE ARMADA
        # ======================================================================
        if M_Ed_Nmm <= M_lim_Nmm + 1e-9:
            tipo_secao = "simplesmente_armada"

            passos.append(_passo(
                titulo="10. Classificação da secção",
                formula=r"M_{Ed}\leq M_{lim}",
                substituicao=(
                    f"{M_Ed_kNm:.2f} kNm ≤ {M_lim_kNm:.2f} kNm"
                ),
                resultado="<b>Secção simplesmente armada</b>",
            ))

            # Momento reduzido
            mu = M_Ed_Nmm / (b * d**2 * f_cd)

            passos.append(_passo(
                titulo="11. Momento fletor reduzido",
                formula=r"\mu=\frac{M_{Ed}}{bf_{cd}d^2}",
                substituicao=(
                    f"μ = {M_Ed_Nmm:.2f} / "
                    f"({b:.2f} × {f_cd:.2f} × {d:.2f}²)"
                ),
                resultado=f"μ = <b>{mu:.5f}</b>",
            ))

            radicando = 1.0 - 2.0 * mu

            if radicando < 0:
                raise ValueError(
                    "O cálculo da profundidade do eixo neutro produziu "
                    "um radicando negativo."
                )

            xi = (1.0 - math.sqrt(radicando)) / lambda_val

            passos.append(_passo(
                titulo="12. Profundidade relativa do eixo neutro",
                formula=r"\xi=\frac{1-\sqrt{1-2\mu}}{0.8}",
                substituicao=(
                    f"ξ = [1 - √(1 - 2 × {mu:.5f})] / 0.8"
                ),
                resultado=f"ξ = <b>{xi:.5f}</b>",
            ))

            x = xi * d

            passos.append(_passo(
                titulo="13. Profundidade do eixo neutro",
                formula=r"x=\xi d",
                substituicao=f"x = {xi:.5f} × {d:.2f}",
                resultado=f"x = <b>{x:.2f} mm</b>",
            ))

            z = d * (1.0 - 0.4 * xi)

            passos.append(_passo(
                titulo="14. Braço do binário interno",
                formula=r"z=d(1-0.4\xi)",
                substituicao=(
                    f"z = {d:.2f} × (1 - 0.4 × {xi:.5f})"
                ),
                resultado=f"z = <b>{z:.2f} mm</b>",
            ))

            As_calc_mm2 = M_Ed_Nmm / (z * f_yd)
            As_calc_cm2 = As_calc_mm2 / 100.0

            passos.append(_passo(
                titulo="15. Armadura longitudinal calculada",
                formula=r"A_{s,calc}=\frac{M_{Ed}}{zf_{yd}}",
                substituicao=(
                    f"A_s,calc = {M_Ed_Nmm:.2f} / "
                    f"({z:.2f} × {f_yd:.2f})"
                ),
                resultado=(
                    f"A_s,calc = {As_calc_mm2:.2f} mm² "
                    f"= <b>{As_calc_cm2:.2f} cm²</b>"
                ),
            ))

            # As,min
            As_min_1_mm2 = 0.26 * (f_ctm / f_yk) * b * d
            As_min_2_mm2 = 0.0013 * b * d
            As_min_mm2 = max(As_min_1_mm2, As_min_2_mm2)
            As_min_cm2 = As_min_mm2 / 100.0

            passos.append(_passo(
                titulo="16. Primeira expressão da armadura mínima",
                formula=r"A_{s,min,1}=0.26\frac{f_{ctm}}{f_{yk}}bd",
                substituicao=(
                    f"A_s,min,1 = 0.26 × ({f_ctm:.2f}/{f_yk:.2f}) "
                    f"× {b:.2f} × {d:.2f}"
                ),
                resultado=(
                    f"A_s,min,1 = {As_min_1_mm2:.2f} mm² "
                    f"= <b>{As_min_1_mm2/100.0:.2f} cm²</b>"
                ),
            ))

            passos.append(_passo(
                titulo="17. Segunda expressão da armadura mínima",
                formula=r"A_{s,min,2}=0.0013bd",
                substituicao=(
                    f"A_s,min,2 = 0.0013 × {b:.2f} × {d:.2f}"
                ),
                resultado=(
                    f"A_s,min,2 = {As_min_2_mm2:.2f} mm² "
                    f"= <b>{As_min_2_mm2/100.0:.2f} cm²</b>"
                ),
            ))

            passos.append(_passo(
                titulo="18. Armadura mínima adotada",
                formula=r"A_{s,min}=\max(A_{s,min,1};A_{s,min,2})",
                substituicao=(
                    f"A_s,min = max({As_min_1_mm2/100.0:.2f}; "
                    f"{As_min_2_mm2/100.0:.2f}) cm²"
                ),
                resultado=f"A_s,min = <b>{As_min_cm2:.2f} cm²</b>",
            ))

            As_req_mm2 = max(As_calc_mm2, As_min_mm2)
            As_req_cm2 = As_req_mm2 / 100.0

            passos.append(_passo(
                titulo="19. Armadura requerida",
                formula=r"A_{s,req}=\max(A_{s,calc};A_{s,min})",
                substituicao=(
                    f"A_s,req = max({As_calc_cm2:.2f}; "
                    f"{As_min_cm2:.2f}) cm²"
                ),
                resultado=f"A_s,req = <b>{As_req_cm2:.2f} cm²</b>",
            ))

            if As_req_mm2 > As_max_mm2 + 1e-9:
                raise ValueError(
                    "A área de armadura requerida é superior a As,max = 0,04 Ac."
                )

            principal, unica, mista = escolher(0,
                As_req_cm2,
                largura_disponivel,
                dg_mm=dg_mm,
            )

            solucao_unica = unica
            solucao_mista = mista

            As_prov_cm2 = principal["area_total_cm2"]
            As_prov_mm2 = As_prov_cm2 * 100.0
            phi_novo = _diametro_representativo(principal)

            passos.append(_passo(
                titulo="20. Seleção da armadura real",
                formula=r"A_{s,prov}\geq A_{s,req}",
                substituicao=(
                    f"A_s,prov = {As_prov_cm2:.2f} cm²; "
                    f"A_s,req = {As_req_cm2:.2f} cm²"
                ),
                resultado=(
                    f"<b>{principal['combinacao_str']}</b> "
                    f"com A_s,prov = <b>{As_prov_cm2:.2f} cm²</b>"
                ),
            ))

            # Verificação final com armadura fornecida
            verif = _momento_resistente_simples(
                As_prov_mm2,
                b,
                d,
                f_cd,
                f_yd,
            )

            x_prov = verif["x_mm"]
            z_prov = verif["z_mm"]
            M_Rd_Nmm = verif["M_Rd_Nmm"]
            M_Rd_kNm = M_Rd_Nmm / 1e6

            passos.append(_passo(
                titulo="21. Eixo neutro com a armadura fornecida",
                formula=r"x=\frac{A_{s,prov}f_{yd}}{0.8bf_{cd}}",
                substituicao=(
                    f"x = ({As_prov_mm2:.2f} × {f_yd:.2f}) / "
                    f"(0.8 × {b:.2f} × {f_cd:.2f})"
                ),
                resultado=f"x = <b>{x_prov:.2f} mm</b>",
            ))

            passos.append(_passo(
                titulo="22. Braço interno com a armadura fornecida",
                formula=r"z=d-0.4x",
                substituicao=f"z = {d:.2f} - 0.4 × {x_prov:.2f}",
                resultado=f"z = <b>{z_prov:.2f} mm</b>",
            ))

            passos.append(_passo(
                titulo="23. Momento resistente final",
                formula=r"M_{Rd}=0.8xbf_{cd}(d-0.4x)",
                substituicao=(
                    f"M_Rd = 0.8 × {x_prov:.2f} × {b:.2f} × "
                    f"{f_cd:.2f} × ({d:.2f} - 0.4 × {x_prov:.2f})"
                ),
                resultado=f"M_Rd = <b>{M_Rd_kNm:.2f} kNm</b>",
                observacao=(
                    f"M_Rd {'≥' if M_Rd_kNm >= M_Ed_kNm else '<'} "
                    f"M_Ed = {M_Ed_kNm:.2f} kNm"
                ),
            ))

            if x_prov / d > xi_lim + 1e-9:
                raise ValueError(
                    "A armadura fornecida conduz a x/d superior ao limite de 0,45."
                )

            if M_Rd_Nmm + 1e-6 < M_Ed_Nmm:
                raise ValueError(
                    "A combinação selecionada não satisfaz M_Rd >= M_Ed."
                )

            if As_prov_mm2 + 1e-6 < As_req_mm2:
                raise ValueError(
                    "A combinação selecionada é inferior à área requerida."
                )

            if As_prov_mm2 > As_max_mm2 + 1e-6:
                raise ValueError(
                    "A combinação selecionada ultrapassa As,max."
                )

            resultado_iteracao = {
                "tipo_secao": tipo_secao,
                "d": d,
                "x": x_prov,
                "z": z_prov,
                "M_lim_kNm": M_lim_kNm,
                "M_Rd_kNm": M_Rd_kNm,
                "As_calc_cm2": As_calc_cm2,
                "As_min_cm2": As_min_cm2,
                "As_req_cm2": As_req_cm2,
                "As_prov_cm2": As_prov_cm2,
                "solucao_tracao": principal,
                "solucao_compressao": None,
                "sigma_st_MPa": f_yd,
                "sigma_sc_MPa": 0.0,
                "phi_novo": phi_novo,
            }

        # ======================================================================
        # B. SECÇÃO COM ARMADURA DE COMPRESSÃO
        # ======================================================================
        else:
            tipo_secao = "armadura_compressao"

            passos.append(_passo(
                titulo="10. Classificação da secção",
                formula=r"M_{Ed}>M_{lim}",
                substituicao=(
                    f"{M_Ed_kNm:.2f} kNm > {M_lim_kNm:.2f} kNm"
                ),
                resultado="<b>Secção com armadura de compressão</b>",
            ))

            delta_M_Nmm = M_Ed_Nmm - M_lim_Nmm
            delta_M_kNm = delta_M_Nmm / 1e6

            passos.append(_passo(
                titulo="11. Momento excedente",
                formula=r"\Delta M=M_{Ed}-M_{lim}",
                substituicao=(
                    f"ΔM = {M_Ed_kNm:.2f} - {M_lim_kNm:.2f}"
                ),
                resultado=f"ΔM = <b>{delta_M_kNm:.2f} kNm</b>",
            ))

            a = c_nom + phi_estribo + phi_comp / 2.0

            passos.append(_passo(
                titulo="12. Posição da armadura de compressão",
                formula=r"a=c_{nom}+\phi_{est}+\frac{\phi_{comp}}{2}",
                substituicao=(
                    f"a = {c_nom:.2f} + {phi_estribo:.2f} "
                    f"+ {phi_comp:.2f}/2"
                ),
                resultado=f"a = <b>{a:.2f} mm</b>",
            ))

            if a >= x_lim:
                raise ValueError(
                    "A posição da armadura de compressão é incompatível com x_lim."
                )

            epsilon_sc = epsilon_cu * (1.0 - a / x_lim)

            passos.append(_passo(
                titulo="13. Extensão da armadura de compressão",
                formula=r"\epsilon_{sc}=\epsilon_{cu}\left(1-\frac{a}{x_{lim}}\right)",
                substituicao=(
                    f"ε_sc = {epsilon_cu:.6f} × "
                    f"(1 - {a:.2f}/{x_lim:.2f})"
                ),
                resultado=(
                    f"ε_sc = {epsilon_sc:.6f} "
                    f"= <b>{epsilon_sc*1000:.3f} ‰</b>"
                ),
            ))

            epsilon_yd = f_yd / E_s

            passos.append(_passo(
                titulo="14. Extensão de cedência do aço",
                formula=r"\epsilon_{yd}=\frac{f_{yd}}{E_s}",
                substituicao=(
                    f"ε_yd = {f_yd:.2f} / {E_s:.0f}"
                ),
                resultado=(
                    f"ε_yd = {epsilon_yd:.6f} "
                    f"= <b>{epsilon_yd*1000:.3f} ‰</b>"
                ),
            ))

            if epsilon_sc >= epsilon_yd:
                sigma_sc = f_yd

                passos.append(_passo(
                    titulo="15. Tensão na armadura de compressão",
                    formula=r"\sigma_{sc}=f_{yd}",
                    substituicao=(
                        f"ε_sc = {epsilon_sc*1000:.3f} ‰ ≥ "
                        f"ε_yd = {epsilon_yd*1000:.3f} ‰"
                    ),
                    resultado=f"σ_sc = <b>{sigma_sc:.2f} MPa</b>",
                ))
            else:
                sigma_sc = E_s * epsilon_sc

                passos.append(_passo(
                    titulo="15. Tensão na armadura de compressão",
                    formula=r"\sigma_{sc}=E_s\epsilon_{sc}",
                    substituicao=(
                        f"σ_sc = {E_s:.0f} × {epsilon_sc:.6f}"
                    ),
                    resultado=f"σ_sc = <b>{sigma_sc:.2f} MPa</b>",
                    observacao="A armadura comprimida permanece no domínio elástico.",
                ))

            if sigma_sc <= 0:
                raise ValueError(
                    "A tensão calculada na armadura de compressão é não positiva."
                )

            Asc_req_mm2 = delta_M_Nmm / ((d - a) * sigma_sc)
            Asc_req_cm2 = Asc_req_mm2 / 100.0

            passos.append(_passo(
                titulo="16. Armadura de compressão requerida",
                formula=r"A_{sc}=\frac{\Delta M}{(d-a)\sigma_{sc}}",
                substituicao=(
                    f"A_sc = {delta_M_Nmm:.2f} / "
                    f"[({d:.2f} - {a:.2f}) × {sigma_sc:.2f}]"
                ),
                resultado=(
                    f"A_sc = {Asc_req_mm2:.2f} mm² "
                    f"= <b>{Asc_req_cm2:.2f} cm²</b>"
                ),
            ))

            Ast_lim_mm2 = M_lim_Nmm / (z_lim * f_yd)
            Ast_lim_cm2 = Ast_lim_mm2 / 100.0

            passos.append(_passo(
                titulo="17. Armadura de tração correspondente ao momento limite",
                formula=r"A_{st,lim}=\frac{M_{lim}}{z_{lim}f_{yd}}",
                substituicao=(
                    f"A_st,lim = {M_lim_Nmm:.2f} / "
                    f"({z_lim:.2f} × {f_yd:.2f})"
                ),
                resultado=(
                    f"A_st,lim = {Ast_lim_mm2:.2f} mm² "
                    f"= <b>{Ast_lim_cm2:.2f} cm²</b>"
                ),
            ))

            Ast_req_mm2 = (
                Ast_lim_mm2
                + Asc_req_mm2 * sigma_sc / f_yd
            )

            passos.append(_passo(
                titulo="18. Armadura total de tração",
                formula=r"A_{st}=A_{st,lim}+A_{sc}\frac{\sigma_{sc}}{f_{yd}}",
                substituicao=(
                    f"A_st = {Ast_lim_mm2:.2f} + "
                    f"{Asc_req_mm2:.2f} × {sigma_sc:.2f}/{f_yd:.2f}"
                ),
                resultado=(
                    f"A_st = {Ast_req_mm2:.2f} mm² "
                    f"= <b>{Ast_req_mm2/100.0:.2f} cm²</b>"
                ),
            ))

            # As,min para a armadura tracionada
            As_min_1_mm2 = 0.26 * (f_ctm / f_yk) * b * d
            As_min_2_mm2 = 0.0013 * b * d
            As_min_mm2 = max(As_min_1_mm2, As_min_2_mm2)
            As_min_cm2 = As_min_mm2 / 100.0

            passos.append(_passo(
                titulo="19. Armadura mínima de tração",
                formula=r"A_{s,min}=\max\left(0.26\frac{f_{ctm}}{f_{yk}}bd;0.0013bd\right)",
                substituicao=(
                    f"max[0.26 × ({f_ctm:.2f}/{f_yk:.2f}) × "
                    f"{b:.2f} × {d:.2f}; "
                    f"0.0013 × {b:.2f} × {d:.2f}]"
                ),
                resultado=f"A_s,min = <b>{As_min_cm2:.2f} cm²</b>",
            ))

            Ast_req_mm2 = max(Ast_req_mm2, As_min_mm2)
            Ast_req_cm2 = Ast_req_mm2 / 100.0

            passos.append(_passo(
                titulo="20. Armadura de tração requerida",
                formula=r"A_{st,req}=\max(A_{st};A_{s,min})",
                substituicao=(
                    f"A_st,req = max({Ast_req_mm2/100.0:.2f}; "
                    f"{As_min_cm2:.2f}) cm²"
                ),
                resultado=f"A_st,req = <b>{Ast_req_cm2:.2f} cm²</b>",
            ))

            if Ast_req_mm2 > As_max_mm2 + 1e-9:
                raise ValueError(
                    "A armadura de tração requerida ultrapassa As,max = 0,04 Ac."
                )

            if Asc_req_mm2 > As_max_mm2 + 1e-9:
                raise ValueError(
                    "A armadura de compressão requerida ultrapassa As,max = 0,04 Ac."
                )

            sol_trac, unica, mista = escolher(0,
                Ast_req_cm2,
                largura_disponivel,
                dg_mm=dg_mm,
            )

            sol_comp, _, _ = escolher(1,
                Asc_req_cm2,
                largura_disponivel,
                dg_mm=dg_mm,
            )

            solucao_unica = unica
            solucao_mista = mista

            Ast_prov_cm2 = sol_trac["area_total_cm2"]
            Asc_prov_cm2 = sol_comp["area_total_cm2"]

            Ast_prov_mm2 = Ast_prov_cm2 * 100.0
            Asc_prov_mm2 = Asc_prov_cm2 * 100.0

            # A verificação de As,max deve ser feita também sobre as áreas
            # efetivamente fornecidas, e não apenas sobre as áreas teóricas.
            if Ast_prov_mm2 > As_max_mm2 + 1e-9:
                raise ValueError(
                    "A combinação real de armadura de tração ultrapassa "
                    "As,max = 0,04 Ac. A secção deve ser redimensionada."
                )

            if Asc_prov_mm2 > As_max_mm2 + 1e-9:
                raise ValueError(
                    "A combinação real de armadura de compressão ultrapassa "
                    "As,max = 0,04 Ac. A secção deve ser redimensionada."
                )

            passos.append(_passo(
                titulo="21. Armadura provisória de tração",
                formula=r"A_{st,prov}\geq A_{st,req}",
                substituicao=(
                    f"{Ast_prov_cm2:.2f} cm² ≥ {Ast_req_cm2:.2f} cm²"
                ),
                resultado=(
                    f"<b>{sol_trac['combinacao_str']}</b> "
                    f"com A_st,prov = <b>{Ast_prov_cm2:.2f} cm²</b>"
                ),
            ))

            passos.append(_passo(
                titulo="22. Armadura provisória de compressão",
                formula=r"A_{sc,prov}\geq A_{sc,req}",
                substituicao=(
                    f"{Asc_prov_cm2:.2f} cm² ≥ {Asc_req_cm2:.2f} cm²"
                ),
                resultado=(
                    f"<b>{sol_comp['combinacao_str']}</b> "
                    f"com A_sc,prov = <b>{Asc_prov_cm2:.2f} cm²</b>"
                ),
            ))

            phi_trac_novo = _diametro_representativo(sol_trac)
            phi_comp_novo = _diametro_representativo(sol_comp)

            if Ast_prov_cm2 + 1e-9 < Ast_req_cm2:
                raise ValueError(
                    "A armadura de tração fornecida é inferior à requerida."
                )

            if Asc_prov_cm2 + 1e-9 < Asc_req_cm2:
                raise ValueError(
                    "A armadura de compressão fornecida é inferior à requerida."
                )

            # A verificação final de MRd é efetuada depois da convergência geométrica.
            resultado_iteracao = {
                "tipo_secao": tipo_secao,
                "d": d,
                "a": a,
                "x": x_lim,
                "z": z_lim,
                "M_lim_kNm": M_lim_kNm,
                "M_Rd_kNm": None,
                "As_calc_cm2": None,
                "As_min_cm2": As_min_cm2,
                "As_req_cm2": Ast_req_cm2,
                "As_prov_cm2": Ast_prov_cm2,
                "Asc_req_cm2": Asc_req_cm2,
                "Asc_prov_cm2": Asc_prov_cm2,
                "solucao_tracao": sol_trac,
                "solucao_compressao": sol_comp,
                "sigma_sc_MPa": sigma_sc,
                "epsilon_sc": epsilon_sc,
                "phi_novo": phi_trac_novo,
                "phi_comp_novo": phi_comp_novo,
            }

        # ----------------------------------------------------------------------
        # 5. CONVERGÊNCIA
        # ----------------------------------------------------------------------
        phi_trac_antigo = phi_long
        phi_comp_antigo = phi_comp

        phi_long = resultado_iteracao["phi_novo"]

        if tipo_secao == "armadura_compressao":
            phi_comp = resultado_iteracao["phi_comp_novo"]

        d_novo = h - c_nom - phi_estribo - phi_long / 2.0

        convergiu_d = abs(d_novo - d) <= tolerancia_d_mm

        convergiu_comp = (
            tipo_secao == "simplesmente_armada"
            or abs(phi_comp - phi_comp_antigo) <= 1e-9
        )

        passos.append(_passo(
            titulo=(
                "23. Confirmação geométrica da combinação selecionada"
                if tipo_secao == "armadura_compressao"
                else "24. Confirmação geométrica da combinação selecionada"
            ),
            formula=r"d=h-c_{nom}-\phi_{est}\;-\;\frac{\phi_{long}}{2}",
            substituicao=(
                f"Ø tração adotado = {phi_long:.1f} mm; "
                + (
                    f"Ø compressão adotado = {phi_comp:.1f} mm; "
                    if tipo_secao == "armadura_compressao"
                    else ""
                )
                + f"d = {d_novo:.2f} mm"
            ),
            resultado=(
                "<b>Geometria final confirmada</b>"
                if convergiu_d and convergiu_comp
                else "<b>Atualização geométrica necessária</b>"
            ),
        ))

        if convergiu_d and convergiu_comp:
            break

    else:
        raise ValueError(
            "O refinamento da altura útil não convergiu dentro do número "
            "máximo de iterações."
        )

    # ==========================================================================
    # 6. VERIFICAÇÃO FINAL APÓS CONVERGÊNCIA
    # ==========================================================================
    r = resultado_iteracao
    tipo_secao = r["tipo_secao"]

    sol_tracao = r["solucao_tracao"]
    combinacao_final_str = sol_tracao["combinacao_str"]
    As_final_cm2 = r["As_prov_cm2"]

    barras_tracao = _parse_combinacao(combinacao_final_str)

    if tipo_secao == "armadura_compressao":
        sol_comp = r["solucao_compressao"]
        combinacao_compressao = sol_comp["combinacao_str"]
        barras_compressao = _parse_combinacao(combinacao_compressao)

        Ast_prov_mm2 = r["As_prov_cm2"] * 100.0

        # A armadura de tração efetivamente fornecida deve continuar dentro
        # do limite máximo depois da convergência geométrica.
        if Ast_prov_mm2 > As_max_mm2 + 1e-9:
            raise ValueError(
                "A armadura final de tração ultrapassa As,max = 0,04 Ac. "
                "Não existe solução admissível para a secção atual; "
                "a geometria deve ser redimensionada."
            )

        # ----------------------------------------------------------------------
        # AJUSTE FINAL DA ARMADURA DE COMPRESSÃO PARA GARANTIR DUCTILIDADE
        # ----------------------------------------------------------------------
        #
        # A conversão das áreas teóricas em combinações reais pode deslocar a
        # posição de equilíbrio do eixo neutro. Por isso, depois da convergência
        # geométrica, a armadura de compressão é novamente verificada.
        #
        # A solução só é aceite quando:
        #
        #   MRd >= MEd
        #   x / d <= xi_lim
        #
        # mantendo também:
        #
        #   Ast,prov >= Ast,req
        #   Asc,prov >= Asc,req
        #
        # Caso x/d ultrapasse xi_lim, determina-se a área mínima de compressão
        # necessária para que o equilíbrio, avaliado em x = x_lim, não desloque
        # o eixo neutro para além do limite.
        # ----------------------------------------------------------------------

        Asc_teorico_min_mm2 = r["Asc_req_cm2"] * 100.0

        sol_comp_final = sol_comp
        estado_final = None
        xi_final = None
        M_Rd_Nmm = None
        M_Rd_kNm = None
        a_final = None

        for ajuste in range(1, 13):

            combinacao_compressao = sol_comp_final["combinacao_str"]
            barras_compressao = _parse_combinacao(combinacao_compressao)

            if not barras_compressao:
                raise ValueError(
                    "Não foi possível interpretar a armadura de compressão."
                )

            phi_comp_final = max(barras_compressao)
            a_final = c_nom + phi_estribo + phi_comp_final / 2.0

            x_lim_final = xi_lim * r["d"]

            if a_final >= x_lim_final:
                raise ValueError(
                    "A armadura de compressão selecionada fica fora da zona "
                    "comprimida correspondente ao limite x/d = 0,45."
                )

            # Tensões das armaduras avaliadas no estado limite x = x_lim.
            epsilon_st_lim = epsilon_cu * (r["d"] / x_lim_final - 1.0)
            sigma_st_lim = min(
                max(E_s * epsilon_st_lim, 0.0),
                f_yd,
            )

            epsilon_sc_lim = epsilon_cu * (
                1.0 - a_final / x_lim_final
            )
            sigma_sc_lim = min(
                max(E_s * epsilon_sc_lim, 0.0),
                f_yd,
            )

            if sigma_sc_lim <= 0:
                raise ValueError(
                    "A tensão na armadura de compressão no estado limite "
                    "de ductilidade é não positiva."
                )

            Cc_lim_N = 0.8 * x_lim_final * b * f_cd
            T_lim_N = Ast_prov_mm2 * sigma_st_lim

            # Área de compressão necessária para que, em x = x_lim:
            #
            #   T <= Cc + Cs
            #
            # Desta forma, a raiz de equilíbrio não fica acima de x_lim.
            Asc_equilibrio_mm2 = max(
                0.0,
                (T_lim_N - Cc_lim_N) / sigma_sc_lim,
            )

            Asc_alvo_mm2 = max(
                Asc_teorico_min_mm2,
                Asc_equilibrio_mm2,
            )

            if Asc_alvo_mm2 > As_max_mm2 + 1e-9:
                raise ValueError(
                    "A área de armadura de compressão necessária para satisfazer "
                    "a ductilidade ultrapassa As,max = 0,04 Ac."
                )

            # Selecionar novamente uma combinação real com a área necessária
            # para garantir também o limite de ductilidade.
            estado_antes = _resolver_equilibrio_duplamente_armada(
                Ast_prov_mm2, sol_comp_final["area_total_cm2"] * 100.0,
                b, r["d"], a_final, f_cd, f_yd, E_s, epsilon_cu,
            )
            combinacao_antes = sol_comp_final["combinacao_str"]
            xi_antes = estado_antes["x_mm"] / r["d"]

            sol_comp_nova, _, _ = escolher(1,
                Asc_alvo_mm2 / 100.0,
                largura_disponivel,
                dg_mm=dg_mm,
            )

            Asc_prov_mm2 = sol_comp_nova["area_total_cm2"] * 100.0

            if Asc_prov_mm2 > As_max_mm2 + 1e-6:
                raise ValueError(
                    "A armadura de compressão fornecida ultrapassa As,max."
                )

            sol_comp_final = sol_comp_nova

            # Atualizar 'a' se a nova combinação alterar o maior diâmetro.
            barras_compressao = _parse_combinacao(
                sol_comp_final["combinacao_str"]
            )
            phi_comp_final = max(barras_compressao)
            a_final = c_nom + phi_estribo + phi_comp_final / 2.0

            # Equilíbrio final com as armaduras realmente fornecidas.
            estado_final = _resolver_equilibrio_duplamente_armada(
                Ast_prov_mm2,
                Asc_prov_mm2,
                b,
                r["d"],
                a_final,
                f_cd,
                f_yd,
                E_s,
                epsilon_cu,
            )

            x_final = estado_final["x_mm"]
            xi_final = x_final / r["d"]
            z_final = r["d"] - 0.4 * x_final

            M_Rd_Nmm = estado_final["M_Rd_Nmm"]
            M_Rd_kNm = M_Rd_Nmm / 1e6

            passos.append(_passo(
                titulo="Verificação da armadura de compressão selecionada",
                formula=r"A_{sc,eq}=\max(0;(A_{st}\sigma_{st,lim}-0.8x_{lim}bf_{cd})/\sigma_{sc,lim})",
                substituicao=(
                    f"Combinação selecionada: {combinacao_antes}; x/d = {xi_antes:.5f} "
                    f"{'>' if xi_antes > xi_lim else '≤'} {xi_lim:.2f}. "
                    f"Área teórica: {r['Asc_req_cm2']:.3f} cm²; "
                    f"área necessária ao equilíbrio em x_lim: {Asc_equilibrio_mm2/100:.3f} cm²; "
                    f"área mínima adotada na verificação: {Asc_alvo_mm2/100:.3f} cm²."
                ),
                resultado=(
                    f"Equilíbrio final: {sol_comp_final['combinacao_str']}; "
                    f"a = {a_final:.2f} mm; x = {x_final:.3f} mm; "
                    f"x/d = {xi_final:.5f}; M_Rd = {M_Rd_kNm:.3f} kNm."
                ),
                observacao=(
                    "Solução aceite: ductilidade e resistência verificadas."
                    if xi_final <= xi_lim + 1e-9 and M_Rd_Nmm + 1e-6 >= M_Ed_Nmm
                    else "Nova tentativa necessária para verificar ductilidade e resistência."
                ),
            ))

            if (
                xi_final <= xi_lim + 1e-9
                and M_Rd_Nmm + 1e-6 >= M_Ed_Nmm
            ):
                break

            # Se ainda não satisfizer x/d, elevar explicitamente o alvo
            # de compressão na iteração seguinte.
            Asc_teorico_min_mm2 = max(
                Asc_teorico_min_mm2,
                Asc_prov_mm2 + 1.0,
            )

        else:
            raise ValueError(
                "Não foi possível encontrar uma combinação de armadura de "
                "compressão que satisfaça simultaneamente M_Rd >= M_Ed "
                "e x/d <= 0,45."
            )

        combinacao_compressao = sol_comp_final["combinacao_str"]
        barras_compressao = _parse_combinacao(combinacao_compressao)
        Asc_prov_cm2 = sol_comp_final["area_total_cm2"]
        Asc_prov_mm2 = Asc_prov_cm2 * 100.0

        # Verificação final dos limites de armadura fornecida.
        if Ast_prov_mm2 > As_max_mm2 + 1e-9:
            raise ValueError(
                "A armadura final de tração ultrapassa As,max = 0,04 Ac. "
                "A secção deve ser redimensionada."
            )

        if Asc_prov_mm2 > As_max_mm2 + 1e-9:
            raise ValueError(
                "A armadura final de compressão ultrapassa As,max = 0,04 Ac. "
                "A secção deve ser redimensionada."
            )

        # Atualizar os dados finais para que relatório, SVG e verificações
        # utilizem exatamente a mesma armadura.
        r["solucao_compressao"] = sol_comp_final
        r["Asc_prov_cm2"] = Asc_prov_cm2

        passos.append(_passo(
            titulo="24. Armaduras finais adotadas",
            formula=r"A_{st,prov}\geq A_{st,req}\ ;\ A_{sc,prov}\geq A_{sc,req}",
            substituicao=(
                f"Tração: {sol_tracao['combinacao_str']} "
                f"({r['As_prov_cm2']:.2f} cm²); "
                f"Compressão: {combinacao_compressao} "
                f"({Asc_prov_cm2:.2f} cm²)"
            ),
            resultado=(
                f"A_st,prov = {r['As_prov_cm2']:.2f} cm² ≤ "
                f"A_s,max = {As_max_cm2:.2f} cm²; "
                f"A_sc,prov = {Asc_prov_cm2:.2f} cm² ≤ "
                f"A_s,max = {As_max_cm2:.2f} cm²"
            ),
        ))

        passos.append(_passo(
            titulo="25. Equilíbrio final da secção duplamente armada",
            formula=r"A_{st}\sigma_{st}=0.8xbf_{cd}+A_{sc}\sigma_{sc}",
            substituicao=(
                f"{Ast_prov_mm2:.2f} × "
                f"{estado_final['sigma_st_MPa']:.2f} = "
                f"0.8 × x × {b:.2f} × {f_cd:.2f} + "
                f"{Asc_prov_cm2*100.0:.2f} × "
                f"{estado_final['sigma_sc_MPa']:.2f}"
            ),
            resultado=f"x = <b>{x_final:.2f} mm</b>",
        ))

        passos.append(_passo(
            titulo="26. Verificação da ductilidade",
            formula=r"\xi=\frac{x}{d}\leq0.45",
            substituicao=(
                f"ξ = {x_final:.2f} / {r['d']:.2f}"
            ),
            resultado=(
                f"ξ = <b>{xi_final:.4f}</b> ≤ 0.4500"
            ),
        ))

        passos.append(_passo(
            titulo="27. Momento resistente final da secção",
            formula=r"M_{Rd}=C_c(d-0.4x)+C_s(d-a)",
            substituicao=(
                f"M_Rd = {estado_final['Cc_N']:.2f} × "
                f"({r['d']:.2f} - 0.4 × {x_final:.2f}) + "
                f"{estado_final['Cs_N']:.2f} × "
                f"({r['d']:.2f} - {a_final:.2f})"
            ),
            resultado=f"M_Rd = <b>{M_Rd_kNm:.2f} kNm</b>",
            observacao=(
                f"M_Rd {'≥' if M_Rd_kNm >= M_Ed_kNm else '<'} "
                f"M_Ed = {M_Ed_kNm:.2f} kNm"
            ),
        ))

        passos.append(_passo(
            titulo="28. Verificação resistente final",
            formula=r"M_{Rd}\geq M_{Ed}",
            substituicao=(
                f"{M_Rd_kNm:.2f} kNm ≥ {M_Ed_kNm:.2f} kNm"
            ),
            resultado=(
                "<b>VERIFICADO</b>"
                if (
                    M_Rd_kNm + 1e-9 >= M_Ed_kNm
                    and xi_final <= xi_lim + 1e-9
                )
                else "<b>NÃO VERIFICADO</b>"
            ),
        ))

        if xi_final > xi_lim + 1e-9:
            raise ValueError(
                "A solução final não satisfaz a condição de ductilidade "
                "x/d <= 0,45."
            )

        if M_Rd_Nmm + 1e-6 < M_Ed_Nmm:
            raise ValueError(
                "A secção duplamente armada selecionada não satisfaz "
                "M_Rd >= M_Ed."
            )

        r["x"] = x_final
        r["z"] = z_final
        r["a"] = a_final
        r["M_Rd_kNm"] = M_Rd_kNm
        r["xi_final"] = xi_final
        r["sigma_st_MPa"] = estado_final["sigma_st_MPa"]
        r["sigma_sc_MPa"] = estado_final["sigma_sc_MPa"]
        r["epsilon_st"] = estado_final["epsilon_st"]
        r["epsilon_sc"] = estado_final["epsilon_sc"]

    else:
        combinacao_compressao = None
        barras_compressao = [10.0, 10.0]

        passos.append(_passo(
            titulo="25. Verificação resistente final",
            formula=r"M_{Rd}\geq M_{Ed}",
            substituicao=(
                f"{r['M_Rd_kNm']:.2f} kNm ≥ {M_Ed_kNm:.2f} kNm"
            ),
            resultado="<b>VERIFICADO</b>",
        ))


    # --------------------------------------------------------------------------
    # 6.1 EXTENSÕES FINAIS PARA O ESTADO LIMITE RESISTENTE
    # --------------------------------------------------------------------------
    epsilon_cu2 = epsilon_cu
    epsilon_yd_final = f_yd / E_s

    if r["x"] <= 0 or r["x"] >= r["d"]:
        raise ValueError(
            "Não foi possível avaliar o diagrama de extensões: "
            "a posição final do eixo neutro deve satisfazer 0 < x < d."
        )

    epsilon_s_final = epsilon_cu2 * (r["d"] / r["x"] - 1.0)

    modo_rotura = _classificar_modo_rotura(
        epsilon_s=epsilon_s_final,
        epsilon_yd=epsilon_yd_final,
        epsilon_c=epsilon_cu2,
    )

    numero_extensoes = 29 if tipo_secao == "armadura_compressao" else 26

    passos.append(_passo(
        titulo=f"{numero_extensoes}. Extensão final da armadura tracionada",
        formula=r"\epsilon_s=\epsilon_{cu2}\left(\frac{d}{x}-1\right)",
        substituicao=(
            f"ε_s = {epsilon_cu2:.6f} × "
            f"({r['d']:.2f}/{r['x']:.2f} - 1)"
        ),
        resultado=(
            f"ε_s = {epsilon_s_final:.6f} "
            f"= <b>{epsilon_s_final*1000:.3f} ‰</b>"
        ),
    ))

    passos.append(_passo(
        titulo=f"{numero_extensoes + 1}. Extensão de cedência do aço",
        formula=r"\epsilon_{yd}=\frac{f_{yd}}{E_s}",
        substituicao=f"ε_yd = {f_yd:.2f} / {E_s:.0f}",
        resultado=(
            f"ε_yd = {epsilon_yd_final:.6f} "
            f"= <b>{epsilon_yd_final*1000:.3f} ‰</b>"
        ),
    ))

    graficos_materiais_svg = gerar_graficos_materiais_svg(
        f_ck=f_ck, f_cd=f_cd, f_yd=f_yd, E_s=E_s,
        epsilon_c=epsilon_cu2, epsilon_st=epsilon_s_final,
        epsilon_sc=(r["epsilon_sc"] if tipo_secao == "armadura_compressao" else None),
    )

    diagrama_extensoes_svg = gerar_diagrama_extensoes_svg(
        d=r["d"],
        x=r["x"],
        epsilon_c=epsilon_cu2,
        epsilon_s=epsilon_s_final,
        epsilon_yd=epsilon_yd_final,
        modo_rotura=modo_rotura,
    )

    # --------------------------------------------------------------------------
    # 7. DESENHO
    # --------------------------------------------------------------------------
    dados_desenho = {
        "b": b,
        "h": h,
        "c_nom": c_nom,
        "phi_estribo": phi_estribo,
        "barras_tracao": barras_tracao,
        "barras_compressao": barras_compressao,
        # Compatibilidade com a versão anterior:
        "n_barras": len(barras_tracao),
        "phi_long": max(barras_tracao) if barras_tracao else 0,
    }

    # --------------------------------------------------------------------------
    # 8. RESULTADO
    # --------------------------------------------------------------------------
    for nome_camada, barras in (("tração", barras_tracao), ("compressão/montagem", barras_compressao)):
        if len(barras) > 1:
            livre = (largura_disponivel - sum(barras)) / (len(barras) - 1)
            minimo = max(max(barras), 20.0, dg_mm + 5.0)
            if livre + 1e-9 < minimo:
                raise ValueError(f"Espaçamento insuficiente na camada de {nome_camada}.")

    resultado = {
        "dg_mm": dg_mm,
        "status": "Sucesso",
        "mensagem": "Dimensionamento da viga verificado com sucesso.",
        "tipo_secao": tipo_secao,
        "combinacao_final": combinacao_final_str,
        "As_final_cm2": f"{As_final_cm2:.2f}",
        "combinacao_unica": solucao_unica,
        "combinacao_mista": solucao_mista,
        "passos": passos,
        "dados_desenho": dados_desenho,

        "d_mm": round(r["d"], 3),
        "x_mm": round(r["x"], 3),
        "z_mm": round(r["z"], 3),
        "M_lim_kNm": round(r["M_lim_kNm"], 3),
        "M_Rd_kNm": (
            round(r["M_Rd_kNm"], 3)
            if r["M_Rd_kNm"] is not None
            else None
        ),
        "As_min_cm2": round(r["As_min_cm2"], 3),
        "As_req_cm2": round(r["As_req_cm2"], 3),
        "As_max_cm2": round(As_max_cm2, 3),

        # Identificação explícita da verificação final:
        "verificacao_MRd": (
            r["M_Rd_kNm"] is not None
            and r["M_Rd_kNm"] + 1e-9 >= M_Ed_kNm
        ),
        "xi_final": round(
            r.get("xi_final", r["x"] / r["d"]),
            5,
        ),
        "verificacao_ductilidade": (
            r.get("xi_final", r["x"] / r["d"]) <= xi_lim + 1e-9
        ),
        "verificacao_Asmax_tracao": (
            r["As_prov_cm2"] * 100.0 <= As_max_mm2 + 1e-9
        ),
        "verificacao_Asmax_compressao": (
            True
            if tipo_secao != "armadura_compressao"
            else r["Asc_prov_cm2"] * 100.0 <= As_max_mm2 + 1e-9
        ),

        # Diagrama de extensões e modo convencional de rotura
        "epsilon_cu2": epsilon_cu2,
        "epsilon_s": epsilon_s_final,
        "epsilon_yd": epsilon_yd_final,
        "epsilon_cu2_permille": round(epsilon_cu2 * 1000.0, 3),
        "epsilon_s_permille": round(epsilon_s_final * 1000.0, 3),
        "epsilon_yd_permille": round(epsilon_yd_final * 1000.0, 3),
        "modo_rotura": modo_rotura["grupo"],
        "modo_rotura_designacao": modo_rotura["designacao"],
        "modo_rotura_descricao": modo_rotura["descricao"],
        "diagrama_extensoes_svg": diagrama_extensoes_svg,
        "graficos_materiais_svg": graficos_materiais_svg,
    }

    if tipo_secao == "armadura_compressao":
        resultado.update({
            "combinacao_compressao": combinacao_compressao,
            "Asc_req_cm2": round(r["Asc_req_cm2"], 3),
            "Asc_final_cm2": f"{r['Asc_prov_cm2']:.2f}",
            "a_mm": round(r["a"], 3),
            "sigma_st_MPa": round(r["sigma_st_MPa"], 3),
            "sigma_sc_MPa": round(r["sigma_sc_MPa"], 3),
            "epsilon_st": r["epsilon_st"],
            "epsilon_sc": r["epsilon_sc"],
        })

    return resultado


def dimensionar_viga(b, h, f_ck, f_yk, M_Ed_kNm, c_nom, dg_mm=20.0):
    """Pesquisa discreta seguida da memória de cálculo da solução final.

    Catálogo e simetria são opções construtivas do programa. O âmbito não
    inclui amarrações, emendas, ELS, esforço transverso ou ação sísmica.
    """
    _validar_entradas(b,h,f_ck,f_yk,M_Ed_kNm,c_nom)
    best, alternatives = armadura_service.selecionar_viga(
        b, h, f_ck, f_yk, M_Ed_kNm, c_nom, float(dg_mm),
        _resolver_equilibrio_duplamente_armada,
    )
    t,c,*_ = best
    result = _dimensionar_viga_relatorio(b,h,f_ck,f_yk,M_Ed_kNm,c_nom,dg_mm,(t,c))
    result['dados_desenho']['barras_tracao'] = t['barras']
    if c:
        result['dados_desenho']['barras_compressao'] = c['barras']
    # Guardar também metadados suficientes para reconstruir corretamente
    # a representação gráfica no Histórico e no relatório PDF.
    result['dados_desenho']['tipo_secao'] = result.get('tipo_secao')
    result['dados_desenho']['combinacao_compressao'] = result.get('combinacao_compressao')
    result['selecao_metodo'] = 'pesquisa_finita'
    result['area_tracao_exata_cm2'] = t['area_total_cm2']
    result['area_compressao_exata_cm2'] = c['area_total_cm2'] if c else 0
    result['ambito_construtivo'] = (
        'Uma camada por face; Ø10 a Ø32; estribos Ø8 e agregado de 20 mm assumidos. '
        'Confirmar recobrimento, amarrações, emendas e armadura transversal no projeto. '
        'Parâmetros nacionais do EC2 por confirmar; não inclui ELS nem ação sísmica.'
    )
    # Não apresentar alternativas de tração sem a compressão correspondente.
    result['combinacao_unica'] = None
    result['combinacao_mista'] = None
    return result
