# calculos/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .services import viga_service, pilar_service
from .models import HistoricoCalculo, SystemConfiguration
from .forms import SystemConfigurationForm
import re

# ==============================================================================
# FUNÇÃO DE FORMATAÇÃO DE FÓRMULAS
# ==============================================================================
def formatar_latex_para_html(texto):
    """
    Converte uma string LaTeX para HTML para utilização no relatório PDF.
    """
    if not texto:
        return ""

    # Normalização inicial
    texto = texto.replace(r'\,;\,', ' ; ')
    texto = texto.replace(r'\;', ' ')
    texto = texto.replace(r'\,', ' ')
    texto = texto.replace(r'\displaylines', '')
    texto = texto.replace(r'\\', '<br/>')

    # Remover comandos LaTeX usados apenas para dimensionamento visual
    texto = texto.replace(r'\left', '')
    texto = texto.replace(r'\right', '')

    # Comandos mais longos devem ser substituídos antes dos mais curtos
    substituicoes = {
        r'\rightarrow': '→',
        r'\Rightarrow': '⇒',
        r'\varepsilon': 'ε',
        r'\epsilon': 'ε',
        r'\alpha': 'α',
        r'\beta': 'β',
        r'\gamma': 'γ',
        r'\Delta': 'Δ',
        r'\lambda': 'λ',
        r'\mu': 'μ',
        r'\phi': 'φ',
        r'\sigma': 'σ',
        r'\xi': 'ξ',
        r'\omega': 'ω',
        r'\rho': 'ρ',
        r'\geq': '≥',
        r'\leq': '≤',
        r'\ge': '≥',
        r'\le': '≤',
        r'\approx': '≈',
        r'\implies': '⇒',
        r'\pm': '±',
        r'\cdot': '×',
        r'\times': '×',
        r'\sum': 'Σ',
        r'\pi': 'π',
    }

    for original, novo in substituicoes.items():
        texto = texto.replace(original, novo)

    def processar_comandos(t):
        def processar_fracoes(match):
            numerador = processar_comandos(match.group(1))
            denominador = processar_comandos(match.group(2))
            return (
                '<span style="display:inline-block;vertical-align:middle;'
                'text-align:center;font-size:0.9em;margin:0 0.2em;">'
                '<span style="display:block;border-bottom:1px solid black;'
                f'padding:0 0.2em;">{numerador}</span>'
                '<span style="display:block;padding:0 0.2em;">'
                f'{denominador}</span></span>'
            )

        while r'\frac' in t:
            novo_t = re.sub(
                r'\\frac\{((?:[^{}]|\{[^{}]*\})+)\}'
                r'\{((?:[^{}]|\{[^{}]*\})+)\}',
                processar_fracoes,
                t,
                count=1
            )
            if novo_t == t:
                break
            t = novo_t

        t = re.sub(r'\\sqrt\{([^}]+)\}', r'√(\1)', t)
        t = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', t)
        t = re.sub(r'_([a-zA-Z0-9,]+)', r'<sub>\1</sub>', t)
        t = re.sub(r'\^\{([^}]+)\}', r'<sup>\1</sup>', t)
        t = re.sub(r'\^([a-zA-Z0-9]+)', r'<sup>\1</sup>', t)

        return t

    texto = processar_comandos(texto)

    # Limpeza final
    texto = texto.replace(r'\max', 'max')
    texto = texto.replace(r'\min', 'min')
    texto = texto.replace('{', '').replace('}', '').replace('\\', '')

    return texto


def _salvar_calculo_no_historico(request, elemento, resultado):
    if resultado.get('status') == 'Sucesso':
        input_data_copy = request.POST.copy().dict()
        input_data_copy.pop('csrfmiddlewaretoken', None)
        resultado_final_para_db = resultado.copy()
        resultado_final_para_db.pop('desenho_svg', None)
        calculo_obj = HistoricoCalculo.objects.create(
            elemento=elemento,
            input_data=input_data_copy,
            resultado_final=resultado_final_para_db
        )
        return calculo_obj
    return None


ROTULOS_LIGACAO_INPUT = {
    'artic-artic': 'Articulado - Articulado',
    'encab-artic': 'Encastrado - Articulado',
    'artic-encab': 'Articulado - Encastrado',
    'encab-encab': 'Encastrado - Encastrado',
    'encab-livre': 'Encastrado - Livre',
    'livre-encab': 'Livre - Encastrado',
}

CLASSES_BETAO = {
    '20': 'C20/25',
    '25': 'C25/30',
    '30': 'C30/37',
    '35': 'C35/45',
    '40': 'C40/50',
    '45': 'C45/55',
    '50': 'C50/60',
}


def _normalizar_numero_input(value):
    """Normaliza valores numéricos guardados como texto para apresentação."""
    try:
        numero = float(value)
    except (TypeError, ValueError):
        return str(value)

    if numero.is_integer():
        return str(int(numero))

    return str(value)


def _formatar_valor_input(key, value, elemento=None):
    if key == 'cond_ligacao':
        return ROTULOS_LIGACAO_INPUT.get(value, value)

    if key == 'f_ck':
        valor = _normalizar_numero_input(value)
        return CLASSES_BETAO.get(valor, valor)

    if key == 'f_yk':
        valor = _normalizar_numero_input(value)
        return f"A{valor}"

    return value


def _rotulo_input(elemento, key, rotulo_padrao):
    """Adapta o rótulo ao significado físico do parâmetro em cada módulo."""
    if elemento == 'Viga' and key == 'M_Ed':
        return 'Momento fletor de cálculo'
    return rotulo_padrao



def _input_deve_ser_mostrado(elemento, input_data, key):
    """Filtra campos de entrada sem significado no modo de cálculo escolhido."""
    if elemento != 'Pilar':
        return True

    usar_l0_manual = str(input_data.get('usar_l0_manual', '')).lower() in (
        'on', 'true', '1', 'yes'
    )

    if usar_l0_manual:
        # No modo manual, l e a condição de ligação não participam no cálculo.
        if key in ('l', 'cond_ligacao'):
            return False
    else:
        # No modo automático, l0_manual não participa no cálculo.
        if key == 'l0_manual':
            return False

    usar_momentos_extremidade = str(input_data.get('usar_momentos_extremidade', '')).lower() in (
        'on', 'true', '1', 'yes'
    )

    if usar_momentos_extremidade:
        if key == 'M_Ed':
            return False
    else:
        if key in ('M_01', 'M_02'):
            return False

    # Checkboxes são opções de controlo, não dados numéricos do quadro.
    if key in ('usar_l0_manual', 'considerar_fluencia', 'usar_momentos_extremidade'):
        return False

    # phi_ef só deve ser mostrado quando a fluência está efetivamente ativa.
    considerar_fluencia = str(input_data.get('considerar_fluencia', '')).lower() in (
        'on', 'true', '1', 'yes'
    )
    if key == 'phi_ef' and not considerar_fluencia:
        return False

    return True


def index_view(request):
    return render(request, 'calculos/index.html')


def viga_view(request):
    context = {}
    if request.method == 'POST':
        try:
            b = float(request.POST.get('b'))
            h = float(request.POST.get('h'))
            f_ck = float(request.POST.get('f_ck'))
            
           # breakpoint() # <--- Ponto de paragem adicionado para debug interativo
            
            f_yk = float(request.POST.get('f_yk'))
            M_Ed_kNm = float(request.POST.get('M_Ed'))
            c_nom = float(request.POST.get('c_nom'))
            context['input_data'] = request.POST
            resultado = viga_service.dimensionar_viga(
                b=b, h=h, f_ck=f_ck, f_yk=f_yk,
                M_Ed_kNm=M_Ed_kNm, c_nom=c_nom
            )
            if resultado.get('status') == 'Sucesso':
                resultado['desenho_svg'] = viga_service.desenhar_viga_svg(
                    resultado['dados_desenho'], resultado
                )
            calculo_salvo = _salvar_calculo_no_historico(
                request, 'Viga', resultado
            )
            if calculo_salvo:
                resultado['calculo_id'] = calculo_salvo.id
            context['resultado'] = resultado
        except (ValueError, TypeError) as e:
            context['resultado'] = {
                'status': 'Erro',
                'mensagem': f'Erro no cálculo: {e}'
            }
    return render(request, 'calculos/viga_dimensionamento.html', context)


def pilar_view(request):
    context = {}
    if request.method == 'POST':
        try:
            b_mm = float(request.POST.get('b'))
            h_mm = float(request.POST.get('h'))

            usar_l0_manual = request.POST.get('usar_l0_manual') == 'on'
            l0_manual_raw = request.POST.get('l0_manual')
            l0_manual_m = (
                float(l0_manual_raw)
                if usar_l0_manual and l0_manual_raw not in (None, '')
                else None
            )

            if usar_l0_manual:
                # No modo manual, l não participa no cálculo.
                l_m = None
                cond_ligacao = None
            else:
                l_raw = request.POST.get('l')
                if l_raw in (None, ''):
                    raise ValueError(
                        "Indique o comprimento real l quando o comprimento efetivo "
                        "não é introduzido manualmente."
                    )
                l_m = float(l_raw)
                cond_ligacao = request.POST.get('cond_ligacao')

            f_ck = float(request.POST.get('f_ck'))
            f_yk = float(request.POST.get('f_yk'))
            N_Ed_kN = float(request.POST.get('N_Ed'))
            c_nom_mm = float(request.POST.get('c_nom'))

            usar_momentos_extremidade = request.POST.get('usar_momentos_extremidade') == 'on'
            if usar_momentos_extremidade:
                m01_raw = request.POST.get('M_01')
                m02_raw = request.POST.get('M_02')
                if m01_raw in (None, '') or m02_raw in (None, ''):
                    raise ValueError(
                        'Indique M_01 e M_02 quando a opção de momentos distintos '
                        'nas extremidades está ativa.'
                    )
                M_01_kNm = float(m01_raw)
                M_02_kNm = float(m02_raw)
                M_Ed_kNm = 0.0
            else:
                med_raw = request.POST.get('M_Ed')
                if med_raw in (None, ''):
                    raise ValueError('Indique o momento de primeira ordem M_Ed.')
                M_Ed_kNm = float(med_raw)
                M_01_kNm = None
                M_02_kNm = None

            considerar_fluencia = request.POST.get('considerar_fluencia') == 'on'
            phi_ef_raw = request.POST.get('phi_ef')
            phi_ef = (
                float(phi_ef_raw)
                if considerar_fluencia and phi_ef_raw not in (None, '')
                else None
            )

            context['input_data'] = request.POST

            resultado = pilar_service.dimensionar_pilar(
                b_mm=b_mm,
                h_mm=h_mm,
                l_m=l_m,
                cond_ligacao=cond_ligacao,
                f_ck=f_ck,
                f_yk=f_yk,
                N_Ed_kN=N_Ed_kN,
                M_Ed_kNm=M_Ed_kNm,
                c_nom_mm=c_nom_mm,
                usar_l0_manual=usar_l0_manual,
                l0_manual_m=l0_manual_m,
                considerar_fluencia=considerar_fluencia,
                phi_ef=phi_ef,
                usar_momentos_extremidade=usar_momentos_extremidade,
                M_01_kNm=M_01_kNm,
                M_02_kNm=M_02_kNm,
            )

            if resultado.get('status') == 'Sucesso':
                resultado['desenho_svg'] = pilar_service.desenhar_pilar_svg(
                    resultado['dados_desenho']
                )

            calculo_salvo = _salvar_calculo_no_historico(
                request, 'Pilar', resultado
            )
            if calculo_salvo:
                resultado['calculo_id'] = calculo_salvo.id

            context['resultado'] = resultado

        except (ValueError, TypeError, ZeroDivisionError) as e:
            context['resultado'] = {
                'status': 'Erro',
                'mensagem': f'Erro: {e}'
            }

    return render(request, 'calculos/pilar_dimensionamento.html', context)


def sapata_view(request):
    """Apresenta o módulo de sapatas como funcionalidade futura, sem cálculo."""
    return render(request, 'calculos/sapata_dimensionamento.html')


def historico_view(request):
    todos_os_calculos = HistoricoCalculo.objects.filter(elemento__in=('Viga', 'Pilar')).order_by('-timestamp')
    context = {'calculos': todos_os_calculos}
    return render(request, 'calculos/historico.html', context)


def historico_detalhe_view(request, calculo_id):
    try:
        calculo = HistoricoCalculo.objects.get(id=calculo_id)
        if calculo.elemento not in ('Viga', 'Pilar'):
            return redirect('historico_calculos')
        resultado_final = calculo.resultado_final
        input_data = calculo.input_data
        context = {
            'calculo': {
                'id': calculo.id,
                'elemento': calculo.elemento,
                'timestamp': calculo.timestamp,
                'resultado_final': resultado_final,
            }
        }

        if 'dados_desenho' in resultado_final:
            if calculo.elemento == 'Viga':
                context['calculo']['desenho_svg'] = (
                    viga_service.desenhar_viga_svg(
                        resultado_final['dados_desenho'], resultado_final
                    )
                )
            elif calculo.elemento == 'Pilar':
                context['calculo']['desenho_svg'] = (
                    pilar_service.desenhar_pilar_svg(
                        resultado_final['dados_desenho']
                    )
                )

        INPUT_MAP = {
            'b': {'label': 'Largura', 'symbol': 'b', 'unit': 'mm'},
            'h': {'label': 'Altura', 'symbol': 'h', 'unit': 'mm'},
            'l': {'label': 'Comprimento Real', 'symbol': 'l', 'unit': 'm'}, 'l0': {'label': 'Comprimento Efetivo', 'symbol': 'l_0', 'unit': 'm'}, 'l0_manual': {'label': 'Comprimento Efetivo', 'symbol': 'l_0', 'unit': 'm'},
            'f_ck': {'label': 'Classe do Betão', 'symbol': 'f_{ck}', 'unit': ''},
            'f_yk': {'label': 'Classe do Aço', 'symbol': 'f_{yk}', 'unit': ''},
            'M_Ed': {'label': 'Momento de 1.ª Ordem', 'symbol': 'M_{Ed}', 'unit': 'kNm'},
        'M_01': {'label': 'Momento na Extremidade 1', 'symbol': 'M_{01}', 'unit': 'kNm'},
        'M_02': {'label': 'Momento na Extremidade 2', 'symbol': 'M_{02}', 'unit': 'kNm'},
            'M_01': {'label': 'Momento na Extremidade 1', 'symbol': 'M_{01}', 'unit': 'kNm'},
            'M_02': {'label': 'Momento na Extremidade 2', 'symbol': 'M_{02}', 'unit': 'kNm'},
            'c_nom': {'label': 'Recobrimento', 'symbol': 'c_{nom}', 'unit': 'mm'},
            'lig_topo': {'label': 'Ligação no Topo', 'symbol': '', 'unit': ''},
            'lig_base': {'label': 'Ligação na Base', 'symbol': '', 'unit': ''}, 'cond_ligacao': {'label': 'Condição de Ligação', 'symbol': '', 'unit': ''},
            'N_Ed': {'label': 'Esforço Axial', 'symbol': 'N_{Ed}', 'unit': 'kN'},
            'phi_ef': {'label': 'Coef. Fluência', 'symbol': r'\phi_{ef}', 'unit': ''},
        }

        input_formatado = []
        for key, value in input_data.items():
            if not _input_deve_ser_mostrado(calculo.elemento, input_data, key):
                continue
            if key in INPUT_MAP:
                info = INPUT_MAP[key]
                input_formatado.append({
                    'label': _rotulo_input(
                        calculo.elemento, key, info['label']
                    ),
                    'symbol': info['symbol'],
                    'value': _formatar_valor_input(
                        key, value, calculo.elemento
                    ),
                    'unit': info['unit']
                })

        context['calculo']['input_data_formatado'] = input_formatado
        return render(request, 'calculos/historico_detalhe.html', context)

    except HistoricoCalculo.DoesNotExist:
        return redirect('historico_calculos')


def historico_delete_view(request, calculo_id):
    try:
        calculo = HistoricoCalculo.objects.get(id=calculo_id)
        calculo.delete()
    except HistoricoCalculo.DoesNotExist:
        pass
    return redirect('historico_calculos')


def configuracao_view(request):
    config, created = SystemConfiguration.objects.get_or_create(id=1)

    if request.method == 'POST':
        form = SystemConfigurationForm(
            request.POST, request.FILES, instance=config
        )
        if form.is_valid():
            form.save()
            return redirect('pagina_inicial')
    else:
        form = SystemConfigurationForm(instance=config)

    return render(
        request,
        'calculos/configuracao.html',
        {'form': form}
    )


def gerar_relatorio_pdf_view(request, calculo_id):
    try:
        calculo = HistoricoCalculo.objects.get(id=calculo_id)
    except HistoricoCalculo.DoesNotExist:
        return HttpResponse("Cálculo não encontrado.", status=404)

    if calculo.elemento not in ('Viga', 'Pilar'):
        return HttpResponse("Relatório não disponível para este módulo.", status=404)

    resultado_final = calculo.resultado_final

    if 'dados_desenho' in resultado_final:
        if calculo.elemento == 'Viga':
            calculo.desenho_svg = viga_service.desenhar_viga_svg(
                resultado_final['dados_desenho'], resultado_final
            )
        elif calculo.elemento == 'Pilar':
            calculo.desenho_svg = pilar_service.desenhar_pilar_svg(
                resultado_final['dados_desenho']
            )

    INPUT_MAP = {
        'b': {'label': 'Largura', 'symbol': 'b', 'unit': 'mm'},
        'h': {'label': 'Altura', 'symbol': 'h', 'unit': 'mm'},
        'l': {'label': 'Comprimento Real', 'symbol': 'l', 'unit': 'm'}, 'l0': {'label': 'Comprimento Efetivo', 'symbol': 'l_0', 'unit': 'm'}, 'l0_manual': {'label': 'Comprimento Efetivo', 'symbol': 'l_0', 'unit': 'm'},
        'f_ck': {'label': 'Classe do Betão', 'symbol': 'f_{ck}', 'unit': ''},
        'f_yk': {'label': 'Classe do Aço', 'symbol': 'f_{yk}', 'unit': ''},
        'M_Ed': {'label': 'Momento de 1.ª Ordem', 'symbol': 'M_{Ed}', 'unit': 'kNm'},
        'M_01': {'label': 'Momento na Extremidade 1', 'symbol': 'M_{01}', 'unit': 'kNm'},
        'M_02': {'label': 'Momento na Extremidade 2', 'symbol': 'M_{02}', 'unit': 'kNm'},
        'c_nom': {'label': 'Recobrimento', 'symbol': 'c_{nom}', 'unit': 'mm'},
        'lig_topo': {'label': 'Ligação no Topo', 'symbol': '', 'unit': ''},
        'lig_base': {'label': 'Ligação na Base', 'symbol': '', 'unit': ''}, 'cond_ligacao': {'label': 'Condição de Ligação', 'symbol': '', 'unit': ''},
        'N_Ed': {'label': 'Esforço Axial', 'symbol': 'N_{Ed}', 'unit': 'kN'},
        'phi_ef': {'label': 'Coef. Fluência', 'symbol': r'\phi_{ef}', 'unit': ''},
    }

    input_formatado = []

    for key, value in calculo.input_data.items():
        if not _input_deve_ser_mostrado(calculo.elemento, calculo.input_data, key):
            continue
        if key in INPUT_MAP:
            info = INPUT_MAP[key]
            input_formatado.append({
                'label': _rotulo_input(
                    calculo.elemento, key, info['label']
                ),
                'value': _formatar_valor_input(
                    key, value, calculo.elemento
                ),
                'unit': info['unit']
            })

    calculo.input_data_formatado = input_formatado

    if calculo.resultado_final.get('passos'):
        for passo in calculo.resultado_final['passos']:
            if 'formula' in passo and passo['formula']:
                passo['formula_formatada'] = formatar_latex_para_html(
                    passo['formula']
                )

    html_string = render_to_string(
        'calculos/relatorio_pdf.html',
        {'calculo': calculo},
        request=request
    )

    pdf = HTML(
        string=html_string,
        base_url=request.build_absolute_uri()
    ).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="relatorio_{calculo.elemento.lower()}_'
        f'{calculo.id}.pdf"'
    )

    return response
