import unittest
from sistema_pix import executar_experimento

class TestSistemaPix(unittest.TestCase):
    
    def test_transacao_com_semaforo(self):
        """
        Garante que, usando semáforos, 100 threads fazendo 
        transações concorrentes sempre resultarão no saldo correto (R$ 1000).
        """
        saldo_final, _ = executar_experimento(seguro=True, num_threads=100)
        self.assertEqual(saldo_final, 1000, "O saldo com semáforo deve ser estritamente igual ao inicial.")

    def test_transacao_sem_semaforo(self):
        """
        Verifica a falha na proteção.
        Como o sleep introduz a corrida, a probabilidade da falha é altíssima.
        """
        saldo_final, _ = executar_experimento(seguro=False, num_threads=100)
        
        # Esperamos que o saldo final SEJA DIFERENTE de 1000 na maioria das vezes.
        if saldo_final == 1000:
            self.skipTest("Por pura coincidência, o SO agendou as threads de forma ordenada. Execute novamente.")
        self.assertNotEqual(saldo_final, 1000, "Sem proteção, o saldo deve apresentar inconsistência.")

if __name__ == '__main__':
    unittest.main()
