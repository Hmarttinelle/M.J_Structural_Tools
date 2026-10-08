# calculos/tests.py
"""Testes de regressão da M.J. Structural Tools v1.2.

A bateria cobre os casos de referência usados na auditoria final da aplicação:
- seleção de armaduras;
- viga simplesmente armada;
- viga com armadura de compressão;
- pilar não esbelto;
- pilar esbelto;
- limite de resistência do betão no âmbito do modelo;
- secção integralmente comprimida com x > h;
- transição na fronteira de esbelteza;
- comprimento efetivo manual;
- fluência;
- momentos distintos nas extremidades;
- módulo informativo de sapatas.
"""

from django.test import TestCase

from .services import armadura_service, pilar_service, viga_service


class ArmaduraServiceTests(TestCase):
    """Geração finita das armaduras no domínio construtivo atual."""

    def test_geracao_viga_respeita_dominio_construtivo(self):
        solucoes = armadura_service.gerar_combinacoes_viga(
            largura_disponivel_mm=214,
            dg_mm=20,
        )

        self.assertTrue(solucoes)

        catalogo = set(armadura_service.DIAMETROS_VIGA)

        for solucao in solucoes:
            barras = solucao["barras"]

            self.assertGreaterEqual(solucao["n_barras"], 2)
            self.assertLessEqual(solucao["n_barras"], 8)
            self.assertLessEqual(solucao["n_diametros"], 2)
            self.assertTrue(set(barras).issubset(catalogo))

            # A construção da camada é simétrica em relação ao eixo vertical.
            self.assertEqual(barras, barras[::-1])

            espacamento_minimo = max(
                max(barras),
                20.0,
                25.0,  # dg + 5, com dg = 20 mm
            )
            self.assertGreaterEqual(
                solucao["espacamento_livre_mm"] + 1e-9,
                espacamento_minimo,
            )

    def test_geracao_viga_inclui_combinacao_mista_simetrica(self):
        solucoes = armadura_service.gerar_combinacoes_viga(
            largura_disponivel_mm=214,
            dg_mm=20,
        )

        alvo = next(
            (
                solucao
                for solucao in solucoes
                if solucao["counts"] == {12.0: 2, 16.0: 2}
            ),
            None,
        )

        self.assertIsNotNone(alvo)
        self.assertEqual(alvo["n_barras"], 4)
        self.assertEqual(alvo["n_diametros"], 2)
        self.assertEqual(alvo["barras"], [16.0, 12.0, 12.0, 16.0])

    def test_geracao_viga_rejeita_largura_invalida(self):
        with self.assertRaises(ValueError):
            armadura_service.gerar_combinacoes_viga(
                largura_disponivel_mm=0,
                dg_mm=20,
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

    def test_pilar_aceita_fck_50_e_rejeita_superior(self):
        dados = dict(self.DADOS_BASE)
        dados["f_ck"] = 50

        resultado = pilar_service.dimensionar_pilar(**dados)
        self.assertEqual(resultado["status"], "Sucesso")

        dados["f_ck"] = 51
        with self.assertRaisesRegex(ValueError, r"fck ≤ 50 MPa"):
            pilar_service.dimensionar_pilar(**dados)

    def test_secao_integralmente_comprimida_usa_charneira_epsilon_c3(self):
        resultado = pilar_service.dimensionar_pilar(
            b_mm=250,
            h_mm=250,
            l_m=3.0,
            cond_ligacao="artic-artic",
            f_ck=30,
            f_yk=500,
            N_Ed_kN=1600,
            M_Ed_kNm=0,
            c_nom_mm=30,
        )

        self.assertGreater(float(resultado["x_mm"]), 250.0)
        self.assertEqual(
            resultado["regime_deformacao"],
            "secao_integralmente_comprimida",
        )
        self.assertEqual(
            resultado["modo_rotura"],
            "secao_integralmente_comprimida",
        )

        x_mm = float(resultado["x_mm"])
        epsilon_esperada = 1.75e-3 / (1.0 - 250.0 / (2.0 * x_mm))

        self.assertAlmostEqual(
            float(resultado["epsilon_c_max"]),
            epsilon_esperada,
            places=12,
        )
        self.assertGreater(float(resultado["epsilon_c_max"]), 1.75e-3)
        self.assertLess(float(resultado["epsilon_c_max"]), 3.5e-3)
        self.assertAlmostEqual(float(resultado["N_Rd_kN"]), 1600.0, places=2)
        self.assertGreaterEqual(
            float(resultado["M_Rd_kNm"]),
            float(resultado["M_Ed_total_kNm"]),
        )

    def test_fronteira_esbelteza_muda_entre_l0_279_e_280(self):
        comum = {
            "b_mm": 300,
            "h_mm": 400,
            "l_m": None,
            "cond_ligacao": None,
            "f_ck": 25,
            "f_yk": 500,
            "N_Ed_kN": 800,
            "M_Ed_kNm": 100,
            "c_nom_mm": 30,
            "usar_l0_manual": True,
        }

        abaixo = pilar_service.dimensionar_pilar(
            **comum,
            l0_manual_m=2.79,
        )
        acima = pilar_service.dimensionar_pilar(
            **comum,
            l0_manual_m=2.80,
        )

        self.assertEqual(abaixo["combinacao_final"], "4 Ø 12")
        self.assertEqual(acima["combinacao_final"], "4 Ø 12")

        self.assertLessEqual(
            float(abaixo["lambda"]),
            float(abaixo["lambda_lim"]),
        )
        self.assertEqual(abaixo["classificacao"], "Não esbelto")
        self.assertAlmostEqual(float(abaixo["M2_kNm"]), 0.0, places=12)

        self.assertGreater(
            float(acima["lambda"]),
            float(acima["lambda_lim"]),
        )
        self.assertEqual(acima["classificacao"], "Esbelto")
        self.assertGreater(float(acima["M2_kNm"]), 0.0)

    def test_momentos_extremidade_mesmo_sinal_preservam_rm_e_c(self):
        resultado = pilar_service.dimensionar_pilar(
            b_mm=300,
            h_mm=400,
            l_m=8.0,
            cond_ligacao="encab-artic",
            f_ck=25,
            f_yk=500,
            N_Ed_kN=800,
            M_Ed_kNm=0.0,
            c_nom_mm=30,
            usar_momentos_extremidade=True,
            M_01_kNm=50.0,
            M_02_kNm=100.0,
        )

        self.assertTrue(resultado["usar_momentos_extremidade"])
        self.assertAlmostEqual(float(resultado["r_m"]), 0.5, places=12)
        self.assertAlmostEqual(float(resultado["C_esbelteza"]), 1.2, places=12)
        self.assertAlmostEqual(
            float(resultado["M_01_analise_kNm"]),
            50.0,
            places=12,
        )
        self.assertAlmostEqual(
            float(resultado["M_02_analise_kNm"]),
            100.0,
            places=12,
        )

        self.assertEqual(resultado["classificacao"], "Esbelto")
        self.assertGreater(float(resultado["M2_kNm"]), 0.0)
        self.assertEqual(
            resultado["termo_momento_governante"],
            "M0e + M2",
        )
        self.assertAlmostEqual(
            float(resultado["M_Ed_total_kNm"]),
            float(resultado["M0e_kNm"]) + float(resultado["M2_kNm"]),
            places=9,
        )
        self.assertGreaterEqual(
            float(resultado["M_Rd_kNm"]),
            float(resultado["M_Ed_total_kNm"]),
        )

    def test_phi_ef_zero_reproduz_caso_sem_fluencia(self):
        sem_fluencia = pilar_service.dimensionar_pilar(**self.DADOS_BASE)
        phi_zero = pilar_service.dimensionar_pilar(
            **self.DADOS_BASE,
            considerar_fluencia=True,
            phi_ef=0.0,
        )

        self.assertEqual(
            phi_zero["combinacao_final"],
            sem_fluencia["combinacao_final"],
        )
        self.assertAlmostEqual(
            float(phi_zero["lambda_lim"]),
            float(sem_fluencia["lambda_lim"]),
            places=12,
        )
        self.assertEqual(
            phi_zero["classificacao"],
            sem_fluencia["classificacao"],
        )
        self.assertAlmostEqual(
            float(phi_zero["M2_kNm"]),
            float(sem_fluencia["M2_kNm"]),
            places=12,
        )
        self.assertAlmostEqual(
            float(phi_zero["M_Ed_total_kNm"]),
            float(sem_fluencia["M_Ed_total_kNm"]),
            places=12,
        )
        self.assertAlmostEqual(
            float(phi_zero["M_Rd_kNm"]),
            float(sem_fluencia["M_Rd_kNm"]),
            places=12,
        )
        self.assertAlmostEqual(float(phi_zero["K_phi"]), 1.0, places=12)
        self.assertAlmostEqual(float(phi_zero["phi_ef"]), 0.0, places=12)

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
