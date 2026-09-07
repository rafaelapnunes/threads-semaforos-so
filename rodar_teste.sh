#!/bin/bash
echo "=============================================="
echo "Executando simulacao em Python..."
echo "=============================================="
python3 sistema_pix.py

echo "=============================================="
echo "Executando testes unitarios em Python..."
echo "=============================================="
python3 -m unittest test_sistema.py

echo "=============================================="
echo "Compilando e executando simulacao em Java..."
echo "=============================================="
javac SistemaPix.java
java SistemaPix
