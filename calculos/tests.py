# calculos/tests.py
"""Testes de regressão da M.J. Structural Tools v1.2.

A bateria cobre os casos de referência usados na auditoria final da aplicação:
- seleção de armaduras;
- viga simplesmente armada;
- viga com armadura de compressão;
- pilar não esbelto;
- pilar esbelto;
- comprimento efetivo manual;
- fluência;
- momentos distintos nas extremidades;
- módulo informativo de sapatas.
"""

from django.test import TestCase

from .services import armadura_service, pilar_service, viga_service


class ArmaduraServiceTests(TestCase):
    """Critério hierárquico de seleção da armadura."""

    def test_solucao_otima_minimiza_area_fornecida(self):
        resultado = armadura_service.encontrar_combinacoes_otimas(
            As_req_cm2=7.82,
            largura_disponivel_mm=214,
            tipo_elemento="viga",
        )
        self.assertIsNotNone(resultado["unica"])
        self.assertIsNotNone(resultado["mista"])
        self.assertIsNotNone(resultado["otima"])
        self.assertGreaterEqual(resultado["otima"]["area_total_cm2"], 7.82)
        self.assertLessEqual(
            resultado["otima"]["area_total_cm2"],
            resultado["unica"]["area_total_cm2"] + 1e-12,
        )
        self.assertLessEqual(
            resultado["otima"]["area_total_cm2"],
            resultado["mista"]["area_total_cm2"] + 1e-12,
        )

    def test_geracao_inclui_combinacao_mista_2_mais_2(self):
        resultado = armadura_service.encontrar_combinacoes_otimas(
            As_req_cm2=7.82,
            largura_disponivel_mm=214,
            tipo_elemento="viga",
        )
        combinacao = resultado["mista"]["counts"]
        self.assertEqual(sum(combinacao.values()), 4)
        self.assertEqual(len(combinacao), 2)
        self.assertTrue(all(n == 2 for n in combinacao.values()))

    def test_rejeita_area_requerida_invalida(self):
        with self.assertRaises(ValueError):
            armadura_service.encontrar_combinacoes_otimas(
                As_req_cm2=0,
                largura_disponivel_mm=250,
                tipo_elemento="viga",
            )


class VigaServiceTests(TestCase):
    """Casos numéricos de referência para vigas da auditoria final."""

    def test_viga_simplesmente_armada_referencia(self):
        resultado = viga_service.dimensionar_viga(
            b=300,
            h=500,
            f_ck=25,
            f_yk=500,
            M_Ed_kNm=120,
            c_nom=30,
        )

        self.assertEqual(resultado["status"], "Sucesso")
        self.assertEqual(resultado["tipo_secao"], "simplesmente_armada")
        self.assertEqual(resultado["combinacao_final"], "4 Ø 12 + 1 Ø 16")
        self.assertAlmostEqual(float(resultado["As_final_cm2"]), 6.53, places=2)
        self.assertAlmostEqual(float(resultado["M_Rd_kNm"]), 120.914, places=3)
        self.assertAlmostEqual(float(resultado["xi_final"]), 0.15645, places=5)
        self.assertGreaterEqual(resultado["M_Rd_kNm"], 120.0)
        self.assertLessEqual(float(resultado["xi_final"]), 0.45)

    def test_viga_com_armadura_de_compressao_referencia(self):
        resultado = viga_service.dimensionar_viga(
            b=300,
            h=400,
            f_ck=30,
            f_yk=500,
            M_Ed_kNm=300,
            c_nom=30,
        )

        self.assertEqual(resultado["status"], "Sucesso")
        self.assertEqual(resultado["tipo_secao"], "armadura_compressao")
        self.assertEqual(resultado["combinacao_final"], "3 Ø 32")
        self.assertEqual(resultado["combinacao_compressao"], "1 Ø 10 + 2 Ø 20")
        self.assertAlmostEqual(float(resultado["As_final_cm2"]), 24.13, places=2)
        self.assertAlmostEqual(float(resultado["Asc_final_cm2"]), 7.07, places=2)
        self.assertAlmostEqual(float(resultado["M_Rd_kNm"]), 302.367, places=3)
        self.assertAlmostEqual(float(resultado["xi_final"]), 0.44659, places=5)
        self.assertGreaterEqual(resultado["M_Rd_kNm"], 300.0)
        self.assertLessEqual(float(resultado["xi_final"]), 0.45)

    def test_cor_dos_varoes_na_viga_simplesmente_armada(self):
        resultado = viga_service.dimensionar_viga(
            b=300, h=500, f_ck=25, f_yk=500, M_Ed_kNm=120, c_nom=30
        )
        svg = viga_service.desenhar_viga_svg(resultado["dados_desenho"], resultado)

        # Cinco varões resistentes de tração a vermelho.
        self.assertEqual(svg.count('fill="#e53935"'), 5)
        # Dois varões superiores construtivos permanecem cinzentos.
        self.assertEqual(svg.count('fill="#444"'), 2)

    def test_cor_dos_varoes_na_viga_com_armadura_de_compressao(self):
        resultado = viga_service.dimensionar_viga(
            b=300, h=400, f_ck=30, f_yk=500, M_Ed_kNm=300, c_nom=30
        )
        svg = viga_service.desenhar_viga_svg(resultado["dados_desenho"], resultado)

        # 3 varões de tração + 3 varões de compressão, todos resistentes.
        self.assertEqual(svg.count('fill="#e53935"'), 6)
        self.assertEqual(svg.count('fill="#444"'), 0)

    def test_rejeita_geometria_invalida(self):
        with self.assertRaises(ValueError):
            viga_service.dimensionar_viga(
                b=0,
                h=500,
                f_ck=25,
                f_yk=500,
                M_Ed_kNm=120,
                c_nom=30,
            )


class PilarServiceTests(TestCase):
    """Casos de regressão para a assinatura e o algoritmo atuais do pilar."""

    DADOS_BASE = {
        "b_mm": 300,
        "h_mm": 400,
        "l_m": 3.5,
        "cond_ligacao": "encab-artic",
        "f_ck": 25,
        "f_yk": 500,
        "N_Ed_kN": 800,
        "M_Ed_kNm": 100,
        "c_nom_mm": 30,
    }

    def test_pilar_nao_esbelto_referencia(self):
        resultado = pilar_service.dimensionar_pilar(**self.DADOS_BASE)

        self.assertEqual(resultado["status"], "Sucesso")
        self.assertEqual(resultado["combinacao_final"], "4 Ø 12")
        self.assertAlmostEqual(float(resultado["As_final_cm2"]), 4.52, places=2)
        self.assertAlmostEqual(float(resultado["l0_m"]), 2.45, places=3)
        self.assertAlmostEqual(float(resultado["lambda"]), 21.2176, places=4)
        self.assertAlmostEqual(float(resultado["lambda_lim"]), 24.2153, places=4)
        self.assertEqual(resultado["classificacao"], "Não esbelto")
        self.assertAlmostEqual(float(resultado["M2_kNm"]), 0.0, places=6)
        self.assertAlmostEqual(float(resultado["M_Ed_total_kNm"]), 104.90, places=2)
        self.assertAlmostEqual(float(resultado["M_Rd_kNm"]), 126.2450, places=3)
        self.assertAlmostEqual(float(resultado["N_Rd_kN"]), 800.0, places=2)

    def test_pilar_esbelto_ativa_segunda_ordem(self):
        dados = dict(self.DADOS_BASE)
        dados["l_m"] = 6.0
        resultado = pilar_service.dimensionar_pilar(**dados)

        self.assertEqual(resultado["status"], "Sucesso")
        self.assertEqual(resultado["classificacao"], "Esbelto")
        self.assertGreater(float(resultado["lambda"]), float(resultado["lambda_lim"]))
        self.assertGreater(float(resultado["M2_kNm"]), 0.0)
        self.assertGreater(float(resultado["M_Ed_total_kNm"]), float(resultado["M0_Ed_kNm"]))
        self.assertGreaterEqual(float(resultado["M_Rd_kNm"]), float(resultado["M_Ed_total_kNm"]))

    def test_comprimento_efetivo_manual_reproduz_caso_automatico(self):
        automatico = pilar_service.dimensionar_pilar(**self.DADOS_BASE)
        manual = pilar_service.dimensionar_pilar(
            b_mm=300,
            h_mm=400,
            l_m=None,
            cond_ligacao=None,
            f_ck=25,
            f_yk=500,
            N_Ed_kN=800,
            M_Ed_kNm=100,
            c_nom_mm=30,
            usar_l0_manual=True,
            l0_manual_m=2.45,
        )

        self.assertAlmostEqual(float(manual["l0_m"]), float(automatico["l0_m"]), places=9)
        self.assertAlmostEqual(float(manual["lambda"]), float(automatico["lambda"]), places=9)
        self.assertEqual(manual["combinacao_final"], automatico["combinacao_final"])
        self.assertAlmostEqual(float(manual["M_Rd_kNm"]), float(automatico["M_Rd_kNm"]), places=6)

    def test_fluencia_reduz_lambda_lim_e_pode_ativar_segunda_ordem(self):
        sem_fluencia = pilar_service.dimensionar_pilar(**self.DADOS_BASE)
        com_fluencia = pilar_service.dimensionar_pilar(
            **self.DADOS_BASE,
            considerar_fluencia=True,
            phi_ef=2.0,
        )

        self.assertLess(float(com_fluencia["lambda_lim"]), float(sem_fluencia["lambda_lim"]))
        self.assertEqual(com_fluencia["classificacao"], "Esbelto")
        self.assertGreater(float(com_fluencia["M2_kNm"]), 0.0)

    def test_momentos_distintos_preservam_relacao_de_curvatura(self):
        resultado = pilar_service.dimensionar_pilar(
            b_mm=300,
            h_mm=400,
            l_m=6.0,
            cond_ligacao="encab-artic",
            f_ck=25,
            f_yk=500,
            N_Ed_kN=800,
            M_Ed_kNm=0.0,
            c_nom_mm=30,
            usar_momentos_extremidade=True,
            M_01_kNm=-50.0,
            M_02_kNm=100.0,
        )

        self.assertTrue(resultado["usar_momentos_extremidade"])
        self.assertAlmostEqual(float(resultado["r_m"]), -0.5, places=6)
        self.assertAlmostEqual(float(resultado["C_esbelteza"]), 2.2, places=6)
        self.assertAlmostEqual(float(resultado["M_Ed_total_kNm"]), 108.4, places=2)
        self.assertGreaterEqual(float(resultado["M_Rd_kNm"]), float(resultado["M_Ed_total_kNm"]))

    def test_varoes_do_pilar_sao_representados_a_vermelho(self):
        resultado = pilar_service.dimensionar_pilar(**self.DADOS_BASE)
        svg = pilar_service.desenhar_pilar_svg(resultado["dados_desenho"])
        self.assertEqual(svg.count('fill="#e53935"'), 4)


class SapataPlaceholderTests(TestCase):

    def test_pagina_sapata_e_apenas_informativa(self):
        response = self.client.get("/sapata/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Em desenvolvimento")
        self.assertContains(response, "Módulo ainda não disponível")
        self.assertContains(response, "não se encontra disponível nesta versão")

    def test_post_nao_cria_calculo_de_sapata(self):
        from .models import HistoricoCalculo

        antes = HistoricoCalculo.objects.count()
        response = self.client.post("/sapata/", {"N_Ed": "1200"})
        depois = HistoricoCalculo.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(antes, depois)
