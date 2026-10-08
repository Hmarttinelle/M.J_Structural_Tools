"""Testes adicionais de alinhamento entre o Capítulo 3 e o módulo de vigas.

Estes testes verificam especificamente as alterações introduzidas para eliminar
restrições internas sem fundamento no modelo do Capítulo 3:
- utilização integral do catálogo Ø10 a Ø32;
- aceitação de recobrimento nominal positivo sem impor c_nom >= Øestribo;
- domínio do betão limitado a fck <= 50 MPa;
- disponibilização funcional de C45/55 e C50/60.
"""

from django.test import TestCase

from .services import viga_service


class VigaAlinhamentoCapitulo3Tests(TestCase):
    """Testes de regressão dirigidos ao alinhamento com o Capítulo 3."""

    def test_viga_aceita_c45_55(self):
        resultado = viga_service.dimensionar_viga(
            b=300,
            h=500,
            f_ck=45,
            f_yk=500,
            M_Ed_kNm=120,
            c_nom=30,
        )

        self.assertEqual(resultado["status"], "Sucesso")
        self.assertGreaterEqual(float(resultado["M_Rd_kNm"]), 120.0)
        self.assertLessEqual(float(resultado["xi_final"]), 0.45)

    def test_viga_aceita_c50_60(self):
        resultado = viga_service.dimensionar_viga(
            b=300,
            h=500,
            f_ck=50,
            f_yk=500,
            M_Ed_kNm=120,
            c_nom=30,
        )

        self.assertEqual(resultado["status"], "Sucesso")
        self.assertGreaterEqual(float(resultado["M_Rd_kNm"]), 120.0)
        self.assertLessEqual(float(resultado["xi_final"]), 0.45)

    def test_viga_rejeita_fck_superior_a_50_mpa(self):
        with self.assertRaisesRegex(ValueError, r"fck <= 50 MPa"):
            viga_service.dimensionar_viga(
                b=300,
                h=500,
                f_ck=55,
                f_yk=500,
                M_Ed_kNm=120,
                c_nom=30,
            )

    def test_recobrimento_positivo_inferior_a_8_nao_e_rejeitado_artificialmente(self):
        resultado = viga_service.dimensionar_viga(
            b=300,
            h=500,
            f_ck=25,
            f_yk=500,
            M_Ed_kNm=50,
            c_nom=5,
        )

        self.assertEqual(resultado["status"], "Sucesso")
        self.assertGreaterEqual(float(resultado["M_Rd_kNm"]), 50.0)

    def test_phi32_pode_ser_selecionado_sem_prefiltro_por_recobrimento(self):
        # Para c_nom = 20 mm e Øest = 8 mm, a antiga condição
        # Ø <= c_nom + Øest eliminaria Ø32, pois 32 > 28 mm.
        # Com o algoritmo alinhado com o Capítulo 3, Ø32 permanece no catálogo
        # e só é rejeitado se falhar as verificações geométricas ou resistentes.
        resultado = viga_service.dimensionar_viga(
            b=250,
            h=350,
            f_ck=30,
            f_yk=500,
            M_Ed_kNm=200,
            c_nom=20,
        )

        self.assertEqual(resultado["status"], "Sucesso")

        combinacoes = " ".join(
            filter(
                None,
                [
                    resultado.get("combinacao_final"),
                    resultado.get("combinacao_compressao"),
                ],
            )
        )

        self.assertIn("32", combinacoes)
        self.assertGreaterEqual(float(resultado["M_Rd_kNm"]), 200.0)
        self.assertLessEqual(float(resultado["xi_final"]), 0.45)
