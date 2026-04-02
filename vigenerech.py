#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trabalho 1 - Cifra de Vigenère
- Parte I: cifragem/decifragem
- Parte II: ataque por análise de frequência (português/inglês)
Autor: [Seu nome]
"""

import sys
import math
from collections import Counter
from itertools import cycle

# ------------------------------------------------------------
# Parte I: Cifrador / Decifrador de Vigenère
# ------------------------------------------------------------

def vigenere_encrypt(plaintext: str, key: str) -> str:
    """
    Cifra um texto claro usando a cifra de Vigenère.
    - plaintext: texto claro (apenas letras A-Z, sem acentos)
    - key: chave (apenas letras A-Z)
    Retorna o texto cifrado em maiúsculas.
    """
    plaintext = plaintext.upper()
    key = key.upper()
    ciphertext = []
    key_len = len(key)
    for i, ch in enumerate(plaintext):
        if ch.isalpha():
            # Desloca: (P + K) mod 26
            p = ord(ch) - ord('A')
            k = ord(key[i % key_len]) - ord('A')
            c = (p + k) % 26
            ciphertext.append(chr(c + ord('A')))
        else:
            # Mantém caracteres não-alfabéticos (espaços, pontuação)
            ciphertext.append(ch)
    return ''.join(ciphertext)


def vigenere_decrypt(ciphertext: str, key: str) -> str:
    """
    Decifra um texto cifrado usando a cifra de Vigenère.
    - ciphertext: texto cifrado (apenas letras A-Z)
    - key: chave (apenas letras A-Z)
    Retorna o texto claro em maiúsculas.
    """
    ciphertext = ciphertext.upper()
    key = key.upper()
    plaintext = []
    key_len = len(key)
    for i, ch in enumerate(ciphertext):
        if ch.isalpha():
            c = ord(ch) - ord('A')
            k = ord(key[i % key_len]) - ord('A')
            p = (c - k) % 26
            plaintext.append(chr(p + ord('A')))
        else:
            plaintext.append(ch)
    return ''.join(plaintext)


# ------------------------------------------------------------
# Parte II: Ataque por análise de frequência
# ------------------------------------------------------------

# Tabelas de frequência das letras em português e inglês (percentuais)
# Fonte: https://pt.wikipedia.org/wiki/Frequ%C3%AAncia_de_letras
FREQ_PT = {
    'A': 14.63, 'B': 1.04, 'C': 3.88, 'D': 4.99, 'E': 12.57,
    'F': 1.02, 'G': 1.30, 'H': 1.28, 'I': 6.18, 'J': 0.40,
    'K': 0.02, 'L': 2.78, 'M': 4.74, 'N': 5.05, 'O': 10.73,
    'P': 2.52, 'Q': 1.20, 'R': 6.53, 'S': 7.81, 'T': 4.34,
    'U': 4.63, 'V': 1.67, 'W': 0.01, 'X': 0.21, 'Y': 0.01,
    'Z': 0.47
}

FREQ_EN = {
    'A': 8.17, 'B': 1.49, 'C': 2.78, 'D': 4.25, 'E': 12.70,
    'F': 2.23, 'G': 2.02, 'H': 6.09, 'I': 6.97, 'J': 0.15,
    'K': 0.77, 'L': 4.03, 'M': 2.41, 'N': 6.75, 'O': 7.51,
    'P': 1.93, 'Q': 0.10, 'R': 5.99, 'S': 6.33, 'T': 9.06,
    'U': 2.76, 'V': 0.98, 'W': 2.36, 'X': 0.15, 'Y': 1.97,
    'Z': 0.07
}

def index_of_coincidence(text: str) -> float:
    """
    Calcula o índice de coincidência para um texto (apenas letras).
    IC = sum_i (n_i * (n_i - 1)) / (N * (N - 1))
    """
    text = ''.join([ch for ch in text.upper() if ch.isalpha()])
    if len(text) < 2:
        return 0.0
    n = len(text)
    counts = Counter(text)
    ic = sum(cnt * (cnt - 1) for cnt in counts.values()) / (n * (n - 1))
    return ic


def estimate_key_length(ciphertext: str, max_len: int = 20) -> int:
    """
    Estima o tamanho da chave usando o índice de coincidência médio.
    Para cada tamanho L (1..max_len), divide o texto em L sequências
    (uma para cada posição da chave) e calcula a média do IC.
    O tamanho que produzir IC médio mais próximo de 0.066 (inglês)
    ou 0.055 (português) é escolhido. Aqui usamos um limiar empírico.
    """
    ciphertext = ''.join([ch for ch in ciphertext.upper() if ch.isalpha()])
    best_len = 1
    best_ic = 0
    for L in range(1, max_len + 1):
        avg_ic = 0.0
        for i in range(L):
            seq = ciphertext[i::L]
            if len(seq) > 1:
                avg_ic += index_of_coincidence(seq)
        avg_ic /= L
        # Para textos em português/inglês, IC ~ 0.055-0.066
        # Quanto mais próximo desse valor, melhor
        # Queremos maximizar a diferença do IC aleatório (0.038)
        score = abs(avg_ic - 0.066)  # Queremos minimizar
        if L == 1 or score < best_ic:
            best_ic = score
            best_len = L
    return best_len


def shift_text(text: str, shift: int) -> str:
    """Aplica um deslocamento de Caesar (shift) ao texto (apenas letras)."""
    res = []
    for ch in text:
        if ch.isalpha():
            base = ord('A')
            res.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            res.append(ch)
    return ''.join(res)


def find_key_letter(seq: str, lang_freq: dict) -> str:
    """
    Dada uma sequência de letras cifradas (todas provenientes da mesma posição
    da chave), determina a letra da chave que melhor alinha a distribuição
    com a frequência do idioma.
    """
    # Conta frequência das letras na sequência
    seq = ''.join([ch for ch in seq if ch.isalpha()])
    if not seq:
        return 'A'
    n = len(seq)
    counts = Counter(seq)
    # Calcula a soma dos quadrados das diferenças (chi2) para cada possível shift
    best_shift = 0
    best_score = float('inf')
    for shift in range(26):
        # Ajusta as frequências observadas: aplica shift inverso (decifra)
        # Se a letra cifrada é C, a letra clara seria (C - shift) mod 26
        # Então a distribuição esperada no claro é a do idioma.
        # Vamos computar a estatística chi^2 entre a distribuição observada
        # no cifrado (mas deslocada) e a esperada.
        # Método: para cada letra L do alfabeto, a letra clara correspondente
        # é (L - shift) mod 26. A frequência observada de L no cifrado deve
        # ser comparada com a frequência esperada da letra clara correspondente.
        chi2 = 0.0
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            observed = counts.get(letter, 0)
            # Letra clara que resultaria em 'letter' se a chave fosse shift
            # Cifrado = (Claro + shift) mod 26 -> Claro = (Cifrado - shift) mod 26
            plain_letter = chr((ord(letter) - ord('A') - shift) % 26 + ord('A'))
            expected = n * (lang_freq[plain_letter] / 100.0)
            if expected > 0:
                chi2 += (observed - expected) ** 2 / expected
            else:
                chi2 += observed ** 2  # penaliza
        if chi2 < best_score:
            best_score = chi2
            best_shift = shift
    # A letra da chave é o shift que aplicado ao cifrado produz o claro
    # Na cifra: C = (P + K) mod 26 -> K = (C - P) mod 26.
    # O shift que aplicamos ao cifrado para obter o claro é -K mod 26.
    # Mas calculamos shift como (Claro = Cifrado - shift) => shift = K.
    # Portanto best_shift já é a letra da chave.
    return chr(best_shift + ord('A'))


def attack_vigenere(ciphertext: str, language: str) -> tuple:
    """
    Realiza o ataque completo.
    - ciphertext: texto cifrado (pode conter espaços/pontuação)
    - language: 'pt' ou 'en'
    Retorna (key, plaintext)
    """
    # Remove tudo que não é letra para as análises
    letters_only = ''.join([ch for ch in ciphertext.upper() if ch.isalpha()])
    if not letters_only:
        return '', ''
    
    # Estima o tamanho da chave
    key_len = estimate_key_length(letters_only, max_len=20)
    print(f"[+] Tamanho estimado da chave: {key_len}")
    
    # Recupera cada letra da chave
    key = []
    lang_freq = FREQ_PT if language == 'pt' else FREQ_EN
    for i in range(key_len):
        seq = letters_only[i::key_len]
        letter = find_key_letter(seq, lang_freq)
        key.append(letter)
    key = ''.join(key)
    print(f"[+] Chave recuperada: {key}")
    
    # Decifra o texto original (mantendo caracteres especiais)
    plaintext = vigenere_decrypt(ciphertext, key)
    return key, plaintext


# ------------------------------------------------------------
# Exemplo de uso e testes (Parte I e II com arquivos)
# ------------------------------------------------------------

def main():
    # ========== Teste da Parte I ==========
    print("=" * 60)
    print("Parte I - Cifragem e Decifragem")
    print("=" * 60)
    plain = "HELLO WORLD"
    key = "KEY"
    cipher = vigenere_encrypt(plain, key)
    decrypted = vigenere_decrypt(cipher, key)
    print(f"Texto claro: {plain}")
    print(f"Chave: {key}")
    print(f"Cifrado: {cipher}")
    print(f"Decifrado: {decrypted}")
    assert decrypted == plain.upper(), "Erro na decifragem!"
    print("[OK] Cifragem/decifragem funcionando.\n")
    
    # ========== Parte II - Ataque ==========
    print("=" * 60)
    print("Parte II - Ataque por análise de frequência")
    print("=" * 60)
    
    # Verifica se os arquivos das mensagens cifradas foram fornecidos
    # Nomes esperados: mensagem_portugues_cifrada.txt e mensagem_ingles_cifrada.txt
    # Caso não existam, cria exemplos para demonstração.
    import os
    
    def run_attack(filename, language):
        if not os.path.exists(filename):
            print(f"[!] Arquivo '{filename}' não encontrado. Pulando ataque para {language.upper()}.")
            return
        with open(filename, 'r', encoding='utf-8') as f:
            ciphertext = f.read()
        print(f"\n--- Ataque em {language.upper()} usando arquivo '{filename}' ---")
        key, plain = attack_vigenere(ciphertext, language)
        print("\n[+] Texto decifrado (primeiros 500 caracteres):")
        print(plain[:500])
        if len(plain) > 500:
            print("... (truncado)")
        print("\n" + "-"*40)
    
    # Tenta atacar os dois arquivos (o professor fornecerá esses arquivos)
    run_attack("mensagem_portugues_cifrada.txt", "pt")
    run_attack("mensagem_ingles_cifrada.txt", "en")
    
    # Se nenhum arquivo existir, demonstra o ataque com um exemplo artificial
    if not (os.path.exists("mensagem_portugues_cifrada.txt") or 
            os.path.exists("mensagem_ingles_cifrada.txt")):
        print("\n[DEMO] Nenhum arquivo encontrado. Executando ataque com um exemplo conhecido.")
        # Exemplo: cifra uma frase em português com uma chave conhecida e tenta quebrar
        exemplo_pt = "A CIFRA DE VIGENERE FOI INVENTADA NO SECULO XVI"
        chave_exemplo = "SEGURANCA"
        cifrado_exemplo = vigenere_encrypt(exemplo_pt, chave_exemplo)
        print(f"Exemplo - Texto claro: {exemplo_pt}")
        print(f"Exemplo - Chave real: {chave_exemplo}")
        print(f"Exemplo - Texto cifrado: {cifrado_exemplo}")
        key_rec, plain_rec = attack_vigenere(cifrado_exemplo, "pt")
        print(f"Chave recuperada: {key_rec}")
        print(f"Texto decifrado: {plain_rec}")
        if key_rec == chave_exemplo:
            print("[SUCESSO] Ataque funcionou no exemplo!")
        else:
            print("[FALHA] Ataque não recuperou a chave correta (exemplo muito curto).")
    
    print("\nFim do programa.")


if __name__ == "__main__":
    main()